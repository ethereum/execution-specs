"""
Test suite for `ethereum_test.helpers` module.
"""

from ..common import to_address


def test_to_address():
    """
    Test `ethereum_test.helpers.to_address`.
    """
    assert to_address("0x0") == "0x0000000000000000000000000000000000000000"
    assert to_address(0) == "0x0000000000000000000000000000000000000000"
    assert to_address(1) == "0x0000000000000000000000000000000000000001"
    assert to_address("10") == "0x000000000000000000000000000000000000000a"
    assert to_address("0x10") == "0x0000000000000000000000000000000000000010"
    assert (
        to_address(2 ** (20 * 8) - 1)
        == "0xffffffffffffffffffffffffffffffffffffffff"
    )
