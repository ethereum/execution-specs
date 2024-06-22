"""
Test suite for `ethereum_test` module base types.
"""

from typing import Any

import pytest

from ..base_types import Address, Hash


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
