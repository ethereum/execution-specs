"""
Broad-stroke end-to-end tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

These tests cover the core flows of the frame transaction: default-code
validation and payment, contract senders approving via `APPROVE`,
third-party payers, atomic batches, transaction introspection, and the
basic invalid-transaction cases. Exhaustive edge-case coverage is left
for follow-up work.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Case,
    Conditional,
    Fork,
    FrameSignature,
    Op,
    StateTestFiller,
    Switch,
    Transaction,
    TransactionException,
)

from .helpers import (
    FrameTransaction,
    Outcome,
    default_frame,
    sender_frame,
    verify_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""

SLOT_CALL_OUTCOME = 0x02
"""Storage slot used by target contracts to record a nested call's success."""


def test_transfer_with_default_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Transfer ETH from an EOA sender using the default code: a `VERIFY`
    frame authorizes execution and payment against the sender's
    signature entry, and a `SENDER` frame carries the value.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=1)
    transfer_value = 10**17

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(logs=[]),
            sender_frame(target=recipient, value=transfer_value),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            recipient: Account(balance=1 + transfer_value),
        },
    )


def test_contract_sender_approves(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Send a frame transaction from a contract account whose code calls
    `APPROVE` to authorize execution and payment, then executes a
    `SENDER` frame calling another contract.
    """
    sender_code = Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT)
    sender = pre.deploy_contract(code=sender_code, balance=10**18)
    target_code = Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP
    target = pre.deploy_contract(code=target_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(code=sender_code),
            sender_frame(target=target, code=target_code),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=2),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


def test_eoa_paymaster(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Sponsor a frame transaction's fees from a second EOA via the
    default code: the sender approves only execution, the payer
    approves only payment, and the sender's balance is untouched.
    """
    sender_balance = 10**18
    sender = pre.fund_eoa(amount=sender_balance)
    payer = pre.fund_eoa()
    target_code = Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP
    target = pre.deploy_contract(code=target_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        payer=payer,
        frames=[
            verify_frame(flags=Spec.APPROVE_EXECUTION),
            verify_frame(flags=Spec.APPROVE_PAYMENT, target=payer),
            sender_frame(
                target=target,
                code=target_code,
            ),
        ],
        signatures=[
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1,
                signer=Bytes(sender),
            ),
            FrameSignature(
                scheme=Spec.SCHEME_SECP256K1,
                signer=Bytes(payer),
                secret_key=payer.key,
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1, balance=sender_balance),
            payer: Account(nonce=0),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


@pytest.mark.parametrize(
    "revert_position",
    [
        pytest.param("last", id="unrolls_executed_frames"),
        pytest.param("first", id="skips_remaining_frames"),
    ],
)
def test_atomic_batch_rollback(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    revert_position: str,
) -> None:
    """
    Roll back an atomic batch containing a reverting frame.

    When the batch terminator reverts, the state changes of the
    already executed batch frame are unrolled; its frame receipt
    retains the execution status and gas used, with empty logs. When
    the first batch frame reverts, the remaining batch frame is
    skipped with status `0x2` and no gas consumed. In both cases the
    storage write is discarded.
    """
    sender = pre.fund_eoa()
    target_code = Op.SSTORE(SLOT_EXECUTED, 1) + Op.LOG0(0, 0) + Op.STOP
    target = pre.deploy_contract(code=target_code)
    reverter_code = Op.REVERT(0, 0)
    reverter = pre.deploy_contract(code=reverter_code)

    if revert_position == "last":
        batch = [
            sender_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=target,
                code=target_code,
                outcome=Outcome.UNROLLED,
            ),
            sender_frame(
                target=reverter, code=reverter_code, outcome=Outcome.REVERT
            ),
        ]
    else:
        batch = [
            sender_frame(
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=reverter,
                code=reverter_code,
                outcome=Outcome.REVERT,
            ),
            sender_frame(target=target, outcome=Outcome.SKIPPED),
        ]

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[verify_frame(), *batch],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            target: Account(storage={SLOT_EXECUTED: 0}),
        },
    )


@pytest.mark.exception_test
def test_sender_frame_before_approval(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a frame transaction whose `SENDER` frame runs before any
    frame has approved execution.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)

    tx = Transaction(
        sender=sender,
        frames=[
            sender_frame(target=target, gas_limit=200_000),
            verify_frame(),
        ],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            target: Account(storage={SLOT_EXECUTED: 0}),
        },
    )


