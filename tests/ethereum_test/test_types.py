"""
Test suite for `ethereum_test` module.
"""

from ethereum_test import Storage


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
