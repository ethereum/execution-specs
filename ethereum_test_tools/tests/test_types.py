"""
Test suite for `ethereum_test` module.
"""

from typing import Any, Dict, List

import pytest

from ..common import Account, Storage, even_padding
from ..common.conversions import key_value_padding


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

    s = Storage({-1: -1, -2: -2})
    assert s.data[-1] == -1
    assert s.data[-2] == -2
    d = s.to_dict()
    assert (
        d["0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"]
        == "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
    )
    assert (
        d["0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe"]
        == "0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe"
    )
    # Try to add a duplicate key (negative and positive number at the same
    # time)
    # same value, ok
    s[2**256 - 1] = 2**256 - 1
    s.to_dict()
    # different value, not ok
    s[2**256 - 1] = 0
    with pytest.raises(Storage.AmbiguousKeyValue):
        s.to_dict()

    # Check store counter
    s = Storage({})
    s.store_next(0x100)
    s.store_next("0x200")
    s.store_next(b"\x03\x00".rjust(32, b"\x00"))
    d = s.to_dict()
    assert d == {
        "0x00": ("0x0100"),
        "0x01": ("0x0200"),
        "0x02": ("0x0300"),
    }


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
def test_account_check_alloc(account: Account, alloc: Dict[Any, Any], should_pass: bool):
    if should_pass:
        account.check_alloc("test", alloc)
    else:
        with pytest.raises(Exception) as _:
            account.check_alloc("test", alloc)


# Even Padding Test
@pytest.mark.parametrize(
    ["input", "excluded", "expected"],
    [
        (
            {"x": "0x12346", "y": "0xbcd", "z": {"a": "0x1"}},
            [None],
            {"x": "0x012346", "y": "0x0bcd", "z": {"a": "0x01"}},
        ),
        (
            {"a": "0x", "b": "0x", "c": None},
            [None],
            {"a": "0x", "b": "0x", "c": "0x"},
        ),
        (
            {"x": "0x12356", "y": "0xbed", "z": {"a": "0x1"}},
            ["y", "z"],
            {"x": "0x012356", "y": "0xbed", "z": {"a": "0x1"}},
        ),
    ],
)
def test_even_padding(input: Dict, excluded: List[str | None], expected: Dict):
    assert even_padding(input, excluded) == expected


# Key Value Padding Test
@pytest.mark.parametrize(
    ["value", "expected"],
    [
        (
            "0x0000000012346",
            "0x012346",
        ),
        (
            "0x",
            "0x00",
        ),
        (
            None,
            "0x",
        ),
    ],
)
def test_key_value_padding(value: str, expected: str):
    assert key_value_padding(value) == expected
