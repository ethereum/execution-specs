"""
Invalid block access list tests for the fork block of
[EIP-8253: Bump nonce of zero-nonce storage accounts](https://eips.ethereum.org/EIPS/eip-8253).

Each test corrupts the fork block's BAL around the nonce change of a
targeted account and expects the block to be rejected.
"""

from typing import Callable

import pytest
from execution_testing import (
    Address,
    Alloc,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    Block,
    BlockAccessList,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    BlockException,
    Transaction,
    Withdrawal,
)
from execution_testing.test_types.block_access_list.modifiers import (
    append_change,
    append_storage,
    duplicate_nonce_change,
    encode_scalar_non_minimally,
    modify_nonce,
    override_rlp,
    remove_accounts,
    remove_balances,
    remove_nonces,
)

from .helpers import (
    BALANCE_BASE,
    BUMP_EXPECTATION,
    FORK_TIMESTAMP,
    bump_expectation,
    place_targeted_account,
)
from .spec import Spec, ref_spec_8253

REFERENCE_SPEC_GIT_PATH = ref_spec_8253.git_path
REFERENCE_SPEC_VERSION = ref_spec_8253.version

pytestmark = [
    pytest.mark.valid_at_transition_to("Amsterdam"),
    pytest.mark.pre_alloc_mutable,
    pytest.mark.exception_test,
]

TARGET = Spec.TARGETED_ACCOUNTS[0]
GWEI = 10**9

BalModifier = Callable[[BlockAccessList], BlockAccessList]


def split_bump_from_transaction_changes(address: Address) -> BalModifier:
    """
    Split an account's entry in two: one holding the nonce change from the
    fork transition, one holding everything the transactions did.
    """

    def transform(bal: BlockAccessList) -> BlockAccessList:
        new_root = []
        for account_change in bal.root:
            if account_change.address != address:
                new_root.append(account_change)
                continue
            from_fork = account_change.model_copy(deep=True)
            from_fork.balance_changes = []
            from_transactions = account_change.model_copy(deep=True)
            from_transactions.nonce_changes = []
            new_root.extend([from_fork, from_transactions])
        return BlockAccessList(root=new_root)

    return transform


def move_out_of_order(address: Address) -> BalModifier:
    """Move an account's entry to the opposite end of the BAL."""

    def transform(bal: BlockAccessList) -> BlockAccessList:
        new_root = list(bal.root)
        position = next(
            index
            for index, account_change in enumerate(new_root)
            if account_change.address == address
        )
        entry = new_root.pop(position)
        if position == 0:
            new_root.append(entry)
        else:
            new_root.insert(0, entry)
        return BlockAccessList(root=new_root)

    return transform


def fork_block_with_invalid_bal(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    address: Address,
    expectation: BlockAccessListExpectation,
    exception: BlockException = BlockException.INVALID_BLOCK_ACCESS_LIST,
    value: int = 0,
    withdrawal: int = 0,
) -> None:
    """
    Fill a fork block with the corrupted BAL `expectation`. The block holds
    one transaction, sending `value` to the targeted `address` if non-zero
    and otherwise leaving the target alone, plus a withdrawal of
    `withdrawal` gwei to the target if non-zero. The block is rejected, so
    the pre-state stands.
    """
    sender = pre.fund_eoa()
    receiver = pre.fund_eoa(amount=0)
    tx = (
        Transaction(sender=sender, to=address, value=value)
        if value
        else Transaction(sender=sender, to=receiver, value=1)
    )
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                timestamp=FORK_TIMESTAMP,
                txs=[tx],
                withdrawals=[
                    Withdrawal(
                        index=0,
                        validator_index=0,
                        address=address,
                        amount=withdrawal,
                    )
                ]
                if withdrawal
                else None,
                exception=exception,
                expected_block_access_list=expectation,
            )
        ],
        post=pre,
    )


def bumped_with_transfer(value: int) -> BlockAccessListExpectation:
    """Return the valid fork block BAL of a target that received `value`."""
    return BlockAccessListExpectation(
        account_expectations={
            Address(TARGET.address): bump_expectation(
                [
                    BalBalanceChange(
                        block_access_index=1, post_balance=BALANCE_BASE + value
                    )
                ]
            )
        }
    )


def test_bal_invalid_missing_bumped_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """Reject a fork block BAL that omits an untouched targeted account."""
    address = place_targeted_account(pre, TARGET)
    fork_block_with_invalid_bal(
        blockchain_test,
        pre,
        address,
        BlockAccessListExpectation(
            account_expectations={address: BUMP_EXPECTATION}
        ).modify(remove_accounts(address)),
    )


