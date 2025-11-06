"""
Tests for EIP-7805 FOCIL (Fork-choice enforced Inclusion Lists) block
validation.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Transaction,
)

from .spec import Spec, ref_spec_7805

REFERENCE_SPEC_GIT_PATH = ref_spec_7805.git_path
REFERENCE_SPEC_VERSION = ref_spec_7805.version

pytestmark = pytest.mark.valid_from("Eip7805")


def test_focil_block_validation_accepts_empty_inclusion_list(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Verify the EL correctly validates a payload with zero inclusion list
    transactions.

    Test ID: test_focil_block_validation_accepts_empty_inclusion_list
    Coverage: The EL receives a payload with no inclusion list
        transactions. The payload MUST be considered valid.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=alice,
        to=bob,
        value=100,
    )

    block = Block(
        txs=[tx],
        # No inclusion list transactions - empty by default
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(balance=100),
        },
    )


def test_focil_block_validation_with_inclusion_list_transactions(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Verify the EL correctly validates a payload with inclusion list
    transactions.

    Test ID: test_focil_block_validation_with_inclusion_list_transactions
    Coverage: The EL receives a payload with two inclusion list
        transactions. The payload MUST include both transactions.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa()
    charlie = pre.fund_eoa(amount=0)

    tx1 = Transaction(
        sender=alice,
        to=charlie,
        value=100,
    )

    tx2 = Transaction(
        sender=bob,
        to=charlie,
        value=200,
    )

    block = Block(
        txs=[tx1, tx2],
        inclusion_list_transactions=[tx1, tx2],
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(nonce=1),
            charlie: Account(balance=300),
        },
    )


@pytest.mark.parametrize(
    "invalid_tx_type",
    [
        "insufficient_balance_for_gas",
        "insufficient_balance",
        "nonce_too_high",
        "gas_limit_exceeds_block",
    ],
)
def test_focil_block_validation_ignores_invalid_transactions_in_inclusion_list(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    invalid_tx_type: str,
) -> None:
    """
    Verify the EL ignores various types of invalid transactions in the
    inclusion list.

    Test ID:
        test_focil_block_validation_ignores_invalid_transactions_in_inclusion_list
    Coverage: The EL receives a payload with an inclusion list
        containing different types of invalid transactions. Invalid
        transactions MUST be ignored and only valid transactions MUST be
        included in the block.
    """
    alice = pre.fund_eoa(amount=1000)
    bob = pre.fund_eoa()
    charlie = pre.fund_eoa(amount=21000)
    alex = pre.fund_eoa(amount=30000000050)

    # Create invalid transaction based on test parameter
    if invalid_tx_type == "insufficient_balance_for_gas":
        tx_invalid = Transaction(
            sender=charlie,
            to=alice,
            value=50,
            gas_limit=21000,
        )
    elif invalid_tx_type == "insufficient_balance":
        tx_invalid = Transaction(
            sender=charlie,
            to=alice,
            value=10000,
            gas_limit=21000,
        )
    elif invalid_tx_type == "nonce_too_high":
        tx_invalid = Transaction(
            sender=charlie,
            to=alice,
            value=50,
            nonce=100,
            gas_limit=21000,
        )
    elif invalid_tx_type == "gas_limit_exceeds_block":
        tx_invalid = Transaction(
            sender=alex,
            to=alice,
            value=50,
            gas_limit=30000000000,
        )
    else:
        raise ValueError(f"Unknown invalid_tx_type: {invalid_tx_type}")

    # Valid transaction from bob
    tx_valid = Transaction(
        sender=bob,
        to=alice,
        value=100,
    )

    block = Block(
        txs=[tx_valid],
        inclusion_list_transactions=[tx_invalid, tx_valid],
    )

    alice_expected_balance = 1000 + 100

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            charlie: Account(nonce=0),  # Invalid tx didn't execute
            bob: Account(nonce=1),  # Valid tx executed
            alice: Account(balance=alice_expected_balance),
        },
    )


@pytest.mark.exception_test
def test_focil_block_validation_returns_error_when_inclusion_list_tx_is_omitted(  # noqa: E501
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Verify block validation returns INCLUSION_LIST_UNSATISFIED when a
    valid IL tx is omitted.

    Test ID:
        test_focil_block_validation_returns_error_when_inclusion_list_tx_is_omitted
    Coverage: The inclusion list references a transaction valid against
        the current state, but the block body omits it. The EL MUST
        return INCLUSION_LIST_UNSATISFIED.
    """
    from execution_testing import BlockException

    alice = pre.fund_eoa()
    bob = pre.fund_eoa()
    charlie = pre.fund_eoa(amount=0)

    # Two valid transactions
    tx1 = Transaction(
        sender=alice,
        to=charlie,
        value=100,
    )

    tx2 = Transaction(
        sender=bob,
        to=charlie,
        value=200,
    )

    # Block only includes tx1, but inclusion list has both tx1 and tx2
    block = Block(
        txs=[tx1],
        inclusion_list_transactions=[tx1, tx2],
        exception=BlockException.INCLUSION_LIST_UNSATISFIED,
        # t8n doesn't validate inclusion lists
        skip_exception_verification=True,
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={},
    )


def test_focil_block_validation_succeeds_with_interdependent_inclusion_list_transactions(  # noqa: E501
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Verify the EL correctly processes interdependent inclusion list
    transactions.

    Test ID:
        test_focil_block_validation_succeeds_with_interdependent_inclusion_list_transactions
    Coverage: Inclusion list contains [tx_A, tx_B] where tx_A funds a
        new account and tx_B is sent from that new account. Both
        transactions MUST be included.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)
    charlie = pre.fund_eoa(amount=0)

    # tx1: Alice funds Bob
    tx1 = Transaction(
        sender=alice,
        to=bob,
        value=10**18,
    )

    # tx2: Bob sends to Charlie (depends on tx1 executing first)
    tx2 = Transaction(
        sender=bob,
        to=charlie,
        value=1000,
        nonce=0,
    )

    # Both transactions in the block and inclusion list
    block = Block(
        txs=[tx1, tx2],
        inclusion_list_transactions=[tx1, tx2],
    )

    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            alice: Account(nonce=1),
            bob: Account(nonce=1),
            charlie: Account(balance=1000),
        },
    )


def test_focil_block_validation_accepts_full_inclusion_list(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Verify the EL validates a payload with maximum inclusion list
    transactions.

    Test ID: test_focil_block_validation_accepts_full_inclusion_list
    Coverage: The EL receives a payload with many inclusion list
        transactions approaching size limits. The payload MUST include
        all transactions.
    """
    receiver = pre.fund_eoa(amount=0)
    num_transactions = (
        Spec.MAX_BYTES_PER_INCLUSION_LIST * Spec.IL_COMMITTEE_SIZE // 100
    )

    senders = [pre.fund_eoa() for _ in range(num_transactions)]
    transactions = []

    # Create transactions from each sender
    for sender in senders:
        tx = Transaction(
            sender=sender,
            to=receiver,
            value=100,
        )
        transactions.append(tx)

    # All transactions in the block and inclusion list
    block = Block(
        txs=transactions,
        inclusion_list_transactions=transactions,
    )

    # Build expected post state
    post = {receiver: Account(balance=num_transactions * 100)}
    for sender in senders:
        post[sender] = Account(nonce=1)

    blockchain_test(
        pre=pre,
        blocks=[block],
        post=post,
    )