@pytest.mark.exception_test
def test_verify_frame_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a frame transaction with a reverting `VERIFY` frame: the
    sender contract allows no approval scope, so the default code
    reverts.
    """
    sender = pre.fund_eoa()
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))

    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(),
            verify_frame(flags=Spec.APPROVE_NONE, target=reverter),
        ],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )

    state_test(
        pre=pre,
        tx=tx,
        post={},
    )


@pytest.mark.parametrize(
    "frame_reverts",
    [
        pytest.param(
            True,
            id="reverts",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(False, id="returns"),
    ],
)
def test_frame_revert_discards_the_approval_it_granted(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    frame_reverts: bool,
) -> None:
    """
    A frame that reverts discards the approval context it granted.

    `APPROVE` exits its own call context, so a frame cannot approve and
    then revert directly. A nested call back into the frame's target can:
    the inner call approves and returns, and the outer frame decides
    afterwards whether to revert.

    The nonce increment and the `max_cost` collection that `APPROVE`
    performed roll back with the frame's state, so `payer` and
    `sender_approved` have to go with them. Keeping them does not merely
    leak an approval, it produces a free transaction: the payer stays
    bound, the transaction is valid, and fees settle against an account
    whose escrow was rolled back.

    The `returns` case is the control, and is what makes the `reverts`
    case meaningful: the same nested `APPROVE`, with the outer invocation
    returning instead. It must be accepted with the payer bound, which
    pins that the approval really was granted from the nested call --
    otherwise the `reverts` case would be rejected for having never
    approved at all, and would pass against an implementation that keeps
    the approval.
    """
    # The frame's target must be `tx.sender` for the approval scopes, so
    # both invocations run the sender's code. Calldata distinguishes them:
    # the frame supplies some, the self-call supplies none.
    record = Op.SSTORE(SLOT_EXECUTED, 1)
    outer = record + Op.CALL(gas=Op.GAS, address=Op.ADDRESS, address_warm=True)
    outer += Op.REVERT(0, 0) if frame_reverts else Op.STOP
    sender_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=outer,
        # `APPROVE` exits this call context, returning control to `outer`.
        if_false=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT),
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    invocation_gas = sender_code.branch(condition=True).execution_cost(
        fork
    ) + sender_code.branch(condition=False).execution_cost(fork)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            default_frame(
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                target=sender,
                warm=True,
                # The nested call forwards all but a 64th of the gas
                # left, so the budget carries the retention.
                execution_gas=invocation_gas,
                gas_limit_delta=invocation_gas // 64,
                data=Bytes(b"\x01"),
                state_gas_used=record.state_cost(fork),
            ),
        ],
        # Discarding the approval leaves the only frame's transaction with
        # no payer, so it is rejected.
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if frame_reverts
            else None
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                storage={SLOT_EXECUTED: 0 if frame_reverts else 1}
            ),
        },
    )


@pytest.mark.parametrize(
    "middle_reverts,outer_approves",
    [
        pytest.param(
            True,
            False,
            id="middle_reverts",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(False, False, id="middle_returns"),
        pytest.param(True, True, id="middle_reverts_outer_approves"),
    ],
)
def test_call_revert_above_approve_discards_the_approval(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    middle_reverts: bool,
    outer_approves: bool,
) -> None:
    """
    A call that reverts above an `APPROVE` discards the approval
    context it granted, even when the frame itself succeeds.

    The approval context is journaled with the state changes that
    produced it, and reverting a call restores it to the call's
    checkpoint, as reverting a frame or an atomic batch does. Here the
    frame's invocation calls a middle invocation, which calls an inner
    one that approves and returns; the middle one then reverts, rolling
    back the nonce increment and the `max_cost` collection, while the
    outer one returns.

    In the `middle_reverts` case no approval survives, so the
    transaction has no payer and is rejected. Keeping the approval
    would produce a free transaction. The `middle_returns` case is the
    control: the same nested `APPROVE` with the middle invocation
    returning is accepted with the payer bound. In the
    `middle_reverts_outer_approves` case the outer invocation approves
    again after the revert, which only succeeds if the context went back
    to unapproved, and the nonce advances once.
    """
    # The frame's target must be `tx.sender` for the approval scopes, so
    # every invocation runs the sender's code, picked by calldata: the
    # frame supplies two bytes, the middle call one, the inner call none.
    approve = Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT)
    record = Op.SSTORE(SLOT_EXECUTED, 1)
    outer = (
        record
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=Op.ADDRESS,
                args_offset=0,
                args_size=1,
                address_warm=True,
                new_memory_size=1,
            )
        )
        + (approve if outer_approves else Op.STOP)
    )
    middle = Op.POP(
        Op.CALL(gas=Op.GAS, address=Op.ADDRESS, address_warm=True)
    ) + (Op.REVERT(0, 0) if middle_reverts else Op.STOP)
    sender_code = Switch(
        cases=[
            Case(condition=Op.EQ(Op.CALLDATASIZE, 2), action=outer),
            Case(condition=Op.CALLDATASIZE, action=middle),
        ],
        # `APPROVE` exits this call context, returning control to `middle`.
        default_action=approve,
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    invocation_gas = (
        sender_code.branch(case=0).execution_cost(fork)
        + sender_code.branch(case=1).execution_cost(fork)
        + sender_code.branch(case=None).execution_cost(fork)
    )

    approved = not middle_reverts or outer_approves
    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        nonce=1,
        frames=[
            default_frame(
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                target=sender,
                warm=True,
                # Each nested call forwards all but a 64th of the gas
                # left, so the budget carries both retentions.
                execution_gas=invocation_gas,
                gas_limit_delta=invocation_gas // 32,
                data=Bytes(b"\x01\x01"),
                state_gas_used=record.state_cost(fork),
            ),
        ],
        error=(
            None
            if approved
            else TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
        ),
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(
                nonce=2 if approved else 1,
                storage={SLOT_EXECUTED: 1 if approved else 0},
            ),
        },
    )


@pytest.mark.parametrize(
    "inner_attempts_approval",
    [
        pytest.param(True, id="refused_approval"),
        pytest.param(False, id="plain_return"),
    ],
)
def test_refused_approval_reverts_only_its_call_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    inner_attempts_approval: bool,
) -> None:
    """
    A refused `APPROVE` reverts the call frame that issued it, not the
    whole frame: its caller observes a failed call and runs on to a
    successful frame, and the receipt keeps the refused call's gas
    consumed.

    The `plain_return` case is the control, replacing the inner
    `APPROVE` with a bare `STOP`, so that the recorded call outcome
    attributes to the refusal rather than to the nested call itself.
    """
    sender = pre.fund_eoa()

    # The frame carries no approval flags, so any scope it attempts to
    # approve lies outside its own and is refused. Targeting a
    # non-sender is not an option: a frame flagged to approve execution
    # must resolve to the sender to be statically valid. The inner code
    # runs via `DELEGATECALL`, which preserves `ADDRESS`, so the
    # refusal comes from the scope alone — and both executed paths stay
    # straight-line, so the receipt pins the frame's exact gas.
    inner_code = (
        Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION)
        if inner_attempts_approval
        else Op.STOP
    )
    inner = pre.deploy_contract(code=inner_code)
    target_code = Op.SSTORE(
        SLOT_CALL_OUTCOME,
        Op.DELEGATECALL(gas=Op.GAS, address=inner),
        new_value=0 if inner_attempts_approval else 1,
    ) + Op.SSTORE(SLOT_EXECUTED, 1)
    target = pre.deploy_contract(code=target_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(logs=[]),
            # The refused call's gas stays consumed: the frame reports
            # its target's cold entry access, the outer code, and the
            # inner code the revert cut short.
            default_frame(
                target=target,
                code=target_code,
                execution_gas=target_code.execution_cost(fork)
                + inner_code.execution_cost(fork),
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            target: Account(
                storage={
                    SLOT_CALL_OUTCOME: 0 if inner_attempts_approval else 1,
                    SLOT_EXECUTED: 1,
                }
            ),
        },
    )


REFUSED_RETURN_DATA_SIZE = 1024
"""Size of the return-data region a refused `APPROVE` expands memory to."""


@pytest.mark.parametrize(
    "call_opcode,scope",
    [
        pytest.param(Op.CALL, Spec.APPROVE_PAYMENT, id="caller_not_target"),
        pytest.param(
            Op.DELEGATECALL, Spec.ATOMIC_BATCH_FLAG, id="scope_beyond_mask"
        ),
        pytest.param(
            Op.DELEGATECALL, Spec.APPROVE_EXECUTION, id="scope_not_allowed"
        ),
        pytest.param(
            Op.DELEGATECALL, Spec.APPROVE_PAYMENT, id="payer_already_set"
        ),
    ],
)
def test_refused_approval_charges_memory_expansion(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    scope: int,
) -> None:
    """
    A refused `APPROVE` still pays the memory expansion of its
    return-data region: the expansion is the instruction's gas cost,
    charged before any of the checks that refuse it.

    The frame allows only payment approval and the sender has already
    approved payment, so each case fails one check: `CALL` runs the
    inner code at its own address rather than the frame's target, and
    `DELEGATECALL` keeps the target's address but asks for a scope
    outside the approval mask, outside the frame's flags, or already
    granted.
    """
    sender = pre.fund_eoa()

    inner_code = Op.APPROVE(
        0,
        REFUSED_RETURN_DATA_SIZE,
        scope,
        new_memory_size=REFUSED_RETURN_DATA_SIZE,
    )
    inner = pre.deploy_contract(code=inner_code)
    target_code = Op.SSTORE(
        SLOT_CALL_OUTCOME,
        call_opcode(gas=Op.GAS, address=inner),
        new_value=0,
    ) + Op.SSTORE(SLOT_EXECUTED, 1)
    target = pre.deploy_contract(code=target_code)

    tx = FrameTransaction.build(
        fork=fork,
        sender=sender,
        frames=[
            verify_frame(logs=[]),
            default_frame(
                flags=Spec.APPROVE_PAYMENT,
                target=target,
                code=target_code,
                execution_gas=target_code.execution_cost(fork)
                + inner_code.execution_cost(fork),
            ),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            target: Account(storage={SLOT_CALL_OUTCOME: 0, SLOT_EXECUTED: 1}),
        },
    )
