"""
Test fork utilities.
"""

from typing import cast

from ..base_fork import Fork
from ..forks.forks import Berlin, Cancun, Frontier, London, Merge, Shanghai
from ..forks.transition import BerlinToLondonAt5, MergeToShanghaiAtTime15k
from ..helpers import (
    forks_from,
    forks_from_until,
    get_deployed_forks,
    get_development_forks,
    get_forks,
    is_fork,
    transition_fork_from_to,
    transition_fork_to,
)

FIRST_DEPLOYED = Frontier
LAST_DEPLOYED = Shanghai
LAST_DEVELOPMENT = Cancun
DEVELOPMENT_FORKS = [Cancun]


def test_transition_forks():
    """
    Test transition fork utilities.
    """
    assert transition_fork_from_to(Berlin, London) == BerlinToLondonAt5
    assert transition_fork_from_to(Berlin, Merge) is None
    assert transition_fork_to(Shanghai) == [MergeToShanghaiAtTime15k]

    # Test forks transitioned to and from
    assert BerlinToLondonAt5.transitions_to() == London
    assert BerlinToLondonAt5.transitions_from() == Berlin


def test_forks_from():  # noqa: D103
    assert forks_from(Merge) == [Merge, LAST_DEPLOYED]
    assert forks_from(Merge, deployed_only=True) == [Merge, LAST_DEPLOYED]
    assert (
        forks_from(Merge, deployed_only=False)
        == [Merge, LAST_DEPLOYED] + DEVELOPMENT_FORKS
    )


def test_forks():
    """
    Test fork utilities.
    """
    assert forks_from_until(Berlin, Berlin) == [Berlin]
    assert forks_from_until(Berlin, London) == [Berlin, London]
    assert forks_from_until(Berlin, Merge) == [
        Berlin,
        London,
        Merge,
    ]

    # Test fork names
    assert London.name() == "London"
    assert MergeToShanghaiAtTime15k.name() == "MergeToShanghaiAtTime15k"
    assert f"{London}" == "London"
    assert f"{MergeToShanghaiAtTime15k}" == "MergeToShanghaiAtTime15k"

    # Test some fork properties
    assert Berlin.header_base_fee_required(0, 0) is False
    assert London.header_base_fee_required(0, 0) is True
    assert Merge.header_base_fee_required(0, 0) is True

    # Transition forks too
    assert (
        cast(Fork, BerlinToLondonAt5).header_base_fee_required(4, 0) is False
    )
    assert cast(Fork, BerlinToLondonAt5).header_base_fee_required(5, 0) is True
    assert (
        cast(Fork, MergeToShanghaiAtTime15k).header_withdrawals_required(
            0, 14_999
        )
        is False
    )
    assert (
        cast(Fork, MergeToShanghaiAtTime15k).header_withdrawals_required(
            0, 15_000
        )
        is True
    )

    assert is_fork(Berlin, Berlin) is True
    assert is_fork(London, Berlin) is True
    assert is_fork(Berlin, Merge) is False


def test_get_forks():  # noqa: D103
    all_forks = get_forks()
    assert all_forks[0] == FIRST_DEPLOYED
    assert all_forks[-1] == LAST_DEVELOPMENT


def test_development_forks():  # noqa: D103
    assert get_development_forks() == DEVELOPMENT_FORKS


def test_deployed_forks():  # noqa: D103
    deployed_forks = get_deployed_forks()
    assert deployed_forks[0] == FIRST_DEPLOYED
    assert deployed_forks[-1] == LAST_DEPLOYED
