"""
Test fork utilities.
"""

from typing import cast

from ..base_fork import Fork
from ..forks.forks import Berlin, London, Merge, Shanghai
from ..forks.transition import (
    BerlinToLondonAt5,
    MergeToShanghaiAtTime15k,
    ShanghaiToTestOnlyUpcomingFork,
)
from ..forks.upcoming import TestOnlyUpcomingFork
from ..helpers import (
    fork_only,
    forks_from,
    forks_from_until,
    is_fork,
    set_latest_fork_by_name,
    transition_fork_from_to,
    transition_fork_to,
)


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
    assert forks_from(Merge) == [Merge, Shanghai]

    # Test fork names
    assert London.name() == "London"
    assert TestOnlyUpcomingFork.name() == "TestOnlyUpcomingFork"
    assert MergeToShanghaiAtTime15k.name() == "MergeToShanghaiAtTime15k"
    assert f"{London}" == "London"
    assert f"{TestOnlyUpcomingFork}" == "TestOnlyUpcomingFork"
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

    assert fork_only(Berlin) == [Berlin]
    # This is an upcoming fork, so it should not be included in the list
    assert fork_only(TestOnlyUpcomingFork) == []
    assert forks_from(TestOnlyUpcomingFork) == []

    # Transition forks should be included in the list, only if they transition
    # to at least the latest fork
    assert fork_only(MergeToShanghaiAtTime15k) == [MergeToShanghaiAtTime15k]
    assert fork_only(ShanghaiToTestOnlyUpcomingFork) == []

    # Now try modifying the latest fork by name
    set_latest_fork_by_name("TestOnlyUpcomingFork")

    # Now the upcoming fork should be included in the list
    assert forks_from(Merge) == [Merge, Shanghai, TestOnlyUpcomingFork]
    assert fork_only(TestOnlyUpcomingFork) == [TestOnlyUpcomingFork]
    # Also all transition forks that transition to this new latest fork
    assert fork_only(ShanghaiToTestOnlyUpcomingFork) == [
        ShanghaiToTestOnlyUpcomingFork
    ]
