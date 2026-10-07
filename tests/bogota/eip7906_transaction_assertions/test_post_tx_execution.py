"""
Shape and execution context of `POST_TX` frames (EIP-7906): read-only
trailing frames run by the entry point, the only context the diff
instructions run in, and the approval scope they cannot use.
"""

from typing import Callable

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    Frame,
    FrameReceipt,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
)

from tests.bogota.eip8141_frame_transactions.helpers import (
    default_frame,
    sender_frame,
    verify_frame,
)
from tests.bogota.eip8141_frame_transactions.spec import Spec as Spec8141

from .helpers import (
    FUNDS,
    MARKER,
    SLOT_A,
    SLOT_B,
    SLOT_MARKER,
    assertion_transaction,
    body_frame,
    expect_eq,
    frame_gas,
    post_tx_frame,
    reverted_body_receipts,
    success_receipts,
)
from .spec import Spec, ref_spec_7906

REFERENCE_SPEC_GIT_PATH = ref_spec_7906.git_path
REFERENCE_SPEC_VERSION = ref_spec_7906.version

pytestmark = pytest.mark.valid_from("EIP7906")

DIFF_INSTRUCTIONS = [
    pytest.param(Op.TXTRACE(Spec.TXTRACE_BALANCES_CHANGED, 0), id="txtrace"),
    pytest.param(
        Op.TXDIFF(Spec.TXDIFF_ADDRESS_SLOTS_COUNT, 0, 0), id="txdiff"
    ),
    pytest.param(Op.EVENTDATACOPY(0, 0, 0, 0), id="eventdatacopy"),
]
"""One minimal use of each diff instruction."""

EVENT_WORD = 0x7906
"""The data word a body event carries."""


def test_post_tx_success_commits_body(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Commit the execution body when the trailing `POST_TX` frame
    succeeds: the assertion observes the body's single slot change and
    accepts it.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(code=Op.SSTORE(SLOT_A, 1) + Op.STOP)
    assertion = pre.deploy_contract(
        code=expect_eq(Op.TXTRACE(Spec.TXTRACE_SLOTS_CHANGED, 0), 1) + Op.STOP
    )

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=writer)],
            assertion=assertion,
            frame_receipts=success_receipts(3),
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={SLOT_A: 1}),
        },
    )


@pytest.mark.parametrize(
    "violation",
    [
        pytest.param(Op.SSTORE(SLOT_B, 1), id="sstore"),
        pytest.param(Op.TSTORE(SLOT_B, 1), id="tstore"),
        pytest.param(Op.LOG0(0, 0), id="log"),
        pytest.param(Op.CREATE(0, 0, 0), id="create"),
        pytest.param(
            Op.APPROVE(0, 0, Spec8141.APPROVE_EXECUTION_AND_PAYMENT),
            id="approve",
        ),
    ],
)
def test_post_tx_is_static(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    violation: Bytecode,
) -> None:
    """
    Execute the `POST_TX` frame as a `STATICCALL`: any state-changing
    instruction halts it exceptionally, consuming its budget, `APPROVE`
    included, since the `VERIFY` frames' approval exception is not
    granted here. The halt reverts the body like any other assertion
    failure.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(code=Op.SSTORE(SLOT_A, 1) + Op.STOP)
    assertion = pre.deploy_contract(code=violation + Op.STOP)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=writer)],
            assertion=assertion,
            frame_receipts=reverted_body_receipts(
                fork, 1, assertion_halts=True
            ),
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={SLOT_A: 0}),
            assertion: Account(storage={SLOT_B: 0}),
        },
    )


def test_post_tx_caller_and_origin(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Execute a `POST_TX` frame as `ENTRY_POINT`, like `DEFAULT` and
    `VERIFY` frames: both the caller and the origin the frame observes
    are the entry point, not the sender.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(code=Op.SSTORE(SLOT_A, 1) + Op.STOP)
    assertion = pre.deploy_contract(
        code=expect_eq(Op.CALLER, Spec8141.ENTRY_POINT)
        + expect_eq(Op.ORIGIN, Spec8141.ENTRY_POINT)
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=writer)],
            assertion=assertion,
            frame_receipts=success_receipts(3),
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={SLOT_A: 1}),
        },
    )


def test_post_tx_codeless_target(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Run a `POST_TX` frame targeting an account without code like a
    `DEFAULT` frame would: the call has nothing to execute and
    succeeds, so the body commits.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(code=Op.SSTORE(SLOT_A, 1) + Op.STOP)
    codeless = pre.fund_eoa(amount=0)

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=writer)],
            assertion=codeless,
            frame_receipts=success_receipts(3),
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={SLOT_A: 1}),
        },
    )


@pytest.mark.parametrize(
    "scope",
    [
        pytest.param(Spec8141.APPROVE_PAYMENT, id="payment_scope"),
        pytest.param(Spec8141.APPROVE_EXECUTION, id="execution_scope"),
        pytest.param(Spec8141.APPROVE_EXECUTION_AND_PAYMENT, id="full_scope"),
    ],
)
def test_post_tx_approval_scope_is_inert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    scope: int,
) -> None:
    """
    Run a `POST_TX` frame carrying an approval scope on the codeless
    sender like any other `POST_TX` frame: the default code runs only
    in `VERIFY` frames, so the frame succeeds without approving
    anything and the body commits.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(code=Op.SSTORE(SLOT_A, 1) + Op.STOP)

    state_test(
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                verify_frame(),
                body_frame(fork, target=writer),
                post_tx_frame(fork, flags=scope),
            ],
            expected_receipt=TransactionReceipt(
                payer=sender, frame_receipts=success_receipts(3)
            ),
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={SLOT_A: 1}),
        },
    )


