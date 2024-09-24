"""
Test suite for `ethereum_test` module base types.
"""

from typing import Any

import pytest

from ..base_types import Address, Hash, Wei


@pytest.mark.parametrize(
    "a, b, equal",
    [
        (Address("0x0"), Address("0x0"), True),
        (Address("0x0"), Address("0x1"), False),
        (Address("0x1"), Address("0x0"), False),
        (Address("0x1"), "0x1", True),
        (Address("0x1"), "0x2", False),
        (Address("0x1"), 1, True),
        (Address("0x1"), 2, False),
        (Address("0x1"), b"\x01", True),
        (Address("0x1"), b"\x02", False),
        ("0x1", Address("0x1"), True),
        ("0x2", Address("0x1"), False),
        (1, Address("0x1"), True),
        (2, Address("0x1"), False),
        (b"\x01", Address("0x1"), True),
        (b"\x02", Address("0x1"), False),
        (Hash("0x0"), Hash("0x0"), True),
        (Hash("0x0"), Hash("0x1"), False),
        (Hash("0x1"), Hash("0x0"), False),
        (Hash("0x1"), "0x1", True),
        (Hash("0x1"), "0x2", False),
        (Hash("0x1"), 1, True),
        (Hash("0x1"), 2, False),
        (Hash("0x1"), b"\x01", True),
        (Hash("0x1"), b"\x02", False),
        ("0x1", Hash("0x1"), True),
        ("0x2", Hash("0x1"), False),
        (1, Hash("0x1"), True),
        (2, Hash("0x1"), False),
    ],
)
def test_comparisons(a: Any, b: Any, equal: bool):
    """
    Test the comparison methods of the base types.
    """
    if equal:
        assert a == b
        assert not a != b
    else:
        assert a != b
        assert not a == b


@pytest.mark.parametrize(
    "s, expected",
    [
        ("0", 0),
        ("10**18", 10**18),
        ("1e18", 10**18),
        ("1 ether", 10**18),
        ("2 ether", 2 * 10**18),
        ("2.1 ether", 2.1 * 10**18),
        ("2.1 Ether", 2.1 * 10**18),
        ("2.1 ETHER", 2.1 * 10**18),
        ("1 wei", 1),
        ("10**9 wei", 10**9),
        ("1 gwei", 10**9),
        ("1 szabo", 10**12),
        ("1 finney", 10**15),
        ("1 kwei", 10**3),
        ("1 mwei", 10**6),
        ("1 babbage", 10**3),
        ("1 femtoether", 10**3),
        ("1 Lovelace", 10**6),
        ("1 Picoether", 10**6),
        ("1 gwei", 10**9),
        ("1 shannon", 10**9),
        ("1 nanoether", 10**9),
        ("1 nano", 10**9),
        ("1 microether", 10**12),
        ("1 micro", 10**12),
        ("1 milliether", 10**15),
        ("1 milli", 10**15),
    ],
)
def test_wei_parsing(s: str, expected: int):
    """
    Test the parsing of wei values.
    """
    assert Wei(s) == expected
