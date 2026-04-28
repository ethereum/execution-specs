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
    Environment,
    Fork,
    Hash,
    Header,
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
    modify_code,
    modify_nonce,
    modify_storage,
    remove_accounts,
    remove_balances,
    remove_code,
    remove_nonces,
    remove_storage,
    remove_storage_reads,
    reverse_accounts,
    sort_accounts_by_address,
    swap_bal_indices,
)

from .spec import ref_spec_7928
from .test_block_access_lists_eip4788 import (
    SYSTEM_ADDRESS,
    beacon_root_system_call_expectations,
)

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
@pytest.mark.parametrize(
    "scenario",
    ["balance_change", "access_only"],
)
def test_bal_invalid_missing_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    scenario: str,
) -> None:
    """
    Test that clients reject blocks where BAL omits an account that was
    touched during block execution.

    Covers both the case where the omitted account has a balance change
    (value transfer recipient) and the access-only case (account read via
    ``BALANCE`` with no state change).
    """
    sender = pre.fund_eoa(amount=10**18)
    sender_expectation = BalAccountExpectation(
        nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=1)],
    )

    if scenario == "balance_change":
        omitted = pre.fund_eoa(amount=0)
        tx = Transaction(
            sender=sender,
            to=omitted,
            value=10**15,
            gas_limit=21_000,
        )
        post: dict = {
            sender: Account(balance=10**18, nonce=0),
            omitted: None,
        }
        account_expectations: dict = {
            sender: sender_expectation,
            omitted: BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=10**15)
                ],
            ),
        }
    elif scenario == "access_only":
        omitted = pre.fund_eoa(amount=1)
        checker = pre.deploy_contract(code=Op.BALANCE(omitted))
        tx = Transaction(
            sender=sender,
            to=checker,
            gas_limit=100_000,
        )
        post = {
            sender: Account(balance=10**18, nonce=0),
            omitted: Account(balance=1),
            checker: Account(),
        }
        account_expectations = {
            sender: sender_expectation,
            checker: BalAccountExpectation.empty(),
            omitted: BalAccountExpectation.empty(),
        }
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[
            Block(
                txs=[tx],
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=account_expectations,
                ).modify(remove_accounts(omitted)),
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
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
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
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
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
def test_bal_invalid_surplus_system_address_from_system_call(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject a BAL that includes SYSTEM_ADDRESS solely because
    it was the synthetic caller of a pre-execution system operation.
    """
    block_timestamp = 12
    beacon_root = Hash(0xABCDEF)

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[],
                parent_beacon_block_root=beacon_root,
                timestamp=block_timestamp,
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations=beacon_root_system_call_expectations(
                        block_timestamp,
                        beacon_root,
                    )
                ).modify(
                    append_account(
                        BalAccountChange(address=SYSTEM_ADDRESS),
                    )
                ),
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


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_hash_mismatch(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject blocks where the BAL hash in the header
    does not match the actual BAL content.

    Unlike other invalid BAL tests which corrupt the BAL content while
    keeping the header hash consistent with the corrupted data, this
    test keeps the BAL valid but injects a wrong hash into the header
    via rlp_modifier.
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
                rlp_modifier=Header(block_access_list_hash=Hash(1)),
                exception=[
                    BlockException.INVALID_BAL_HASH,
                    BlockException.INVALID_BLOCK_HASH,
                ],
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "modifier",
    [
        pytest.param(
            lambda oracle, **_: remove_storage(oracle),
            id="missing_storage_change",
        ),
        pytest.param(
            lambda oracle, **_: remove_storage_reads(oracle),
            id="missing_storage_read",
        ),
        pytest.param(
            lambda created, **_: remove_code(created),
            id="missing_code_change",
        ),
        pytest.param(
            lambda created, **_: modify_code(
                created, block_access_index=1, code=b"\xde\xad"
            ),
            id="wrong_code_value",
        ),
    ],
)
def test_bal_invalid_field_entries(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    modifier: Callable,
) -> None:
    """
    Test that clients reject blocks with missing or incorrect
    field-level BAL entries.

    Oracle writes storage slot 1, reads storage slot 2, and CREATEs a
    small contract. A valid BAL is created containing all changes, then
    corrupted by the parameterized modifier:

    - missing_storage_change: Oracle's storage writes removed.
    - missing_storage_read: Oracle's storage reads removed.
    - missing_code_change: Created contract's code change removed.
    - wrong_code_value: Created contract's deployed bytecode wrong.
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
                        oracle=oracle,
                        created=created,
                    )
                ),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_withdrawal_balance_value(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that clients reject blocks where BAL contains an incorrect
    balance value for an account modified only by a withdrawal.

    Charlie receives a 10 gwei withdrawal in an empty block.
    BAL is corrupted by changing Charlie's post-balance to 999 instead
    of the correct 10_000_000_000 (10 gwei in wei).
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
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
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
                ).modify(
                    modify_balance(charlie, block_access_index=1, balance=999)
                ),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