def test_post_tx_approval_scope_does_not_lift_static(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Halt `APPROVE` in a `POST_TX` frame whose flags carry the payment
    scope it requests: the scope grants no exception to the static
    context, so the would-be sponsor never becomes the payer.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    sponsor = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec8141.APPROVE_PAYMENT), balance=FUNDS
    )
    writer = pre.deploy_contract(code=Op.SSTORE(SLOT_A, 1) + Op.STOP)

    state_test(
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                verify_frame(),
                body_frame(fork, target=writer),
                post_tx_frame(
                    fork, target=sponsor, flags=Spec8141.APPROVE_PAYMENT
                ),
            ],
            expected_receipt=TransactionReceipt(
                payer=sender,
                frame_receipts=reverted_body_receipts(
                    fork, 1, assertion_halts=True
                ),
            ),
        ),
        post={
            sender: Account(nonce=1),
            sponsor: Account(balance=FUNDS),
            writer: Account(storage={SLOT_A: 0}),
        },
    )


def test_frameparam_reads_post_tx_mode(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Report a `POST_TX` frame's mode through `FRAMEPARAM`, read by an
    earlier frame and by the `POST_TX` frame itself.
    """
    sender = pre.fund_eoa()
    post_tx_index = 2
    mode = Op.FRAMEPARAM(post_tx_index, Spec8141.FRAMEPARAM_MODE)
    recorder = pre.deploy_contract(code=Op.SSTORE(SLOT_A, mode) + Op.STOP)
    assertion = pre.deploy_contract(
        code=expect_eq(mode, Spec.MODE_POST_TX) + Op.STOP
    )

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=recorder)],
            assertion=assertion,
            frame_receipts=success_receipts(3),
        ),
        post={
            sender: Account(nonce=1),
            recorder: Account(storage={SLOT_A: Spec.MODE_POST_TX}),
        },
    )


@pytest.mark.parametrize(
    "call_opcode",
    [
        pytest.param(Op.CALL, id="call"),
        pytest.param(Op.STATICCALL, id="staticcall"),
        pytest.param(Op.DELEGATECALL, id="delegatecall"),
        pytest.param(Op.CALLCODE, id="callcode"),
    ],
)
def test_diff_instructions_in_subcall(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
) -> None:
    """
    Allow the diff instructions anywhere in a `POST_TX` frame's call
    subtree: a contract the assertion reaches through any call
    instruction reads the same diff on its behalf.
    """
    sender = pre.fund_eoa()
    writer = pre.deploy_contract(
        code=Op.SSTORE(SLOT_A, 1)
        + Op.MSTORE(0, EVENT_WORD)
        + Op.LOG0(0, 32)
        + Op.STOP
    )
    reader = pre.deploy_contract(
        code=Op.MSTORE(0, Op.TXTRACE(Spec.TXTRACE_SLOTS_CHANGED, 0))
        + Op.MSTORE(32, Op.TXDIFF(Spec.TXDIFF_SLOT_AFTER, writer, SLOT_A))
        + Op.EVENTDATACOPY(0, 64, 0, 32)
        + Op.RETURN(0, 96)
    )
    assertion = pre.deploy_contract(
        code=expect_eq(
            call_opcode(gas=Op.GAS, address=reader, ret_offset=0, ret_size=96),
            1,
        )
        + expect_eq(Op.MLOAD(0), 1)
        + expect_eq(Op.MLOAD(32), 1)
        + expect_eq(Op.MLOAD(64), EVENT_WORD)
        + Op.STOP
    )

    state_test(
        pre=pre,
        tx=assertion_transaction(
            fork,
            sender,
            body=[body_frame(fork, target=writer)],
            assertion=assertion,
            frame_receipts=success_receipts(3),
        ),
        post={
            sender: Account(nonce=1),
            writer: Account(storage={SLOT_A: 1}),
        },
    )


@pytest.mark.parametrize("instruction", DIFF_INSTRUCTIONS)
@pytest.mark.parametrize(
    "frame_builder",
    [
        pytest.param(sender_frame, id="sender_frame"),
        pytest.param(default_frame, id="default_frame"),
    ],
)
def test_diff_instructions_outside_post_tx(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    instruction: Bytecode,
    frame_builder: Callable[..., Frame],
) -> None:
    """
    Halt the diff instructions exceptionally in a `SENDER` or `DEFAULT`
    frame, consuming its budget: the probe's marker write is discarded
    with the failed frame, which does not invalidate the transaction.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_MARKER, MARKER) + instruction + Op.STOP
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=sender,
            frames=[
                verify_frame(),
                frame_builder(target=probe, gas_limit=frame_gas(fork)),
            ],
            expected_receipt=TransactionReceipt(
                payer=sender,
                frame_receipts=[
                    FrameReceipt(status=Spec8141.STATUS_SUCCESS),
                    FrameReceipt(
                        status=Spec8141.STATUS_FAILURE,
                        gas_used=frame_gas(fork),
                    ),
                ],
            ),
        ),
        post={
            sender: Account(nonce=1),
            probe: Account(storage={SLOT_MARKER: 0}),
        },
    )


