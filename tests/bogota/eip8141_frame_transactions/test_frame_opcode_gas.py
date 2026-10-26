"""
Gas boundary tests for the introspection instructions of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Each case runs one introspection instruction as the last charged
instruction of a `DEFAULT` frame whose execution budget is exactly what
the frame spends, or one unit less. With the exact budget the frame
succeeds and its receipt reports the budget as used. One unit short,
the instruction under test is the one that cannot pay, so the frame
halts out of gas and its receipt reports its whole budget used. A cost
one unit too high fails the first case; one unit too low passes the
second.

The instruction's cost is derived here from the EIP text rather than
from the framework's gas table; only the operand pushes before it are
priced by the framework.
"""

from typing import Callable

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Bytes,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
)

from .helpers import FrameTransaction, Outcome, default_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

PARAM_INSTRUCTION_GAS = 2
"""
`TXPARAM` (EIP-8141 l.802), `FRAMEPARAM` (l.860) and `SIGPARAM` (l.888):
"The gas cost of this operation is `2`".
"""

FRAMEDATALOAD_GAS = 3
"""`FRAMEDATALOAD` (l.823): "Gas cost: 3 (matches CALLDATALOAD)"."""

COPY_BASE_GAS = 3
"""
`FRAMEDATACOPY` (l.839-841) and `SIGDATACOPY` (l.906): gas "calculated
exactly as for `CALLDATACOPY`, including the fixed cost of 3".
"""

COPY_PER_WORD_GAS = 3
"""The per-word copy cost of `CALLDATACOPY`, which both copies reuse."""

COPIED_BYTES = Bytes(bytes(range(1, 41)))
"""
Data of the probe frame and raw bytes of the `ARBITRARY` signature
entry: 40 bytes, longer than every copy below except the 33-byte one's
zero-filled tail.
"""

FAR_OFFSET = 0x100
"""A memory offset whose 1-byte copy expands memory to 9 words."""

ProbeCost = Callable[[Fork], int]
"""The EIP-derived execution gas of the instruction under test."""


def fixed(cost: int) -> ProbeCost:
    """Return a fixed instruction cost."""

    def fixed_cost(fork: Fork) -> int:
        del fork
        return cost

    return fixed_cost


def copy_cost(
    length: int, memory_end: int, memory_before: int = 0
) -> ProbeCost:
    """
    Return the cost of a `CALLDATACOPY`-shaped copy of `length` bytes
    whose destination region ends at byte `memory_end`: the fixed cost,
    the per-word copy cost, and the standard memory expansion from
    `memory_before` bytes. A zero-length copy expands nothing.
    """

    def cost(fork: Fork) -> int:
        words = (length + 31) // 32
        expansion = 0
        if length > 0:
            expansion = fork.memory_expansion_gas_calculator()(
                new_bytes=memory_end, previous_bytes=memory_before
            )
        return COPY_BASE_GAS + COPY_PER_WORD_GAS * words + expansion

    return cost


def copy_operands(
    index: int, length: int, data_offset: int = 0, memory_offset: int = 0
) -> Bytecode:
    """
    Push a copy's operands: `memOffset` on top, then `dataOffset`,
    `length` and the frame or signature index (l.845-850, l.910-915).
    """
    return (
        Op.PUSH1[index]
        + Op.PUSH1[length]
        + Op.PUSH1[data_offset]
        + Op.PUSH2[memory_offset]
    )


def copy_cases(opcode: Op, index: int, name: str) -> list:
    """Return the length and memory boundary cases of a copy."""
    return [
        *(
            pytest.param(
                copy_operands(index, length),
                opcode,
                copy_cost(length, memory_end=length),
                id=f"{name}_length_{length}",
            )
            for length in (0, 1, 32, 33)
        ),
        pytest.param(
            copy_operands(index, 1, memory_offset=FAR_OFFSET),
            opcode,
            copy_cost(1, memory_end=FAR_OFFSET + 1),
            id=f"{name}_expands_to_far_offset",
        ),
        pytest.param(
            copy_operands(index, 0, memory_offset=0xFFFF),
            opcode,
            copy_cost(0, memory_end=0xFFFF),
            id=f"{name}_length_0_far_offset_no_expansion",
        ),
        pytest.param(
            # Memory already spans two words, so the 33-byte copy pays
            # its copy cost and no expansion.
            Op.MSTORE8(63, 0, new_memory_size=64) + copy_operands(index, 33),
            opcode,
            copy_cost(33, memory_end=33, memory_before=64),
            id=f"{name}_into_expanded_memory",
        ),
    ]