def test_bal_invalid_missing_coinbase(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that clients reject blocks where BAL is missing the
    coinbase/fee recipient account.

    Alice sends 100 wei to Bob with gas_price > base_fee so the
    coinbase (charlie) receives a non-zero tip. BAL is corrupted
    by removing charlie's entry entirely.
    """
    alice = pre.fund_eoa(amount=10**18)
    bob = pre.fund_eoa(amount=0)
    charlie = pre.fund_eoa(amount=0)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=b"",
        contract_creation=False,
        access_list=[],
    )
    gas_price = 0xA

    tx = Transaction(
        sender=alice,
        to=bob,
        value=100,
        gas_limit=intrinsic_gas + 1000,
        gas_price=gas_price,
    )

    genesis_env = Environment(base_fee_per_gas=0x7)
    base_fee_per_gas = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=int(genesis_env.base_fee_per_gas or 0),
        parent_gas_used=0,
        parent_gas_limit=genesis_env.gas_limit,
    )
    tip = (gas_price - base_fee_per_gas) * intrinsic_gas

    blockchain_test(
        pre=pre,
        post={},
        genesis_environment=genesis_env,
        blocks=[
            Block(
                txs=[tx],
                fee_recipient=charlie,
                header_verify=Header(base_fee_per_gas=base_fee_per_gas),
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
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
                                    block_access_index=1, post_balance=100
                                )
                            ],
                        ),
                        charlie: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1, post_balance=tip
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
def test_bal_invalid_coinbase_balance_value(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that clients reject blocks where BAL contains an incorrect
    balance value for the coinbase/fee recipient.

    Same setup as test_bal_invalid_missing_coinbase but the coinbase
    entry is present with a wrong balance (999 instead of the
    actual tip).
    """
    alice = pre.fund_eoa(amount=10**18)
    bob = pre.fund_eoa(amount=0)
    charlie = pre.fund_eoa(amount=0)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=b"",
        contract_creation=False,
        access_list=[],
    )
    gas_price = 0xA

    tx = Transaction(
        sender=alice,
        to=bob,
        value=100,
        gas_limit=intrinsic_gas + 1000,
        gas_price=gas_price,
    )

    genesis_env = Environment(base_fee_per_gas=0x7)
    base_fee_per_gas = fork.base_fee_per_gas_calculator()(
        parent_base_fee_per_gas=int(genesis_env.base_fee_per_gas or 0),
        parent_gas_used=0,
        parent_gas_limit=genesis_env.gas_limit,
    )
    tip = (gas_price - base_fee_per_gas) * intrinsic_gas

    blockchain_test(
        pre=pre,
        post={},
        genesis_environment=genesis_env,
        blocks=[
            Block(
                txs=[tx],
                fee_recipient=charlie,
                header_verify=Header(base_fee_per_gas=base_fee_per_gas),
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
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
                                    block_access_index=1, post_balance=100
                                )
                            ],
                        ),
                        charlie: BalAccountExpectation(
                            balance_changes=[
                                BalBalanceChange(
                                    block_access_index=1, post_balance=tip
                                )
                            ],
                        ),
                    }
                ).modify(
                    modify_balance(charlie, block_access_index=1, balance=999)
                ),
            )
        ],
    )


@pytest.mark.valid_from("Amsterdam")
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "has_withdrawal",
    [
        pytest.param(False, id="empty_block"),
        pytest.param(True, id="withdrawal_only"),
    ],
)
def test_bal_invalid_extraneous_coinbase(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    has_withdrawal: bool,
) -> None:
    """
    Test that clients reject blocks where BAL contains a spurious
    coinbase entry when the coinbase received no fees.

    Coinbase is only included in BAL when it receives transaction tips.
    In blocks with no transactions, the coinbase receives nothing —
    even if withdrawals modify other accounts' balances.

    - empty_block: No txs, no withdrawals. Only system contracts.
    - withdrawal_only: No txs, one withdrawal to a different address.
      Withdrawals don't pay fees, so coinbase is still untouched.
    """
    coinbase = pre.fund_eoa(amount=0)

    withdrawals = None
    post: dict = {}
    if has_withdrawal:
        recipient = pre.fund_eoa(amount=0)
        withdrawals = [
            Withdrawal(
                index=0,
                validator_index=0,
                address=recipient,
                amount=10,
            )
        ]
        post[recipient] = None

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[
            Block(
                txs=[],
                fee_recipient=coinbase,
                withdrawals=withdrawals,
                exception=BlockException.INVALID_BLOCK_ACCESS_LIST,
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={coinbase: None}
                ).modify(
                    append_account(BalAccountChange(address=coinbase)),
                    sort_accounts_by_address(),
                ),
            )
        ],
    )
