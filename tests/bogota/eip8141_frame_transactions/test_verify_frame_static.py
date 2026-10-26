"""
`VERIFY` frame static-context tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A `VERIFY` frame runs as a `STATICCALL` (§Behavior: "Execute the frame
as a `STATICCALL`, disallowing state manipulation. Only `APPROVE` can
modify the state or transaction context in `VERIFY`."). Every opcode a
`STATICCALL` forbids — `SSTORE`, `TSTORE`, `LOG0` to `LOG4`, a `CALL`
carrying value, `CREATE`, `CREATE2` and `SELFDESTRUCT` — therefore
halts exceptionally in a `VERIFY` frame's code, and in any call that
code makes, since the static restriction is inherited by nested calls.

A halt at the frame's top level fails the frame, and a failed `VERIFY`
frame makes the transaction invalid, unrolling its approvals
(§Behavior: "If the frame fails by reverting or halting exceptionally,
the transaction is invalid. This unrolls any effects of `APPROVE`.").
A halt in a nested call only fails that call, which returns zero to the
`VERIFY` frame's code like any failed call. Reads stay allowed, and so
does a `CALLCODE` carrying value, which `STATICCALL` does not forbid:
it sends the value to the calling account itself.
"""

from typing import Callable, List

import pytest
from _pytest.mark import ParameterSet
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Conditional,
    Fork,
    Op,
    Opcode,
    StateTestFiller,
    TransactionException,
)

from .helpers import APPROVE_ALL, FrameTransaction, verify_frame
from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

VERIFY_FRAME_GAS = 500_000
"""
Execution gas budget of the `VERIFY` frames: enough for every opcode
under test to succeed outside a static context, so a halt can only
come from the static restriction.
"""

NESTED_CALL_GAS = 300_000
"""Execution gas the `VERIFY` frame's code forwards to its nested call."""

Operation = Callable[[Address], Bytecode]
"""
Build the bytecode of an opcode under test, given an existing account
the opcode can send value to or name as a beneficiary.
"""

STATE_CHANGES = [
    pytest.param(lambda _: Op.SSTORE(0, 1), id="SSTORE"),
    pytest.param(lambda _: Op.TSTORE(0, 1), id="TSTORE"),
    pytest.param(lambda _: Op.LOG0(0, 0), id="LOG0"),
    pytest.param(lambda _: Op.LOG1(0, 0, 1), id="LOG1"),
    pytest.param(lambda _: Op.LOG2(0, 0, 1, 2), id="LOG2"),
    pytest.param(lambda _: Op.LOG3(0, 0, 1, 2, 3), id="LOG3"),
    pytest.param(lambda _: Op.LOG4(0, 0, 1, 2, 3, 4), id="LOG4"),
    pytest.param(
        lambda to: Op.POP(Op.CALL(gas=0, address=to, value=1)),
        id="CALL_with_value",
    ),
    pytest.param(lambda _: Op.POP(Op.CREATE(0, 0, 0)), id="CREATE"),
    pytest.param(lambda _: Op.POP(Op.CREATE2(0, 0, 0, 0)), id="CREATE2"),
    pytest.param(lambda to: Op.SELFDESTRUCT(to), id="SELFDESTRUCT"),
]
"""Opcodes a static context forbids."""

READS = [
    pytest.param(lambda _: Op.POP(Op.SLOAD(0)), id="SLOAD"),
    pytest.param(lambda _: Op.POP(Op.TLOAD(0)), id="TLOAD"),
    pytest.param(lambda to: Op.POP(Op.BALANCE(to)), id="BALANCE"),
    pytest.param(
        lambda to: Op.POP(Op.CALL(gas=0, address=to, value=0)),
        id="CALL_without_value",
    ),
    # EIP-214 bans only `CALL` with value in a static context: a
    # `CALLCODE` with value sends the value to the calling account
    # itself, which changes no balance.
    pytest.param(
        lambda to: Op.POP(Op.CALLCODE(gas=0, address=to, value=1)),
        id="CALLCODE_with_value",
    ),
]
"""Opcodes a static context allows, the controls."""