@pytest.mark.parametrize("instruction", DIFF_INSTRUCTIONS)
@pytest.mark.frame_tx_incompatible
def test_diff_instructions_in_legacy_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    instruction: Bytecode,
) -> None:
    """
    Halt the diff instructions exceptionally in a transaction that is
    not a frame transaction, which has no `POST_TX` frame to run in,
    consuming the transaction's gas.
    """
    sender = pre.fund_eoa()
    probe = pre.deploy_contract(
        code=Op.SSTORE(SLOT_MARKER, MARKER) + instruction + Op.STOP
    )
    gas_limit = frame_gas(fork)

    state_test(
        pre=pre,
        tx=Transaction(
            sender=sender,
            to=probe,
            gas_limit=gas_limit,
            expected_receipt=TransactionReceipt(cumulative_gas_used=gas_limit),
        ),
        post={probe: Account(storage={SLOT_MARKER: 0})},
    )


@pytest.mark.exception_test
@pytest.mark.parametrize("instruction", DIFF_INSTRUCTIONS)
def test_diff_instructions_in_verify_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    instruction: Bytecode,
) -> None:
    """
    Halt the diff instructions in a `VERIFY` frame, which invalidates
    the transaction like any failed `VERIFY` frame.
    """
    sender = pre.fund_eoa(amount=FUNDS)
    payer = pre.deploy_contract(
        code=instruction + Op.APPROVE(0, 0, Spec8141.APPROVE_PAYMENT),
        balance=FUNDS,
    )
    tx = Transaction(
        sender=sender,
        frames=[
            verify_frame(flags=Spec8141.APPROVE_EXECUTION),
            verify_frame(target=payer, flags=Spec8141.APPROVE_PAYMENT),
        ],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )
    state_test(pre=pre, tx=tx, post={sender: Account(nonce=0)})


@pytest.mark.exception_test
def test_post_tx_without_payment(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Invalidate a transaction whose only frames are `POST_TX` frames:
    nothing approves payment, so the transaction fails the end-of-frames
    rule regardless of the assertion's outcome.
    """
    sender = pre.fund_eoa()
    assertion = pre.deploy_contract(code=Op.STOP)
    tx = Transaction(
        sender=sender,
        frames=[post_tx_frame(fork, target=assertion)],
        error=TransactionException.TYPE_6_INVALID_FRAME_EXECUTION,
    )
    state_test(pre=pre, tx=tx, post={})
