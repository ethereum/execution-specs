"""
Test fork utilities.
"""

from ethereum_test_forks import (
    Berlin,
    London,
    Merge,
    Shanghai,
    forks_from,
    forks_from_until,
    is_fork,
)


def test_forks():
    assert forks_from_until(Berlin, Berlin) == [Berlin]
    assert forks_from_until(Berlin, London) == [Berlin, London]
    assert forks_from_until(Berlin, Merge) == [
        Berlin,
        London,
        Merge,
    ]
    assert forks_from(Merge) == [Merge, Shanghai]

    assert London.__name__ == "London"
    assert Berlin.header_base_fee_required(0, 0) is False
    assert London.header_base_fee_required(0, 0) is True
    assert Merge.header_base_fee_required(0, 0) is True

    assert is_fork(Berlin, Berlin) is True
    assert is_fork(London, Berlin) is True
    assert is_fork(Berlin, Merge) is False