def static_cases(*, invalidating: bool) -> List[ParameterSet]:
    """
    Return the state changes, then the reads, each with whether the
    static context allows it. With `invalidating`, a state change makes
    the transaction invalid, so its case is an exception test.
    """
    marks = [pytest.mark.exception_test] if invalidating else []
    return [
        pytest.param(*case.values, False, id=case.id, marks=marks)
        for case in STATE_CHANGES
    ] + [pytest.param(*case.values, True, id=case.id) for case in READS]


@pytest.mark.parametrize("operation,allowed", static_cases(invalidating=True))
def test_verify_frame_runs_as_staticcall(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    operation: Operation,
    allowed: bool,
) -> None:
    """
    Run an opcode directly in a `VERIFY` frame's code, after the
    frame has approved: a state change halts the frame, which makes the
    transaction invalid, while a read lets the frame succeed.

    EIP-8141 §Behavior, `VERIFY` mode: "Execute the frame as a
    `STATICCALL`, disallowing state manipulation" and "If the frame
    fails by reverting or halting exceptionally, the transaction is
    invalid. This unrolls any effects of `APPROVE`."

    The frame approves first, from a self-call, so it stands approved
    when the opcode runs: the transaction is valid exactly when the
    opcode does not halt. Approving after the opcode would leave
    `SELFDESTRUCT` untested, since it ends the frame either way.
    """
    recipient = pre.deploy_contract(code=Op.STOP)
    # The frame supplies calldata; the self-call, which approves and
    # returns, supplies none.
    sender_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=Op.POP(Op.CALL(gas=Op.GAS, address=Op.ADDRESS))
        + operation(recipient)
        + Op.STOP,
        if_false=APPROVE_ALL,
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(
                gas_limit=VERIFY_FRAME_GAS,
                data=Bytes(b"\x01"),
                pin_gas=False,
                logs=[],
            ),
        ],
        error=(
            None
            if allowed
            else TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        # The approval's nonce increment is the witness that the frame,
        # and with it the approval, survived.
        post={
            sender: Account(nonce=2 if allowed else 1, storage={}),
            recipient: Account(balance=0),
        },
    )


@pytest.mark.parametrize("operation,allowed", static_cases(invalidating=False))
@pytest.mark.parametrize(
    "call_opcode",
    [
        pytest.param(Op.CALL, id="CALL"),
        pytest.param(Op.DELEGATECALL, id="DELEGATECALL"),
    ],
)
def test_verify_frame_nested_call_is_static(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    operation: Operation,
    allowed: bool,
    call_opcode: Opcode,
) -> None:
    """
    Run an opcode in a contract the `VERIFY` frame's code calls with a
    plain `CALL`, or runs in its own context with `DELEGATECALL`: the
    static restriction carries into either, so a state change halts
    the call, which returns zero, and the frame still succeeds.

    EIP-8141 §Behavior, `VERIFY` mode: "Execute the frame as a
    `STATICCALL`, disallowing state manipulation." As for any
    `STATICCALL`, the restriction holds at every depth below it,
    whichever call opcode reaches that depth.

    The frame approves only if the call's result matches the expected
    verdict (zero for a state change, one for a read), so the
    transaction is valid only if the callee halted exactly when it
    tried to change state. The callee, and under `DELEGATECALL` the
    sender whose context it runs in, hold a balance, so a `CALL` with
    value can only fail on the static restriction.
    """
    recipient = pre.deploy_contract(code=Op.STOP)
    callee = pre.deploy_contract(
        code=operation(recipient) + Op.STOP, balance=1
    )
    sender_code = Conditional(
        condition=Op.EQ(
            call_opcode(gas=NESTED_CALL_GAS, address=callee),
            1 if allowed else 0,
        ),
        if_true=APPROVE_ALL,
        if_false=Op.REVERT(0, 0),
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(
                gas_limit=VERIFY_FRAME_GAS,
                pin_gas=False,
                logs=[],
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=2, storage={}),
            # Under `DELEGATECALL` the callee's code runs in the sender's
            # context, so this entry is a sanity check there; the oracle
            # is the transaction's validity and the sender's nonce.
            callee: Account(nonce=1, balance=1, storage={}),
            recipient: Account(balance=0),
        },
    )
