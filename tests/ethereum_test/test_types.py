"""
Test suite for `ethereum_test` module.
"""

from typing import Any, Dict

import pytest

from ethereum_test import Account, Storage


def test_storage():
    """
    Test `ethereum_test.types.storage` parsing.
    """
    s = Storage({"10": "0x10"})

    assert 10 in s.data
    assert s.data[10] == 16

    s = Storage({"10": "10"})

    assert 10 in s.data
    assert s.data[10] == 10

    s = Storage({10: 10})

    assert 10 in s.data
    assert s.data[10] == 10

    s["10"] = "0x10"
    s["0x10"] = "10"
    assert s.data[10] == 16
    assert s.data[16] == 10

    assert "10" in s
    assert "0xa" in s
    assert 10 in s

    del s[10]
    assert "10" not in s
    assert "0xa" not in s
    assert 10 not in s


@pytest.mark.parametrize(
    ["account", "alloc", "should_pass"],
    [
        # All None: Pass
        (
            Account(),
            {"nonce": "1", "code": "0x123", "balance": "1", "storage": {0: 1}},
            True,
        ),
        # Storage must be empty: Fail
        (
            Account(storage={}),
            {"nonce": "1", "code": "0x123", "balance": "1", "storage": {0: 1}},
            False,
        ),
        # Storage must be empty: Pass
        (
            Account(storage={}),
            {"nonce": "1", "code": "0x123", "balance": "1", "storage": {}},
            True,
        ),
        # Storage must be empty: Pass
        (
            Account(storage={}),
            {
                "nonce": "1",
                "code": "0x123",
                "balance": "1",
                "storage": {0: 0, 1: 0},
            },
            True,
        ),
        # Storage must be empty: Pass
        (
            Account(storage={0: 0}),
            {
                "nonce": "1",
                "code": "0x123",
                "balance": "1",
                "storage": {},
            },
            True,
        ),
        # Storage must not be empty: Pass
        (
            Account(storage={1: 1}),
            {
                "nonce": "1",
                "code": "0x123",
                "balance": "1",
                "storage": {0: 0, 1: 1},
            },
            True,
        ),
        # Storage must not be empty: Fail
        (
            Account(storage={1: 1}),
            {
                "nonce": "1",
                "code": "0x123",
                "balance": "1",
                "storage": {0: 0, 1: 1, 2: 2},
            },
            False,
        ),
        # Code must be empty: Fail
        (
            Account(code=""),
            {
                "nonce": "0",
                "code": "0x123",
                "balance": "0",
                "storage": {},
            },
            False,
        ),
        # Code must be empty: Pass
        (
            Account(code=""),
            {
                "nonce": "1",
                "code": "0x",
                "balance": "1",
                "storage": {0: 0, 1: 1},
            },
            True,
        ),
        # Nonce must be empty: Fail
        (
            Account(nonce=0),
            {
                "nonce": "1",
                "code": "0x",
                "balance": "0",
                "storage": {},
            },
            False,
        ),
        # Nonce must be empty: Pass
        (
            Account(nonce=0),
            {
                "nonce": "0",
                "code": "0x1234",
                "balance": "1",
                "storage": {0: 0, 1: 1},
            },
            True,
        ),
        # Nonce must not be empty: Fail
        (
            Account(nonce=1),
            {
                "code": "0x1234",
                "balance": "1",
                "storage": {0: 0, 1: 1},
            },
            False,
        ),
        # Nonce must not be empty: Pass
        (
            Account(nonce=1),
            {
                "nonce": "1",
                "code": "0x",
                "balance": "0",
                "storage": {},
            },
            True,
        ),
        # Balance must be empty: Fail
        (
            Account(balance=0),
            {
                "nonce": "0",
                "code": "0x",
                "balance": "1",
                "storage": {},
            },
            False,
        ),
        # Balance must be empty: Pass
        (
            Account(balance=0),
            {
                "nonce": "1",
                "code": "0x1234",
                "balance": "0",
                "storage": {0: 0, 1: 1},
            },
            True,
        ),
        # Balance must not be empty: Fail
        (
            Account(balance=1),
            {
                "nonce": "1",
                "code": "0x1234",
                "storage": {0: 0, 1: 1},
            },
            False,
        ),
        # Balance must not be empty: Pass
        (
            Account(balance=1),
            {
                "nonce": "0",
                "code": "0x",
                "balance": "1",
                "storage": {},
            },
            True,
        ),
    ],
)
def test_account_check_alloc(
    account: Account, alloc: Dict[Any, Any], should_pass: bool
):
    if should_pass:
        account.check_alloc("test", alloc)
    else:
        with pytest.raises(Exception) as _:
            account.check_alloc("test", alloc)
