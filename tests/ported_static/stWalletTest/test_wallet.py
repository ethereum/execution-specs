"""
Call the `Wallet` contract: pending confirmations, execution and kill.

Ported from:
state_tests/stWalletTest/walletAddOwnerRemovePendingTransactionFiller.json
state_tests/stWalletTest/walletChangeOwnerRemovePendingTransactionFiller.json
state_tests/stWalletTest/walletChangeRequirementRemovePendingTransactionFiller.json
state_tests/stWalletTest/walletConfirmFiller.json
state_tests/stWalletTest/walletDefaultFiller.json
state_tests/stWalletTest/walletDefaultWithOutValueFiller.json
state_tests/stWalletTest/walletExecuteOverDailyLimitMultiOwnerFiller.json
state_tests/stWalletTest/walletExecuteOverDailyLimitOnlyOneOwnerFiller.json
state_tests/stWalletTest/walletExecuteOverDailyLimitOnlyOneOwnerNewFiller.json
state_tests/stWalletTest/walletExecuteUnderDailyLimitFiller.json
state_tests/stWalletTest/walletKillFiller.json
state_tests/stWalletTest/walletKillNotByOwnerFiller.json
state_tests/stWalletTest/walletKillToWalletFiller.json
state_tests/stWalletTest/walletRemoveOwnerRemovePendingTransactionFiller.json
"""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
)

