"""
Test cases for invalid Block Access Lists.

These tests verify that clients properly reject blocks with corrupted BALs.
"""

from typing import Callable

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountChange,
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BlockException,
    Initcode,
    Op,
    Storage,
    Transaction,
    Withdrawal,
    compute_create_address,
)
from execution_testing.test_types.block_access_list.modifiers import (
    append_account,
    append_change,
    append_storage,
    duplicate_account,
    duplicate_balance_change,
    duplicate_code_change,
    duplicate_nonce_change,
    duplicate_slot_change,
    duplicate_storage_read,
    duplicate_storage_slot,
    insert_storage_read,
    modify_balance,
    modify_nonce,
    modify_storage,
    remove_accounts,
    remove_balances,
    remove_nonces,
    reverse_accounts,
    swap_bal_indices,
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
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
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
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                    }
                ).modify(modify_nonce(sender, block_access_index=1, nonce=42)),
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
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=1,
                                            post_value=0x01,
                                        )
                                    ],
                                ),
                                BalStorageSlot(
                                    slot=0x02,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=1,
                                            post_value=0x02,
                                        )
                                    ],
                                ),
                                BalStorageSlot(
                                    slot=0x03,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=1,
                                            post_value=0x03,
                                        )
                                    ],
                                ),
                            ],
                        ),
                    }
                ).modify(
                    # Corrupt storage value for slot 0x02
                    modify_storage(
                        contract, block_access_index=1, slot=0x02, value=0xFF
                    )
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
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                        sender2: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=2, post_nonce=1
                                )
                            ],
                        ),
                        receiver: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1, post_balance=10**15
                                ),
                                BalBalanceChange(
                                    block_access_index=2,
                                    post_balance=3 * 10**15,
                                ),
                            ],
                        ),
                    }
                ).modify(swap_bal_indices(1, 2)),
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
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                    }
                ).modify(
                    append_account(
                        BalAccountChange(
                            address=phantom,
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
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
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                        receiver: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1, post_balance=10**15
                                )
                            ],
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
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                        receiver: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1, post_balance=10**15
                                )
                            ],
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
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                ),
                                BalNonceChange(
                                    block_access_index=2, post_nonce=2
                                ),
                            ],
                        ),
                        contract: BalAccountExpectation(
                            storage_changes=[
                                BalStorageSlot(
                                    slot=0x01,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=1,
                                            post_value=0x01,
                                        )
                                    ],
                                ),
                                BalStorageSlot(
                                    slot=0x02,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=1,
                                            post_value=0x02,
                                        )
                                    ],
                                ),
                            ],
                        ),
                        receiver: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=2, post_balance=10**15
                                )
                            ],
                        ),
                    }
                ).modify(
                    remove_nonces(sender),
                    modify_storage(
                        contract, block_access_index=1, slot=0x01, value=0xFF
                    ),
                    remove_balances(receiver),
                    swap_bal_indices(1, 2),
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
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                        receiver: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1, post_balance=10**15
                                )
                            ],
                        ),
                    }
                ).modify(remove_accounts(receiver)),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_missing_withdrawal_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject blocks where BAL is missing an account
    that was modified only by a withdrawal.

    Alice sends 5 wei to Bob (1 transaction).
    Charlie receives 10 gwei withdrawal.
    BAL is corrupted by removing Charlie's entry entirely.
    Clients must detect that Charlie's balance was modified by the
    withdrawal but has no corresponding BAL entry.
    """
    alice = pre.fund_eoa()
    bob = pre.fund_eoa(amount=0)
    charlie = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=alice,
        to=bob,
        value=5,
        gas_limit=21_000,
    )

    blockchain_test(
        pre=pre,
        post={
            alice: Account(nonce=0),
            bob: None,
            charlie: None,
        },
        blocks=[
            Block(
                txs=[tx],
                withdrawals=[
                    Withdrawal(
                        index=0,
                        validator_index=0,
                        address=charlie,
                        amount=10,
                    )
                ],
                exception=BlockException.INVALID_BAL_MISSING_ACCOUNT,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        alice: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                        bob: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1, post_balance=5
                                )
                            ],
                        ),
                        charlie: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=2,
                                    post_balance=10 * 10**9,
                                )
                            ],
                        ),
                    }
                ).modify(remove_accounts(charlie)),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_missing_withdrawal_account_empty_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject blocks where BAL is missing an account
    that was modified only by a withdrawal, in a block with no transactions.

    Charlie receives 10 gwei withdrawal in an empty block.
    BAL is corrupted by removing Charlie's entry entirely.
    """
    charlie = pre.fund_eoa(amount=0)

    blockchain_test(
        pre=pre,
        post={
            charlie: None,
        },
        blocks=[
            Block(
                txs=[],
                withdrawals=[
                    Withdrawal(
                        index=0,
                        validator_index=0,
                        address=charlie,
                        amount=10,
                    )
                ],
                exception=BlockException.INVALID_BAL_MISSING_ACCOUNT,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        charlie: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1,
                                    post_balance=10 * 10**9,
                                )
                            ],
                        ),
                    }
                ).modify(remove_accounts(charlie)),
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
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1, post_balance=10**15
                                )
                            ],
                        ),
                    }
                ).modify(
                    modify_balance(
                        receiver, block_access_index=1, balance=999999
                    )
                ),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "modifier",
    [
        pytest.param(
            lambda idx, **actors: append_change(
                account=actors["oracle"],
                change=BalNonceChange(block_access_index=idx, post_nonce=999),
            ),
            id="extra_nonce",
        ),
        pytest.param(
            lambda idx, **actors: append_account(
                BalAccountChange(
                    address=actors["charlie"],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=idx, post_balance=999
                        )
                    ],
                )
            ),
            id="extra_balance",
        ),
        pytest.param(
            lambda idx, **actors: append_change(
                account=actors["oracle"],
                change=BalCodeChange(
                    block_access_index=idx, new_code=b"Amsterdam"
                ),
            ),
            id="extra_code",
        ),
        pytest.param(
            lambda idx, **actors: append_storage(
                address=actors["oracle"],
                slot=0,
                change=BalStorageChange(
                    block_access_index=idx, post_value=0xCAFE
                ),
            ),
            id="extra_storage_write_touched",
        ),
        pytest.param(
            lambda idx, **actors: append_storage(
                address=actors["oracle"],
                slot=1,
                change=BalStorageChange(
                    block_access_index=idx, post_value=0xCAFE
                ),
            ),
            id="extra_storage_write_untouched",
        ),
        pytest.param(
            lambda idx, **actors: append_account(
                BalAccountChange(
                    address=actors["charlie"],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0,
                            slot_changes=[
                                BalStorageChange(
                                    block_access_index=idx,
                                    post_value=0xDEAD,
                                )
                            ],
                        )
                    ],
                )
            ),
            id="extra_storage_write_uninvolved_account",
        ),
        pytest.param(
            lambda idx, **actors: append_account(  # noqa: ARG005
                BalAccountChange(
                    address=actors["charlie"],
                )
            ),
            id="extra_account_access",
        ),
        pytest.param(
            lambda idx, **actors: append_storage(  # noqa: ARG005
                address=actors["oracle"],
                slot=999,
                read=True,
            ),
            id="extra_storage_read",
        ),
    ],
)
@pytest.mark.parametrize(
    "bal_index",
    [
        pytest.param(1, id="same_tx"),
        pytest.param(2, id="system_tx"),
        pytest.param(3, id="out_of_bounds"),
    ],
)
def test_bal_invalid_extraneous_entries(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    modifier: Callable,
    bal_index: int,
) -> None:
    """
    Test that clients reject blocks where BAL contains extraneous entries.

    Alice sends 100 wei to Oracle (1 transaction). Oracle reads storage slot 0.
    Charlie is uninvolved in this transaction.
    A valid BAL is created containing nonce change for Alice, balance change
    and storage read for Oracle which is further modified as:

    - extra_nonce: Extra nonce change for Oracle.
    - extra_balance: Extra balance change for uninvolved Charlie.
    - extra_code: Extra code change for Oracle.
    - extra_storage_write_touched: Extra storage write for an already read slot
      (slot 0) for Oracle.
    - extra_storage_write_untouched: Extra storage write for an unread slot
      (slot 1) for Oracle.
    - extra_storage_write_uninvolved_account: Extra storage write for
      uninvolved account (Charlie) that isn't accessed at all.
    - extra_account_access: Uninvolved account (Charlie) added to BAL entirely.
    - extra_storage_read: Extra storage read for Oracle (slot 999).

    BAL is corrupted with extraneous entries at various block_access_index
    values:
    - bal_index=1: current transaction
    - bal_index=2: system transaction (tx_count + 1)
    - bal_index=3: beyond system transaction (tx_count + 2)
    """
    transfer_value = 100

    alice = pre.fund_eoa()
    oracle = pre.deploy_contract(code=Op.SLOAD(0), storage={0: 42})
    charlie = pre.fund_eoa(amount=0)

    tx = Transaction(
        sender=alice,
        to=oracle,
        value=transfer_value,
        gas_limit=1_000_000,
    )

    blockchain_test(
        pre=pre,
        # The block reverts and the post state remains unchanged.
        post=pre,
        blocks=[
            Block(
                txs=[tx],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    # Valid BAL expectation: nonce change for Alice,
                    # balance change and storage read for Oracle.
                    account_expectations={
                        alice: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1, post_nonce=1
                                )
                            ],
                        ),
                        oracle: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1,
                                    post_balance=transfer_value,
                                )
                            ],
                            storage_reads=[0],
                        ),
                    }
                ).modify(
                    # The parameterized modifier is applied to the BAL
                    # which adds an extraneous entry.
                    modifier(
                        idx=bal_index,
                        alice=alice,
                        oracle=oracle,
                        charlie=charlie,
                    )
                ),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "modifier",
    [
        pytest.param(
            lambda alice, **_: duplicate_nonce_change(alice, 1),
            id="duplicate_nonce_change",
        ),
        pytest.param(
            lambda oracle, **_: duplicate_balance_change(oracle, 1),
            id="duplicate_balance_change",
        ),
        pytest.param(
            lambda created, **_: duplicate_code_change(created, 1),
            id="duplicate_code_change",
        ),
        pytest.param(
            lambda oracle, **_: duplicate_storage_slot(oracle, 1),
            id="duplicate_storage_slot",
        ),
        pytest.param(
            lambda oracle, **_: duplicate_storage_read(oracle, 2),
            id="duplicate_storage_read",
        ),
        pytest.param(
            lambda oracle, **_: duplicate_slot_change(oracle, 1, 1),
            id="duplicate_slot_change",
        ),
        pytest.param(
            lambda oracle, **_: insert_storage_read(oracle, 1),
            id="storage_key_in_both_changes_and_reads",
        ),
    ],
)
def test_bal_invalid_duplicate_entries(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    modifier: Callable,
) -> None:
    """
    Test that clients reject blocks where BAL contains duplicate entries.

    Oracle writes storage, reads storage, and CREATEs a small contract.
    Verify the EIP-7928 uniqueness constraints: each block_access_index
    must appear at most once per change list (nonce, balance, code,
    slot), each storage key at most once in storage_changes and
    storage_reads, and no key in both.
    """
    alice = pre.fund_eoa()
    deploy_code = b"\x13\x37"
    initcode = Initcode(deploy_code=deploy_code)
    initcode_word = int.from_bytes(bytes(initcode).ljust(32, b"\x00"), "big")
    oracle = pre.deploy_contract(
        code=(
            Op.SSTORE(1, 0x42)
            + Op.SLOAD(2)
            + Op.MSTORE(0, initcode_word)
            + Op.CREATE(0, 0, len(initcode))
        ),
        storage={2: 0x84},
    )
    created = compute_create_address(address=oracle, nonce=1)

    tx = Transaction(
        sender=alice,
        to=oracle,
        value=100,
        gas_limit=2_000_000,
    )

    blockchain_test(
        pre=pre,
        post=pre,
        blocks=[
            Block(
                txs=[tx],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={
                        alice: BalAccountExpectation(
                            nonce_changes=[
                                BalNonceChange(
                                    block_access_index=1,
                                    post_nonce=1,
                                ),
                            ],
                        ),
                        oracle: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1,
                                    post_balance=100,
                                ),
                            ],
                            storage_changes=[
                                BalStorageSlot(
                                    slot=1,
                                    slot_changes=[
                                        BalStorageChange(
                                            block_access_index=1,
                                            post_value=0x42,
                                        ),
                                    ],
                                ),
                            ],
                            storage_reads=[2],
                        ),
                        created: BalAccountExpectation(
                            code_changes=[
                                BalCodeChange(
                                    block_access_index=1,
                                    new_code=deploy_code,
                                ),
                            ],
                        ),
                    }
                ).modify(
                    modifier(
                        alice=alice,
                        oracle=oracle,
                        created=created,
                    )
                ),
            )
        ],
    )
