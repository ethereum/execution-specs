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
from .signature_helpers import canonical_entry
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

PARAM_INSTRUCTION_GAS = 2
"""
EIP-8141 "`TXPARAM` Instruction", "`FRAMEPARAM` Instruction" and
"`SIGPARAM` Instruction": "The gas cost of this operation is `2`".
"""

FRAMEDATALOAD_GAS = 3
"""
EIP-8141 "`FRAMEDATALOAD` Instruction": "Gas cost: 3 (matches
CALLDATALOAD)".
"""

COPY_BASE_GAS = 3
"""
EIP-8141 "`FRAMEDATACOPY` Instruction" and "`SIGDATACOPY` Instruction":
gas "calculated exactly as for `CALLDATACOPY`, including the fixed cost
of 3".
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

QUADRATIC_OFFSET = 0x2000
"""
A memory offset whose 1-byte copy expands memory to 257 words, where
the quadratic term of the memory cost, `257**2 // 512 = 129`, is far
from zero.
"""

MAX_WORD = 2**256 - 1
"""The largest stack word."""

ProbeCost = Callable[[Fork], int]
"""The EIP-derived execution gas of the instruction under test."""


def push(value: int) -> Bytecode:
    """
    Push `value` with the narrowest of `PUSH1` to `PUSH32` that holds
    it; all of them cost the same.
    """
    return getattr(Op, f"PUSH{max(1, (value.bit_length() + 7) // 8)}")[value]


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
    `length` and the frame or signature index ("`FRAMEDATACOPY`
    Instruction", "`SIGDATACOPY` Instruction").
    """
    return push(index) + push(length) + push(data_offset) + push(memory_offset)


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
            copy_operands(index, 1, memory_offset=QUADRATIC_OFFSET),
            opcode,
            copy_cost(1, memory_end=QUADRATIC_OFFSET + 1),
            id=f"{name}_expands_quadratic",
        ),
        pytest.param(
            # The byte at offset 33 lies in the second word, so memory
            # grows to 2 words for a 1-word copy.
            copy_operands(index, 1, memory_offset=33),
            opcode,
            copy_cost(1, memory_end=34),
            id=f"{name}_unaligned_memory_offset",
        ),
        pytest.param(
            copy_operands(index, 0, memory_offset=0xFFFF),
            opcode,
            copy_cost(0, memory_end=0xFFFF),
            id=f"{name}_length_0_far_offset_no_expansion",
        ),
        pytest.param(
            # A zero-length copy expands nothing even at the largest
            # offset, where any region would end beyond 2**256.
            copy_operands(index, 0, memory_offset=MAX_WORD),
            opcode,
            copy_cost(0, memory_end=MAX_WORD),
            id=f"{name}_length_0_max_memory_offset",
        ),
        pytest.param(
            # Bytes past the end of the source copy as zeroes, so a
            # source offset beyond any data costs as an ordinary copy.
            copy_operands(index, 32, data_offset=MAX_WORD),
            opcode,
            copy_cost(32, memory_end=32),
            id=f"{name}_max_data_offset",
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
        # The canonical signature hash, which a client may compute
        # lazily on first read; its cost is still the flat 2.
        Op.PUSH1[Spec.TXPARAM_SIG_HASH],
        Op.TXPARAM,
        fixed(PARAM_INSTRUCTION_GAS),
        id="txparam_sig_hash",
    ),
    pytest.param(
        # `frameIndex` on top, `param` second ("`FRAMEPARAM` Instruction").
        Op.PUSH1[Spec.FRAMEPARAM_MODE] + Op.PUSH1[1],
        Op.FRAMEPARAM,
        fixed(PARAM_INSTRUCTION_GAS),
        id="frameparam",
    ),
    *(
        pytest.param(
            # Frame 0, the completed `VERIFY` frame: these params read
            # its receipt, at the same flat cost.
            Op.PUSH1[param] + Op.PUSH1[0],
            Op.FRAMEPARAM,
            fixed(PARAM_INSTRUCTION_GAS),
            id=f"frameparam_{name}",
        )
        for param, name in (
            (Spec.FRAMEPARAM_STATUS, "status"),
            (Spec.FRAMEPARAM_EXECUTION_GAS_USED, "execution_gas_used"),
            (Spec.FRAMEPARAM_STATE_GAS_USED, "state_gas_used"),
        )
    ),
    pytest.param(
        # `signatureIndex` on top, `param` second ("`SIGPARAM`
        # Instruction").
        Op.PUSH1[Spec.SIGPARAM_SCHEME] + Op.PUSH1[1],
        Op.SIGPARAM,
        fixed(PARAM_INSTRUCTION_GAS),
        id="sigparam",
    ),
    pytest.param(
        # Entry 0 is the sender's `SECP256K1` entry, whose resolved
        # signer is read at the same flat cost.
        Op.PUSH1[Spec.SIGPARAM_RESOLVED_SIGNER] + Op.PUSH1[0],
        Op.SIGPARAM,
        fixed(PARAM_INSTRUCTION_GAS),
        id="sigparam_resolved_signer",
    ),
    pytest.param(
        # `offset` on top, `frameIndex` second ("`FRAMEDATALOAD`
        # Instruction").
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

    - `TXPARAM`, `FRAMEPARAM`, `SIGPARAM` cost 2 (EIP-8141 "`TXPARAM`
      Instruction", "`FRAMEPARAM` Instruction", "`SIGPARAM`
      Instruction") whatever the param, including the signature hash,
      the receipt fields of a completed frame and the resolved signer;
      `FRAMEDATALOAD` costs 3 ("`FRAMEDATALOAD` Instruction").
    - `FRAMEDATACOPY` and `SIGDATACOPY` cost 3, plus 3 per copied word,
      plus the standard memory expansion ("`FRAMEDATACOPY` Instruction",
      "`SIGDATACOPY` Instruction"). Lengths 0, 1, 32 and 33 copy 0, 1, 1
      and 2 words and expand memory to 0, 1, 1 and 2 words. A 1-byte
      copy at offset 256 expands memory to 9 words, and at offset
      0x2000 to 257 words, where the quadratic term of the memory cost
      counts; a 1-byte copy at offset 33 expands memory to 2 words. A
      zero-length copy expands nothing whatever its offset, up to
      2**256 - 1; a copy from a source offset of 2**256 - 1 is priced as
      any other copy; a copy into memory that is already large enough
      pays no expansion.

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
                data=COPIED_BYTES,
                execution_gas=setup.execution_cost(fork) + opcode_cost(fork),
                gas_limit_delta=-shortfall,
                outcome=Outcome.HALT if shortfall else Outcome.SUCCESS,
            ),
        ],
        signatures=[
            canonical_entry(sender),
            FrameSignature(
                scheme=Spec.SCHEME_ARBITRARY, signature=COPIED_BYTES
            ),
        ],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})


