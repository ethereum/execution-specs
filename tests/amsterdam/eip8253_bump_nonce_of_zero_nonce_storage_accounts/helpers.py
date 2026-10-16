"""Shared helpers for the EIP-8253 tests."""

from typing import Dict, List

from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalNonceChange,
    Storage,
)

from .spec import Spec, TargetedAccount

FORK_TIMESTAMP = 15_000

BALANCE_BASE = 10**15
"""
Balance given to a targeted account in the pre-state. Distinct per account
where several are placed, so a balance that is zeroed or attributed to the
wrong account is caught.
"""


def bump_expectation(
    balance_changes: List[BalBalanceChange] | None = None,
) -> BalAccountExpectation:
    """
    Return the BAL entry of a targeted account in the fork block: the nonce
    change at block access index zero plus the given balance changes, with
    every other field asserted empty.
    """
    return BalAccountExpectation(
        nonce_changes=[BalNonceChange(block_access_index=0, post_nonce=1)],
        balance_changes=balance_changes or [],
        code_changes=[],
        storage_changes=[],
        storage_reads=[],
    )


BUMP_EXPECTATION = bump_expectation()
"""The only BAL entry an otherwise untouched targeted account gets."""


def targeted_storage(target: TargetedAccount) -> Storage:
    """Return a non-zero value in each Mainnet storage slot of `target`."""
    storage = Storage()
    for key in target.storage_keys:
        storage[key] = 1
    return storage


def place_targeted_account(
    pre: Alloc, target: TargetedAccount, balance: int = BALANCE_BASE
) -> Address:
    """
    Add `target` to the pre-state as it looks on Mainnet: empty code, zero
    nonce, non-empty storage.
    """
    address = Address(target.address)
    pre[address] = Account(
        nonce=0, balance=balance, code=b"", storage=targeted_storage(target)
    )
    return address


def bumped_account(
    target: TargetedAccount, balance: int = BALANCE_BASE
) -> Account:
    """Return `target` as it looks after the bump."""
    return Account(
        nonce=1, balance=balance, code=b"", storage=targeted_storage(target)
    )


def place_targeted_accounts(pre: Alloc) -> Dict[Address, Account]:
    """
    Add every targeted account to the pre-state and return the accounts
    expected after the bump.
    """
    post: Dict[Address, Account] = {}
    for index, target in enumerate(Spec.TARGETED_ACCOUNTS):
        balance = BALANCE_BASE + index
        address = place_targeted_account(pre, target, balance)
        post[address] = bumped_account(target, balance)
    return post