def test_bal_invalid_missing_bump_on_touched_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a fork block BAL that keeps the balance change of a targeted
    account but drops its nonce change, so the account itself is present.
    """
    address = place_targeted_account(pre, TARGET)
    value = 5
    fork_block_with_invalid_bal(
        blockchain_test,
        pre,
        address,
        bumped_with_transfer(value).modify(remove_nonces(address)),
        value=value,
    )


@pytest.mark.parametrize("post_nonce", [0, 2])
def test_bal_invalid_bump_nonce_value(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    post_nonce: int,
) -> None:
    """Reject a fork block BAL whose nonce change does not end at one."""
    address = place_targeted_account(pre, TARGET)
    fork_block_with_invalid_bal(
        blockchain_test,
        pre,
        address,
        BlockAccessListExpectation(
            account_expectations={address: BUMP_EXPECTATION}
        ).modify(
            modify_nonce(address, block_access_index=0, nonce=post_nonce)
        ),
    )


@pytest.mark.parametrize(
    "block_access_index",
    [
        pytest.param(1, id="transaction_index"),
        pytest.param(2, id="post_transaction_index"),
    ],
)
def test_bal_invalid_bump_index(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    block_access_index: int,
) -> None:
    """
    Reject a fork block BAL that records the nonce change at a transaction
    or post-transaction index instead of index zero.
    """
    address = place_targeted_account(pre, TARGET)
    fork_block_with_invalid_bal(
        blockchain_test,
        pre,
        address,
        BlockAccessListExpectation(
            account_expectations={address: BUMP_EXPECTATION}
        ).modify(
            remove_nonces(address),
            append_change(
                address,
                BalNonceChange(
                    block_access_index=block_access_index, post_nonce=1
                ),
            ),
        ),
    )


def test_bal_invalid_duplicate_bump(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """Reject a fork block BAL that lists the nonce change twice."""
    address = place_targeted_account(pre, TARGET)
    fork_block_with_invalid_bal(
        blockchain_test,
        pre,
        address,
        BlockAccessListExpectation(
            account_expectations={address: BUMP_EXPECTATION}
        ).modify(duplicate_nonce_change(address, block_access_index=0)),
    )


def test_bal_invalid_split_target_account(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a fork block BAL that keeps the fork transition and the
    transaction changes of a targeted account in two separate entries.
    """
    address = place_targeted_account(pre, TARGET)
    value = 5
    fork_block_with_invalid_bal(
        blockchain_test,
        pre,
        address,
        bumped_with_transfer(value).modify(
            split_bump_from_transaction_changes(address)
        ),
        exception=BlockException.INCORRECT_BLOCK_FORMAT,
        value=value,
    )


@pytest.mark.parametrize(
    "spurious",
    [
        pytest.param(
            lambda address: append_change(
                address,
                BalBalanceChange(
                    block_access_index=0, post_balance=BALANCE_BASE
                ),
            ),
            id="balance",
        ),
        pytest.param(
            lambda address: append_change(
                address,
                BalCodeChange(block_access_index=0, new_code=b""),
            ),
            id="code",
        ),
        pytest.param(
            lambda address: append_storage(
                address,
                slot=TARGET.storage_keys[0],
                change=BalStorageChange(block_access_index=0, post_value=1),
            ),
            id="storage_write",
        ),
        pytest.param(
            lambda address: append_storage(
                address, slot=TARGET.storage_keys[0], read=True
            ),
            id="storage_read",
        ),
    ],
)
def test_bal_invalid_spurious_bump_field(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    spurious: Callable[[Address], BalModifier],
) -> None:
    """
    Reject a fork block BAL that records anything but the nonce change for
    an untouched targeted account at index zero, even when the recorded
    value matches the account's actual state.
    """
    address = place_targeted_account(pre, TARGET)
    fork_block_with_invalid_bal(
        blockchain_test,
        pre,
        address,
        BlockAccessListExpectation(
            account_expectations={address: BUMP_EXPECTATION}
        ).modify(spurious(address)),
    )


@pytest.mark.parametrize("source", ["transaction", "withdrawal"])
def test_bal_invalid_missing_later_target_change(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    source: str,
) -> None:
    """
    Reject a fork block BAL with a correct nonce change but without the
    balance change a transaction or withdrawal made to the same account.
    """
    address = place_targeted_account(pre, TARGET)
    if source == "transaction":
        value, withdrawal = 5, 0
        balance = BALANCE_BASE + value
        block_access_index = 1
    elif source == "withdrawal":
        value, withdrawal = 0, 10
        balance = BALANCE_BASE + withdrawal * GWEI
        block_access_index = 2
    else:
        raise ValueError(f"Unhandled source: {source}")

    fork_block_with_invalid_bal(
        blockchain_test,
        pre,
        address,
        BlockAccessListExpectation(
            account_expectations={
                address: bump_expectation(
                    [
                        BalBalanceChange(
                            block_access_index=block_access_index,
                            post_balance=balance,
                        )
                    ]
                )
            }
        ).modify(remove_balances(address)),
        value=value,
        withdrawal=withdrawal,
    )


def test_bal_invalid_target_ordering(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Reject a fork block BAL that places a targeted account out of address
    order: fork transition entries sort with every other account.
    """
    address = place_targeted_account(pre, TARGET)
    fork_block_with_invalid_bal(
        blockchain_test,
        pre,
        address,
        BlockAccessListExpectation(
            account_expectations={address: BUMP_EXPECTATION}
        ).modify(move_out_of_order(address)),
        exception=BlockException.INCORRECT_BLOCK_FORMAT,
    )


@pytest.mark.blockchain_test_engine_only
@pytest.mark.parametrize("header_commits_to", ["canonical_rlp", "payload_rlp"])
def test_bal_invalid_bump_index_zero_encoding(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    header_commits_to: str,
) -> None:
    """
    Reject a `newPayload` whose BAL encodes the nonce change's block access
    index zero as a zero byte instead of the empty string.
    """
    address = place_targeted_account(pre, TARGET)
    encoder = encode_scalar_non_minimally(address, "nonce_block_access_index")
    expectation = BlockAccessListExpectation(
        account_expectations={address: BUMP_EXPECTATION}
    )
    if header_commits_to == "canonical_rlp":
        expectation = expectation.modify_rlp(encoder)
    elif header_commits_to == "payload_rlp":
        expectation = expectation.modify(override_rlp(encoder))
    else:
        raise ValueError(f"Unhandled header commitment: {header_commits_to}")

    fork_block_with_invalid_bal(blockchain_test, pre, address, expectation)