@pytest.mark.parametrize(
    "length",
    [
        pytest.param(2**64, id="length_2_pow_64"),
        pytest.param(MAX_WORD, id="length_max_word"),
    ],
)
@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.FRAMEDATACOPY, id="framedatacopy"),
        pytest.param(Op.SIGDATACOPY, id="sigdatacopy"),
    ],
)
def test_frame_copy_huge_length_runs_out_of_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    length: int,
) -> None:
    """
    Halt out of gas on a copy whose length no budget can pay for.

    EIP-8141 "`FRAMEDATACOPY` Instruction" and "`SIGDATACOPY`
    Instruction": gas "calculated exactly as for `CALLDATACOPY`", so a
    length of 2**64 or 2**256 - 1 bytes costs 3 per word plus the memory
    expansion to that size, which exceeds any frame budget: the frame
    halts exceptionally and its receipt reports its whole budget used.

    A client that narrows the length to 64 bits before pricing it
    copies 0 bytes for 2**64 and succeeds; one whose word count or
    memory end wraps at 256 bits prices 2**256 - 1 bytes as nearly
    nothing.
    """
    sender = pre.fund_eoa()
    code = copy_operands(1, length, memory_offset=1) + opcode + Op.STOP
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
                gas_limit=1_000_000,
                outcome=Outcome.HALT,
            ),
        ],
        signatures=[
            canonical_entry(sender),
            FrameSignature(
                scheme=Spec.SCHEME_ARBITRARY, signature=COPIED_BYTES
            ),
        ],
    )

    state_test(pre=pre, tx=tx, post={sender: Account(nonce=1)})
