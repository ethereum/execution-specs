"""Test the EIP-8253 pre-state invariant check."""

import pytest

from execution_testing.base_types import Account, Address
from execution_testing.forks import Amsterdam, Osaka
from execution_testing.forks.forks.eips.amsterdam.eip_8253 import (
    ZERO_NONCE_STORAGE_ACCOUNTS,
)
from execution_testing.test_types import Alloc

from ..helpers import verify_zero_nonce_storage_accounts

TARGETED = ZERO_NONCE_STORAGE_ACCOUNTS[0]
OTHER = Address(0x1234)


@pytest.mark.parametrize(
    "account",
    [
        pytest.param(
            Account(nonce=0, balance=1, storage={0: 1}),
            id="mainnet_shape",
        ),
        pytest.param(Account(nonce=0, balance=1), id="no_storage"),
    ],
)
def test_targeted_account_allowed_before_bump(account: Account) -> None:
    """A targeted account with zero nonce and no code passes pre-bump."""
    verify_zero_nonce_storage_accounts(Alloc({TARGETED: account}), Osaka)


@pytest.mark.parametrize(
    "account",
    [
        pytest.param(Account(nonce=1, storage={0: 1}), id="nonzero_nonce"),
        pytest.param(Account(nonce=0, code=b"\x00"), id="with_code"),
    ],
)
def test_targeted_account_rejected_before_bump(account: Account) -> None:
    """
    A targeted account that does not look like Mainnet is rejected before
    the bump.
    """
    with pytest.raises(Exception, match="EIP-8253"):
        verify_zero_nonce_storage_accounts(Alloc({TARGETED: account}), Osaka)


def test_other_zero_nonce_storage_account_allowed_before_bump() -> None:
    """A non-targeted account of the same shape is fine before the bump."""
    verify_zero_nonce_storage_accounts(
        Alloc({OTHER: Account(nonce=0, storage={0: 1})}), Osaka
    )


@pytest.mark.parametrize(
    "address", [TARGETED, OTHER], ids=["targeted", "other"]
)
def test_zero_nonce_storage_account_rejected_after_bump(
    address: Address,
) -> None:
    """No account of the removed shape can exist after the bump."""
    with pytest.raises(Exception, match="EIP-8253"):
        verify_zero_nonce_storage_accounts(
            Alloc({address: Account(nonce=0, storage={0: 1})}), Amsterdam
        )


@pytest.mark.parametrize(
    "account",
    [
        pytest.param(Account(nonce=1, storage={0: 1}), id="bumped"),
        pytest.param(Account(nonce=0, storage={0: 0}), id="zero_storage"),
        pytest.param(
            Account(nonce=0, code=b"\x00", storage={0: 1}), id="code"
        ),
    ],
)
def test_accounts_allowed_after_bump(account: Account) -> None:
    """Accounts that do not match the removed shape pass after the bump."""
    verify_zero_nonce_storage_accounts(Alloc({TARGETED: account}), Amsterdam)
