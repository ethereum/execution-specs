"""
Tests that the instructions of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141)
halt exceptionally outside a frame transaction.

`APPROVE` (`0xaa`) halts "if the current transaction is not a frame
transaction" (EIP-8141 l.768), and the introspection instructions
`TXPARAM`, `FRAMEDATALOAD`, `FRAMEDATACOPY`, `FRAMEPARAM`, `SIGPARAM`
and `SIGDATACOPY` (`0xb0`-`0xb5`) "are defined only during the
execution of a frame transaction. Executing any of them in the context
of any other transaction type results in an exceptional halt" (l.798).

The rule keys on the transaction, not on the call depth: the same
probe contract halts when a regular transaction of any type calls it,
and runs when a frame transaction's frame calls it.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Bytes,
    CodeGasMeasure,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
    Transaction,
)

from .helpers import default_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_EXECUTED = 0x01
"""Storage slot the probe writes once the frame instruction returns."""

SLOT_CALL_GAS = 0x02
"""Storage slot the caller writes the gas its call to the probe used."""

SLOT_CALL_SUCCESS = 0x03
"""Storage slot the caller writes its call to the probe's outcome into."""

PROBE_GAS = 50_000
"""Execution gas the caller forwards to the probe."""

CALL_VALUE = 1
"""Wei the caller sends along, so a halt has a transfer to undo."""

ARBITRARY_WITNESS = Bytes(b"\xab" * 40)
"""Raw bytes of the frame transaction's `ARBITRARY` signature entry."""

# Every operand is valid inside the frame transaction of
# `test_frame_opcodes_run_at_depth_in_frame_transaction`: frame 1 is
# the frame calling the probe, and signature entry 1 is `ARBITRARY`, so
# both its scheme and its raw bytes are readable. The only difference
# between that test and the halting one is the transaction type.
FRAME_OPCODES = [
    pytest.param(
        Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT), id="approve"
    ),
    pytest.param(Op.POP(Op.TXPARAM(Spec.TXPARAM_TYPE)), id="txparam"),
    pytest.param(Op.POP(Op.FRAMEDATALOAD(0, 1)), id="framedataload"),
    pytest.param(Op.FRAMEDATACOPY(0, 0, 32, 1), id="framedatacopy"),
    pytest.param(
        Op.POP(Op.FRAMEPARAM(1, Spec.FRAMEPARAM_MODE)), id="frameparam"
    ),
    pytest.param(Op.POP(Op.SIGPARAM(1, Spec.SIGPARAM_SCHEME)), id="sigparam"),
    pytest.param(Op.SIGDATACOPY(0, 0, 32, 1), id="sigdatacopy"),
]
"""Each frame instruction, with operands valid in the frame transaction."""


def probe_code(frame_opcode: Bytecode) -> Bytecode:
    """
    Return the probe's code: the frame instruction, then a write that
    records the instruction returned.
    """
    return frame_opcode + Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP


@pytest.mark.with_all_typed_transactions(
    selector=lambda tx_type: tx_type != Spec.FRAME_TX_TYPE,
    marks=lambda tx_type: (
        pytest.mark.execute(
            pytest.mark.skip(
                reason="type 3 transactions aren't supported in execute mode"
            )
        )
        if tx_type == 3
        else None
    ),
)
@pytest.mark.parametrize("frame_opcode", FRAME_OPCODES)
# The oracle depends on the transaction type: rewritten as a frame
# transaction, the instructions would no longer halt.
@pytest.mark.frame_tx_incompatible
def test_frame_opcode_halts_outside_frame_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    typed_transaction: Transaction,
    frame_opcode: Bytecode,
) -> None:
    """
    Halt exceptionally on each frame instruction executed under every
    transaction type other than the frame transaction (EIP-8141 l.768,
    l.798).

    The transaction calls a caller contract, which calls the probe with
    `PROBE_GAS` and one wei. An exceptional halt consumes all the gas a
    call frame was given and discards its state changes, so:

    - the caller measures its `CALL` at the instruction's own cost plus
      the whole `PROBE_GAS`: a probe that returned, reverted, or treated
      the instruction as a no-op would hand gas back;
    - the probe's balance stays at zero, since the value transfer into
      it is undone;
    - the probe's write after the instruction never happens.
    """
    probe = pre.deploy_contract(code=probe_code(frame_opcode))
    call = Op.CALL(
        gas=PROBE_GAS,
        address=probe,
        value=CALL_VALUE,
        address_warm=False,
        value_transfer=True,
    )
    caller = pre.deploy_contract(
        code=CodeGasMeasure(
            code=call, extra_stack_items=1, sstore_key=SLOT_CALL_GAS
        )
        + Op.STOP,
        balance=CALL_VALUE,
    )

    state_test(
        pre=pre,
        tx=typed_transaction.copy(to=caller, gas_limit=1_000_000),
        post={
            caller: Account(
                balance=CALL_VALUE,
                storage={SLOT_CALL_GAS: call.gas_cost(fork) + PROBE_GAS},
            ),
            probe: Account(balance=0, storage={}),
        },
    )


@pytest.mark.parametrize(
    "frame_opcode",
    # `APPROVE` at depth is covered by `test_frame_transactions.py`:
    # nested approvals through `CALL`, `DELEGATECALL` and `STATICCALL`.
    # Called here by a contract other than the frame's target, it would
    # revert on `ADDRESS != resolved_target` (l.769), not run.
    [p for p in FRAME_OPCODES if p.id != "approve"],
)
def test_frame_opcodes_run_at_depth_in_frame_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
    frame_opcode: Bytecode,
) -> None:
    """
    Run each introspection instruction one call deep inside a frame
    transaction: the instructions are defined "during the execution of
    a frame transaction" (EIP-8141 l.798), with no restriction on the
    call depth.

    This is the positive control of
    `test_frame_opcode_halts_outside_frame_transaction`: the same probe
    code, called the same way, by a `DEFAULT` frame instead of by a
    regular transaction. The call succeeds and the probe's write after
    the instruction lands.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(code=probe_code(frame_opcode))
    caller = pre.deploy_contract(
        code=Op.SSTORE(
            SLOT_CALL_SUCCESS, Op.CALL(gas=PROBE_GAS, address=probe)
        )
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        frames=[verify_frame(), default_frame(target=caller)],
        signatures=[
            FrameSignature(scheme=Spec.SCHEME_SECP256K1, signer=Bytes(sender)),
            FrameSignature(
                scheme=Spec.SCHEME_ARBITRARY, signature=ARBITRARY_WITNESS
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            caller: Account(storage={SLOT_CALL_SUCCESS: 1}),
            probe: Account(storage={SLOT_EXECUTED: 1}),
        },
    )
