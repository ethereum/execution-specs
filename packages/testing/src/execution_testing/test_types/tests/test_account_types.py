"""Test account test types."""

import pytest

from ..account_types import Account


@pytest.mark.parametrize(
    "account_1, account_2, equal",
    [
        (Account(), Account(), True),
        (Account(nonce=1), Account(nonce=2), False),
        (Account(nonce=1), Account(nonce=1), True),
        (Account(nonce=1), Account(nonce=1, code="0x1234"), False),
        (Account(nonce=1, code="0x1234"), Account(nonce=1), False),
        (
            Account(nonce=1, code="0x1234"),
            Account(nonce=1, code="0x1234"),
            True,
        ),
        (
            Account(nonce=1, code="0x1234"),
            Account(nonce=1, code="0x5678"),
            False,
        ),
        (
            Account(nonce=1, code="0x1234"),
            Account(nonce=2, code="0x5678"),
            False,
        ),
        (
            Account(nonce=1, code="0x1234"),
            Account(nonce=2, code="0x1234"),
            False,
        ),
        (
            Account(nonce=1, code="0x1234"),
            Account(nonce=1, code="0x1234", storage={0: 0, 1: 1}),
            False,
        ),
        (
            Account(nonce=1, code="0x1234", storage={1: 1, 0: 0}),
            Account(nonce=1, code="0x1234", storage={0: 0, 1: 1}),
            True,
        ),
    ],
)
def test_account_hash(
    account_1: Account, account_2: Account, equal: bool
) -> None:
    """Test two different accounts to return the same hash."""
    if equal:
        assert account_1.hash() == account_2.hash(), (
            f"Account 1: {account_1.hash()}, Account 2: {account_2.hash()}"
        )
    else:
        assert account_1.hash() != account_2.hash(), (
            f"Account 1: {account_1.hash()}, Account 2: {account_2.hash()}"
        )
