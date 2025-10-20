"""
Test cases for invalid Block Access Lists.

These tests verify that clients properly reject blocks with corrupted BALs.
"""

import pytest

from ethereum_test_exceptions import BlockException
from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Storage,
    Transaction,
)
from ethereum_test_tools import (
    Opcodes as Op,
)
from ethereum_test_types.block_access_list import (
    BalAccountChange,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessListExpectation,
)
from ethereum_test_types.block_access_list.modifiers import (
    append_account,
    duplicate_account,
    modify_balance,
    modify_nonce,
    modify_storage,
    remove_accounts,
    remove_balances,
    remove_nonces,
    reverse_accounts,
    swap_tx_indices,
)

from .spec import ref_spec_7928

REFERENCE_SPEC_GIT_PATH = ref_spec_7928.git_path
REFERENCE_SPEC_VERSION = ref_spec_7928.version


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_missing_nonce(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject blocks where BAL is missing required nonce
    changes.
    """
    sender = pre.fund_eoa(amount=10**18)
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=sender,
        to=receiver,
        value=10**15,
        gas_limit=21_000,
    )

    blockchain_test(
        pre=pre,
        post={
            sender: Account(balance=10**18, nonce=0),
            receiver: None,
        },
        blocks=[
            Block(
                txs=[tx],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        sender: BalAccountExpectation(
                            nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                        ),
                    }
                ).modify(remove_nonces(sender)),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_nonce_value(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject blocks where BAL contains incorrect nonce value.
    """
    sender = pre.fund_eoa(amount=10**18)
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=sender,
        to=receiver,
        value=10**15,
        gas_limit=21_000,
    )

    blockchain_test(
        pre=pre,
        post={
            sender: Account(balance=10**18, nonce=0),  # Unchanged
            receiver: None,
        },
        blocks=[
            Block(
                txs=[tx],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        sender: BalAccountExpectation(
                            nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                        ),
                    }
                ).modify(modify_nonce(sender, tx_index=1, nonce=42)),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_storage_value(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject blocks where BAL contains incorrect storage
    values.
    """
    sender = pre.fund_eoa(amount=10**18)

    # Simple storage contract with canary values
    storage = Storage({1: 0, 2: 0, 3: 0})  # type: ignore
    contract = pre.deploy_contract(
        code=Op.SSTORE(1, 1) + Op.SSTORE(2, 2) + Op.SSTORE(3, 3),
        storage=storage.canary(),
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100_000,
    )

    blockchain_test(
        pre=pre,
        post={
            sender: Account(balance=10**18, nonce=0),
            contract: Account(storage=storage.canary()),
        },
        blocks=[
            Block(
                txs=[tx],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        contract: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=0x01,
                                    slot_changes=[BalStorageChange(tx_index=1, post_value=0x01)],
                                ),
                                BalStorageSlot(
                                    slot=0x02,
                                    slot_changes=[BalStorageChange(tx_index=1, post_value=0x02)],
                                ),
                                BalStorageSlot(
                                    slot=0x03,
                                    slot_changes=[BalStorageChange(tx_index=1, post_value=0x03)],
                                ),
                            ],
                        ),
                    }
                ).modify(
                    # Corrupt storage value for slot 0x02
                    modify_storage(contract, tx_index=1, slot=0x02, value=0xFF)
                ),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_tx_order(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject blocks where BAL has incorrect transaction
    ordering.
    """
    sender1 = pre.fund_eoa(amount=10**18)
    sender2 = pre.fund_eoa(amount=10**18)
    receiver = pre.fund_eoa(amount=0)

    tx1 = Transaction(
        sender=sender1,
        to=receiver,
        value=10**15,
        gas_limit=21_000,
    )

    tx2 = Transaction(
        sender=sender2,
        to=receiver,
        value=2 * 10**15,
        gas_limit=21_000,
    )

    blockchain_test(
        pre=pre,
        post={
            sender1: Account(balance=10**18, nonce=0),
            sender2: Account(balance=10**18, nonce=0),
            receiver: None,
        },
        blocks=[
            Block(
                txs=[tx1, tx2],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        sender1: BalAccountExpectation(
                            nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                        ),
                        sender2: BalAccountExpectation(
                            nonce_changes=[BalNonceChange(tx_index=2, post_nonce=1)],
                        ),
                        receiver: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(tx_index=1, post_balance=10**15),
                                BalBalanceChange(tx_index=2, post_balance=3 * 10**15),
                            ],
                        ),
                    }
                ).modify(swap_tx_indices(1, 2)),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject blocks where BAL contains accounts that don't
    exist.
    """
    sender = pre.fund_eoa(amount=10**18)
    receiver = pre.fund_eoa(amount=0)
    phantom = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=sender,
        to=receiver,
        value=10**15,
        gas_limit=21_000,
    )

    blockchain_test(
        pre=pre,
        post={
            sender: Account(balance=10**18, nonce=0),
            receiver: None,
            phantom: None,
        },
        blocks=[
            Block(
                txs=[tx],
                exception=BlockException.INVALID_BAL_EXTRA_ACCOUNT,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        sender: BalAccountExpectation(
                            nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                        ),
                    }
                ).modify(
                    append_account(
                        BalAccountChange(
                            address=phantom,
                            nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                        )
                    )
                ),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_duplicate_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject blocks where BAL contains duplicate account
    entries.
    """
    sender = pre.fund_eoa(amount=10**18)
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=sender,
        to=receiver,
        value=10**15,
        gas_limit=21_000,
    )

    blockchain_test(
        pre=pre,
        post={
            sender: Account(balance=10**18, nonce=0),
            receiver: None,
        },
        blocks=[
            Block(
                txs=[tx],
                exception=BlockException.INCORRECT_BLOCK_FORMAT,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        sender: BalAccountExpectation(
                            nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                        ),
                        receiver: BalAccountExpectation(
                            balance_changes=[BalBalanceChange(tx_index=1, post_balance=10**15)],
                        ),
                    }
                ).modify(duplicate_account(sender)),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_account_order(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject blocks where BAL has incorrect account ordering.
    """
    sender = pre.fund_eoa(amount=10**18)
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=sender,
        to=receiver,
        value=10**15,
        gas_limit=21_000,
    )

    blockchain_test(
        pre=pre,
        post={
            sender: Account(balance=10**18, nonce=0),
            receiver: None,
        },
        blocks=[
            Block(
                txs=[tx],
                exception=BlockException.INCORRECT_BLOCK_FORMAT,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        sender: BalAccountExpectation(
                            nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                        ),
                        receiver: BalAccountExpectation(
                            balance_changes=[BalBalanceChange(tx_index=1, post_balance=10**15)],
                        ),
                    }
                ).modify(reverse_accounts()),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_complex_corruption(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """Test complex BAL corruption with multiple transformations."""
    sender = pre.fund_eoa(amount=10**18)
    receiver = pre.fund_eoa(amount=0)

    storage = Storage({1: 0, 2: 0})  # type: ignore
    contract = pre.deploy_contract(
        code=Op.SSTORE(1, 1) + Op.SSTORE(2, 2),
        storage=storage.canary(),
    )

    tx1 = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100_000,
    )

    tx2 = Transaction(
        sender=sender,
        to=receiver,
        value=10**15,
        gas_limit=21_000,
    )

    blockchain_test(
        pre=pre,
        post={
            sender: Account(balance=10**18, nonce=0),
            contract: Account(storage=storage.canary()),
            receiver: None,
        },
        blocks=[
            Block(
                txs=[tx1, tx2],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        sender: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(tx_index=1, post_nonce=1),
                                BalNonceChange(tx_index=2, post_nonce=2),
                            ],
                        ),
                        contract: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=0x01,
                                    slot_changes=[BalStorageChange(tx_index=1, post_value=0x01)],
                                ),
                                BalStorageSlot(
                                    slot=0x02,
                                    slot_changes=[BalStorageChange(tx_index=1, post_value=0x02)],
                                ),
                            ],
                        ),
                        receiver: BalAccountExpectation(
                            balance_changes=[BalBalanceChange(tx_index=2, post_balance=10**15)],
                        ),
                    }
                ).modify(
                    remove_nonces(sender),
                    modify_storage(contract, tx_index=1, slot=0x01, value=0xFF),
                    remove_balances(receiver),
                    swap_tx_indices(1, 2),
                ),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_missing_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject blocks where BAL is missing an entire account.
    """
    sender = pre.fund_eoa(amount=10**18)
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=sender,
        to=receiver,
        value=10**15,
        gas_limit=21_000,
    )

    blockchain_test(
        pre=pre,
        post={
            sender: Account(balance=10**18, nonce=0),
            receiver: None,
        },
        blocks=[
            Block(
                txs=[tx],
                exception=BlockException.INVALID_BAL_MISSING_ACCOUNT,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        sender: BalAccountExpectation(
                            nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                        ),
                        receiver: BalAccountExpectation(
                            balance_changes=[BalBalanceChange(tx_index=1, post_balance=10**15)],
                        ),
                    }
                ).modify(remove_accounts(receiver)),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_balance_value(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject blocks where BAL contains incorrect balance value.
    """
    sender = pre.fund_eoa(amount=10**18)
    receiver = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=sender,
        to=receiver,
        value=10**15,
        gas_limit=21_000,
    )

    blockchain_test(
        pre=pre,
        post={
            sender: Account(balance=10**18, nonce=0),
            receiver: None,
        },
        blocks=[
            Block(
                txs=[tx],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        receiver: BalAccountExpectation(
                            balance_changes=[BalBalanceChange(tx_index=1, post_balance=10**15)],
                        ),
                    }
                ).modify(modify_balance(receiver, tx_index=1, balance=999999)),
            )
        ],
    )