from tests.ported_static.stWalletTest.wallet_contracts import (
    DAILY_LIMIT_SLOT,
    LAST_DAY_SLOT,
    PENDING_INDEX_SLOT,
    PENDING_MAP,
    SPENT_TODAY_SLOT,
    TRANSACTIONS_MAP,
    WALLET_CODE,
    mapping_slot,
    owners_storage,
    pending_index_element_slot,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

ADD_OWNER = Bytes("7065cb48")
CHANGE_OWNER = Bytes("f00d4b5d")
CHANGE_REQUIREMENT = Bytes("ba51a6df")
CONFIRM = Bytes("797af627")
EXECUTE = Bytes("b61d27f6")
KILL = Bytes("cbf0b0c0")
REMOVE_OWNER = Bytes("173825d9")

WALLET_BALANCE = 100
LAST_DAY = 0xC22E4
PENDING_OPERATION = Hash(
    0x6877E4536B661640954061CDBC3A9761FB5245C340FCB1721307CD9D5F285C96
)
TRANSFER_VALUE = 9


def word(value: int | Address) -> Hash:
    """Return `value` as an ABI-encoded word."""
    return Hash(value, left_padding=True)


def pending_storage(
    operation: Hash, owner_index: int, to: Address, value: int
) -> dict:
    """Return the storage of an operation confirmed by one owner."""
    pending = mapping_slot(operation, PENDING_MAP)
    transaction = mapping_slot(operation, TRANSACTIONS_MAP)
    return {
        PENDING_INDEX_SLOT: 1,
        pending_index_element_slot(0): operation,
        pending: 1,
        pending + 1: 2**owner_index,
        transaction: to,
        transaction + 1: value,
    }


def queued_transaction(operation: Hash, to: Address, value: int) -> dict:
    """Return the storage of a queued transaction with no pending entry."""
    transaction = mapping_slot(operation, TRANSACTIONS_MAP)
    return {PENDING_INDEX_SLOT: 1, transaction: to, transaction + 1: value}


@pytest.mark.ported_from(
    [
        "state_tests/stWalletTest/walletAddOwnerRemovePendingTransactionFiller.json",  # noqa: E501
        "state_tests/stWalletTest/walletChangeOwnerRemovePendingTransactionFiller.json",  # noqa: E501
        "state_tests/stWalletTest/walletChangeRequirementRemovePendingTransactionFiller.json",  # noqa: E501
        "state_tests/stWalletTest/walletConfirmFiller.json",
        "state_tests/stWalletTest/walletDefaultFiller.json",
        "state_tests/stWalletTest/walletDefaultWithOutValueFiller.json",
        "state_tests/stWalletTest/walletExecuteOverDailyLimitMultiOwnerFiller.json",  # noqa: E501
        "state_tests/stWalletTest/walletExecuteOverDailyLimitOnlyOneOwnerFiller.json",  # noqa: E501
        "state_tests/stWalletTest/walletExecuteOverDailyLimitOnlyOneOwnerNewFiller.json",  # noqa: E501
        "state_tests/stWalletTest/walletExecuteUnderDailyLimitFiller.json",
        "state_tests/stWalletTest/walletKillFiller.json",
        "state_tests/stWalletTest/walletKillNotByOwnerFiller.json",
        "state_tests/stWalletTest/walletKillToWalletFiller.json",
        "state_tests/stWalletTest/walletRemoveOwnerRemovePendingTransactionFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.execute(
    pytest.mark.skip(
        reason="Expects the block number and timestamp of the test env"
    )
)
@pytest.mark.parametrize(
    "scenario",
    [
        "add_owner_remove_pending_transaction",
        "change_owner_remove_pending_transaction",
        "change_requirement_remove_pending_transaction",
        "confirm",
        "remove_owner_remove_pending_transaction",
        "default",
        "default_with_out_value",
        "execute_over_daily_limit_multi_owner",
        "execute_over_daily_limit_only_one_owner",
        "execute_over_daily_limit_only_one_owner_new",
        "execute_under_daily_limit",
        "kill",
        "kill_not_by_owner",
        "kill_to_wallet",
    ],
)
def test_wallet(
    state_test: StateTestFiller,
    pre: Alloc,
    scenario: str,
) -> None:
    """Call one `Wallet` function from the sender."""
    sender = pre.fund_eoa()
    other_owner = pre.nonexistent_account()
    new_owner = pre.nonexistent_account()
    recipient = pre.nonexistent_account()

    execute = EXECUTE + word(recipient) + word(TRANSFER_VALUE) + word(0x60)
    execute_operation = Bytes(execute + word(1)).keccak256()
    single_owner = owners_storage(1, [sender])
    pending = (
        owners_storage(1, [other_owner, sender])
        | {LAST_DAY_SLOT: LAST_DAY}
        | pending_storage(PENDING_OPERATION, 1, recipient, TRANSFER_VALUE)
    )

    data = b""
    value = 0
    transferred = 0
    wallet_balance_change = 0
    post: Dict[Address, Account | None] = {}

    if scenario == "add_owner_remove_pending_transaction":
        storage = pending
        data = ADD_OWNER + word(new_owner)
        post_storage = owners_storage(1, [other_owner, sender, new_owner]) | {
            LAST_DAY_SLOT: LAST_DAY
        }
    elif scenario == "change_owner_remove_pending_transaction":
        storage = pending
        data = CHANGE_OWNER + word(other_owner) + word(new_owner)
        post_storage = owners_storage(1, [new_owner, sender]) | {
            LAST_DAY_SLOT: LAST_DAY
        }
    elif scenario == "change_requirement_remove_pending_transaction":
        storage = pending
        data = CHANGE_REQUIREMENT + word(2)
        post_storage = owners_storage(2, [other_owner, sender]) | {
            LAST_DAY_SLOT: LAST_DAY
        }
    elif scenario == "confirm":
        storage = pending | {0: 2}
        data = CONFIRM + PENDING_OPERATION
        post_storage = owners_storage(2, [other_owner, sender]) | {
            LAST_DAY_SLOT: LAST_DAY,
            PENDING_INDEX_SLOT: 1,
        }
        transferred = TRANSFER_VALUE
    elif scenario == "remove_owner_remove_pending_transaction":
        storage = pending
        data = REMOVE_OWNER + word(other_owner)
        post_storage = owners_storage(1, [sender]) | {LAST_DAY_SLOT: LAST_DAY}
    elif scenario in ("default", "default_with_out_value"):
        storage = single_owner
        post_storage = storage
        if scenario == "default":
            value = WALLET_BALANCE
            wallet_balance_change = value
    elif scenario == "execute_over_daily_limit_multi_owner":
        storage = owners_storage(2, [sender, other_owner])
        data = execute
        post_storage = storage | pending_storage(
            execute_operation, 1, recipient, TRANSFER_VALUE
        )
    elif scenario == "execute_over_daily_limit_only_one_owner":
        storage = single_owner | {DAILY_LIMIT_SLOT: 4}
        data = execute
        post_storage = storage | queued_transaction(
            execute_operation, recipient, TRANSFER_VALUE
        )
    elif scenario == "execute_over_daily_limit_only_one_owner_new":
        storage = single_owner | {SPENT_TODAY_SLOT: 4, LAST_DAY_SLOT: LAST_DAY}
        data = execute
        post_storage = storage | queued_transaction(
            execute_operation, recipient, TRANSFER_VALUE
        )
    elif scenario == "execute_under_daily_limit":
        storage = single_owner | {
            DAILY_LIMIT_SLOT: 255,
            LAST_DAY_SLOT: LAST_DAY,
        }
        data = execute
        post_storage = storage | {SPENT_TODAY_SLOT: TRANSFER_VALUE}
        transferred = TRANSFER_VALUE
    elif scenario == "kill":
        storage = single_owner
        data = KILL + word(sender)
        post_storage = storage | {PENDING_INDEX_SLOT: 1}
        wallet_balance_change = -WALLET_BALANCE
    elif scenario == "kill_not_by_owner":
        storage = owners_storage(1, [other_owner])
        data = KILL + word(recipient)
        post_storage = storage
        value = WALLET_BALANCE
        wallet_balance_change = value
    elif scenario == "kill_to_wallet":
        storage = single_owner
        post_storage = storage | {PENDING_INDEX_SLOT: 1}
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    wallet = pre.deploy_contract(
        code=WALLET_CODE, storage=storage, balance=WALLET_BALANCE
    )
    if scenario == "kill_to_wallet":
        data = KILL + word(wallet)

    if transferred:
        post[recipient] = Account(balance=transferred)
        wallet_balance_change = -transferred
    else:
        post[recipient] = Account.NONEXISTENT
    post[wallet] = Account(
        storage=post_storage, balance_change=wallet_balance_change
    )

    tx = Transaction(sender=sender, to=wallet, data=data, value=value)
    state_test(pre=pre, post=post, tx=tx)