GAS_CASES = [
    pytest.param(
        Op.PUSH1[Spec.TXPARAM_TYPE],
        Op.TXPARAM,
        fixed(PARAM_INSTRUCTION_GAS),
        id="txparam",
    ),
    pytest.param(
        # `frameIndex` on top, `param` second (l.860).
        Op.PUSH1[Spec.FRAMEPARAM_MODE] + Op.PUSH1[1],
        Op.FRAMEPARAM,
        fixed(PARAM_INSTRUCTION_GAS),
        id="frameparam",
    ),
    pytest.param(
        # `signatureIndex` on top, `param` second (l.888).
        Op.PUSH1[Spec.SIGPARAM_SCHEME] + Op.PUSH1[1],
        Op.SIGPARAM,
        fixed(PARAM_INSTRUCTION_GAS),
        id="sigparam",
    ),
    pytest.param(
        # `offset` on top, `frameIndex` second (l.827-830).
        Op.PUSH1[1] + Op.PUSH1[0],
        Op.FRAMEDATALOAD,
        fixed(FRAMEDATALOAD_GAS),
        id="framedataload",
    ),
    # Frame 1 is the probe frame, which carries `COPIED_BYTES`.
    *copy_cases(Op.FRAMEDATACOPY, 1, "framedatacopy"),
    # Signature entry 1 is `ARBITRARY`, carrying `COPIED_BYTES`.
    *copy_cases(Op.SIGDATACOPY, 1, "sigdatacopy"),
]
"""
The operand pushes, the bare instruction, and its EIP-derived cost.
"""


@pytest.mark.parametrize("setup,opcode,opcode_cost", GAS_CASES)
@pytest.mark.parametrize(
    "shortfall",
    [pytest.param(0, id="exact_gas"), pytest.param(1, id="one_short")],
)
def test_frame_opcode_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    setup: Bytecode,
    opcode: Op,
    opcode_cost: ProbeCost,
    shortfall: int,
) -> None:
    """
    Pin each introspection instruction's execution gas, including the
    copy cost and memory expansion of `FRAMEDATACOPY` and
    `SIGDATACOPY`, between the budget that covers it exactly and one
    unit less.

    - `TXPARAM`, `FRAMEPARAM`, `SIGPARAM` cost 2 (EIP-8141 l.802, l.860,
      l.888); `FRAMEDATALOAD` costs 3 (l.823).
    - `FRAMEDATACOPY` and `SIGDATACOPY` cost 3, plus 3 per copied word,
      plus the standard memory expansion (l.839-841, l.906). Lengths 0,
      1, 32 and 33 copy 0, 1, 1 and 2 words and expand memory to 0, 1,
      1 and 2 words. A 1-byte copy at offset 256 expands memory to 9
      words; a zero-length copy expands nothing whatever its offset; a
      copy into memory that is already large enough pays no expansion.

    The probe frame's receipt pins its execution gas: the cold access
    to its target at frame entry plus its code when the budget is
    exact, its whole budget when the frame halts one unit short. A
    `DEFAULT` frame halting leaves the transaction valid, so both
    outcomes settle and the sender's nonce increments either way.
    """
    sender = pre.fund_eoa()
    code = setup + opcode + Op.STOP
    probe = pre.deploy_contract(code=code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(),
            default_frame(
                target=probe,
                code=code,
                data=COPIED_BYTES,
                execution_gas=setup.execution_cost(fork) + opcode_cost(fork),
                gas_limit_delta=-shortfall,
                outcome=Outcome.HALT if shortfall else Outcome.SUCCESS,
            ),
        ],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            FrameSignature(
                scheme=Spec.SCHEME_ARBITRARY, signature=COPIED_BYTES
            ),
        ],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})
