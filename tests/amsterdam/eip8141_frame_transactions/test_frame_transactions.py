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
    Conditional,
    Frame,
    FrameReceipt,
    FrameSignature,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
)

from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

# EIP-8141 is slated for the fork after Amsterdam, so fixtures are
# labeled with the pseudo `Bogota` fork (Amsterdam + EIP-8141), even
# though the spec prototypes the EIP inside the Amsterdam fork module.
# Fill these tests with `--fork Bogota`.
pytestmark = pytest.mark.valid_from("Bogota")

SLOT_EXECUTED = 0x01
"""Storage slot used by target contracts to record execution."""


def test_transfer_with_default_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Transfer ETH from an EOA sender using the default code: a `VERIFY`
    frame authorizes execution and payment against the sender's
    signature entry, and a `SENDER` frame carries the value.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=1)
    transfer_value = 10**17

    tx = Transaction(
        sender=sender,
        frames=[
            Frame(
                mode=Spec.MODE_VERIFY,
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                gas_limit=100_000,
            ),
            Frame(
                mode=Spec.MODE_SENDER,
                target=recipient,
                gas_limit=100_000,
                value=transfer_value,
            ),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS, logs=[]),
                FrameReceipt(status=Spec.STATUS_SUCCESS),
            ],
        ),
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
) -> None:
    """
    Send a frame transaction from a contract account whose code calls
    `APPROVE` to authorize execution and payment, then executes a
    `SENDER` frame calling another contract.
    """
    sender = pre.deploy_contract(
        code=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT),
        balance=10**18,
    )
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            Frame(
                mode=Spec.MODE_VERIFY,
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                gas_limit=100_000,
            ),
            Frame(
                mode=Spec.MODE_SENDER,
                target=target,
                gas_limit=200_000,
            ),
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS),
                FrameReceipt(status=Spec.STATUS_SUCCESS),
            ],
        ),
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
) -> None:
    """
    Sponsor a frame transaction's fees from a second EOA via the
    default code: the sender approves only execution, the payer
    approves only payment, and the sender's balance is untouched.
    """
    sender_balance = 10**18
    sender = pre.fund_eoa(amount=sender_balance)
    payer = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)

    tx = Transaction(
        sender=sender,
        frames=[
            Frame(
                mode=Spec.MODE_VERIFY,
                flags=Spec.APPROVE_EXECUTION,
                gas_limit=100_000,
            ),
            Frame(
                mode=Spec.MODE_VERIFY,
                flags=Spec.APPROVE_PAYMENT,
                target=payer,
                gas_limit=100_000,
            ),
            Frame(
                mode=Spec.MODE_SENDER,
                target=target,
                gas_limit=200_000,
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
        expected_receipt=TransactionReceipt(
            payer=payer,
            frame_receipts=[
                FrameReceipt(status=Spec.STATUS_SUCCESS),
                FrameReceipt(status=Spec.STATUS_SUCCESS),
                FrameReceipt(status=Spec.STATUS_SUCCESS),
            ],
        ),
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
    target = pre.deploy_contract(
        code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.LOG0(0, 0) + Op.STOP
    )
    reverter = pre.deploy_contract(code=Op.REVERT(0, 0))

    store_frame_flags = (
        Spec.ATOMIC_BATCH_FLAG if revert_position == "last" else 0
    )
    revert_frame_flags = (
        Spec.ATOMIC_BATCH_FLAG if revert_position == "first" else 0
    )
    store_frame = Frame(
        mode=Spec.MODE_SENDER,
        flags=store_frame_flags,
        target=target,
        gas_limit=200_000,
    )
    revert_frame = Frame(
        mode=Spec.MODE_SENDER,
        flags=revert_frame_flags,
        target=reverter,
        gas_limit=100_000,
    )
    if revert_position == "last":
        batch = [store_frame, revert_frame]
        expected_frame_receipts = [
            FrameReceipt(status=Spec.STATUS_SUCCESS),
            # The unrolled frame retains its execution status and gas
            # used, but its logs are discarded with its state changes.
            FrameReceipt(status=Spec.STATUS_SUCCESS, logs=[]),
            FrameReceipt(status=Spec.STATUS_FAILURE),
        ]
    else:
        batch = [revert_frame, store_frame]
        expected_frame_receipts = [
            FrameReceipt(status=Spec.STATUS_SUCCESS),
            FrameReceipt(status=Spec.STATUS_FAILURE),
            FrameReceipt(status=Spec.STATUS_SKIPPED, gas_used=0),
        ]

    tx = Transaction(
        sender=sender,
        frames=[
            Frame(
                mode=Spec.MODE_VERIFY,
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                gas_limit=100_000,
            ),
            *batch,
        ],
        expected_receipt=TransactionReceipt(
            payer=sender,
            frame_receipts=expected_frame_receipts,
        ),
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
            Frame(
                mode=Spec.MODE_SENDER,
                target=target,
                gas_limit=200_000,
            ),
            Frame(
                mode=Spec.MODE_VERIFY,
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                gas_limit=100_000,
            ),
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
            Frame(
                mode=Spec.MODE_VERIFY,
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                gas_limit=100_000,
            ),
            Frame(
                mode=Spec.MODE_VERIFY,
                flags=Spec.APPROVE_NONE,
                target=reverter,
                gas_limit=100_000,
            ),
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
    outer = Op.SSTORE(SLOT_EXECUTED, 1) + Op.CALL(
        gas=Op.GAS, address=Op.ADDRESS
    )
    outer += Op.REVERT(0, 0) if frame_reverts else Op.STOP
    sender_code = Conditional(
        condition=Op.CALLDATASIZE,
        if_true=outer,
        # `APPROVE` exits this call context, returning control to `outer`.
        if_false=Op.APPROVE(0, 0, Spec.APPROVE_EXECUTION_AND_PAYMENT),
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            Frame(
                mode=Spec.MODE_DEFAULT,
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                target=sender,
                gas_limit=400_000,
                data=Bytes(b"\x01"),
            ),
        ],
        # Discarding the approval leaves the only frame's transaction with
        # no payer, so it is rejected.
        error=(
            TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
            if frame_reverts
            else None
        ),
        expected_receipt=(
            None
            if frame_reverts
            else TransactionReceipt(
                payer=sender,
                frame_receipts=[FrameReceipt(status=Spec.STATUS_SUCCESS)],
            )
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
