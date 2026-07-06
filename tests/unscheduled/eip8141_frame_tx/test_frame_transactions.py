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
    Environment,
    Frame,
    FrameSignature,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
)

from .helpers import approve_bytecode
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

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
    )

    state_test(
        env=Environment(),
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
        code=approve_bytecode(Spec.APPROVE_EXECUTION_AND_PAYMENT),
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
    )

    state_test(
        env=Environment(),
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
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1, balance=sender_balance),
            payer: Account(nonce=0),
            target: Account(storage={SLOT_EXECUTED: 1}),
        },
    )


def test_atomic_batch_rollback(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Roll back an atomic batch: a `SENDER` frame with the atomic batch
    flag writes storage, and the subsequent frame terminating the batch
    reverts, discarding the write.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(code=Op.SSTORE(SLOT_EXECUTED, 1) + Op.STOP)
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
                mode=Spec.MODE_SENDER,
                flags=Spec.ATOMIC_BATCH_FLAG,
                target=target,
                gas_limit=200_000,
            ),
            Frame(
                mode=Spec.MODE_SENDER,
                target=reverter,
                gas_limit=100_000,
            ),
        ],
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=1),
            target: Account(storage={SLOT_EXECUTED: 0}),
        },
    )


def test_txparam_sender_introspection(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Read the transaction sender through `TXPARAM` from a `DEFAULT`
    frame and store it.
    """
    sender = pre.fund_eoa()
    target = pre.deploy_contract(
        code=Op.SSTORE(SLOT_EXECUTED, Op.TXPARAM(Spec.TXPARAM_SENDER))
        + Op.STOP
    )

    tx = Transaction(
        sender=sender,
        frames=[
            Frame(
                mode=Spec.MODE_VERIFY,
                flags=Spec.APPROVE_EXECUTION_AND_PAYMENT,
                gas_limit=100_000,
            ),
            Frame(
                mode=Spec.MODE_DEFAULT,
                target=target,
                gas_limit=200_000,
            ),
        ],
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            target: Account(storage={SLOT_EXECUTED: sender}),
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
        env=Environment(),
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
        env=Environment(),
        pre=pre,
        tx=tx,
        post={},
    )
