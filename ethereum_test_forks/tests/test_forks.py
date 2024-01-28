"""
Test fork utilities.
"""

from typing import Mapping, cast

from ..base_fork import Fork
from ..forks.forks import Berlin, Cancun, Frontier, London, Paris, Shanghai
from ..forks.transition import BerlinToLondonAt5, ParisToShanghaiAtTime15k
from ..helpers import (
    forks_from,
    forks_from_until,
    get_deployed_forks,
    get_development_forks,
    get_forks,
    transition_fork_from_to,
    transition_fork_to,
)
from ..transition_base_fork import transition_fork

FIRST_DEPLOYED = Frontier
LAST_DEPLOYED = Shanghai
LAST_DEVELOPMENT = Cancun
DEVELOPMENT_FORKS = [Cancun]


def test_transition_forks():
    """
    Test transition fork utilities.
    """
    assert transition_fork_from_to(Berlin, London) == BerlinToLondonAt5
    assert transition_fork_from_to(Berlin, Paris) is None
    assert transition_fork_to(Shanghai) == [ParisToShanghaiAtTime15k]

    # Test forks transitioned to and from
    assert BerlinToLondonAt5.transitions_to() == London
    assert BerlinToLondonAt5.transitions_from() == Berlin

    assert BerlinToLondonAt5.transition_tool_name(4, 0) == "Berlin"
    assert BerlinToLondonAt5.transition_tool_name(5, 0) == "London"
    # Default values of transition forks is the transition block
    assert BerlinToLondonAt5.transition_tool_name() == "London"

    assert ParisToShanghaiAtTime15k.transition_tool_name(0, 14_999) == "Merge"
    assert ParisToShanghaiAtTime15k.transition_tool_name(0, 15_000) == "Shanghai"
    assert ParisToShanghaiAtTime15k.transition_tool_name() == "Shanghai"

    assert BerlinToLondonAt5.header_base_fee_required(4, 0) is False
    assert BerlinToLondonAt5.header_base_fee_required(5, 0) is True

    assert ParisToShanghaiAtTime15k.header_withdrawals_required(0, 14_999) is False
    assert ParisToShanghaiAtTime15k.header_withdrawals_required(0, 15_000) is True

    assert ParisToShanghaiAtTime15k.engine_new_payload_version(0, 14_999) == 1
    assert ParisToShanghaiAtTime15k.engine_new_payload_version(0, 15_000) == 2

    assert BerlinToLondonAt5.fork_at(4, 0) == Berlin
    assert BerlinToLondonAt5.fork_at(5, 0) == London
    assert ParisToShanghaiAtTime15k.fork_at(0, 14_999) == Paris
    assert ParisToShanghaiAtTime15k.fork_at(0, 15_000) == Shanghai
    assert ParisToShanghaiAtTime15k.fork_at() == Paris
    assert ParisToShanghaiAtTime15k.fork_at(10_000_000, 14_999) == Paris


def test_forks_from():  # noqa: D103
    assert forks_from(Paris) == [Paris, LAST_DEPLOYED]
    assert forks_from(Paris, deployed_only=True) == [Paris, LAST_DEPLOYED]
    assert forks_from(Paris, deployed_only=False) == [Paris, LAST_DEPLOYED] + DEVELOPMENT_FORKS


def test_forks():
    """
    Test fork utilities.
    """
    assert forks_from_until(Berlin, Berlin) == [Berlin]
    assert forks_from_until(Berlin, London) == [Berlin, London]
    assert forks_from_until(Berlin, Paris) == [
        Berlin,
        London,
        Paris,
    ]

    # Test fork names
    assert London.name() == "London"
    assert ParisToShanghaiAtTime15k.name() == "ParisToShanghaiAtTime15k"
    assert f"{London}" == "London"
    assert f"{ParisToShanghaiAtTime15k}" == "ParisToShanghaiAtTime15k"

    # Merge name will be changed to paris, but we need to check the inheriting fork name is still
    # the default
    assert Paris.transition_tool_name() == "Merge"
    assert Shanghai.transition_tool_name() == "Shanghai"
    assert Paris.blockchain_test_network_name() == "Merge"
    assert Shanghai.blockchain_test_network_name() == "Shanghai"
    assert ParisToShanghaiAtTime15k.blockchain_test_network_name() == "ParisToShanghaiAtTime15k"

    # Test some fork properties
    assert Berlin.header_base_fee_required(0, 0) is False
    assert London.header_base_fee_required(0, 0) is True
    assert Paris.header_base_fee_required(0, 0) is True
    # Default values of normal forks if the genesis block
    assert Paris.header_base_fee_required() is True

    # Transition forks too
    assert cast(Fork, BerlinToLondonAt5).header_base_fee_required(4, 0) is False
    assert cast(Fork, BerlinToLondonAt5).header_base_fee_required(5, 0) is True
    assert cast(Fork, ParisToShanghaiAtTime15k).header_withdrawals_required(0, 14_999) is False
    assert cast(Fork, ParisToShanghaiAtTime15k).header_withdrawals_required(0, 15_000) is True
    assert cast(Fork, ParisToShanghaiAtTime15k).header_withdrawals_required() is True

    # Test fork comparison
    assert Paris > Berlin
    assert not Berlin > Paris
    assert Berlin < Paris
    assert not Paris < Berlin

    assert Paris >= Berlin
    assert not Berlin >= Paris
    assert Berlin <= Paris
    assert not Paris <= Berlin

    assert London > Berlin
    assert not Berlin > London
    assert Berlin < London
    assert not London < Berlin

    assert London >= Berlin
    assert not Berlin >= London
    assert Berlin <= London
    assert not London <= Berlin

    assert Berlin >= Berlin
    assert Berlin <= Berlin
    assert not Berlin > Berlin
    assert not Berlin < Berlin

    fork = Berlin
    assert fork >= Berlin
    assert fork <= Berlin
    assert not fork > Berlin
    assert not fork < Berlin
    assert fork == Berlin


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


class PrePreAllocFork(Shanghai):
    """
    Dummy fork used for testing.
    """

    @classmethod
    def pre_allocation(cls, block_number: int = 0, timestamp: int = 0) -> Mapping:
        """
        Return some starting point for allocation.
        """
        return {"test": "test"}


class PreAllocFork(PrePreAllocFork):
    """
    Dummy fork used for testing.
    """

    @classmethod
    def pre_allocation(cls, block_number: int = 0, timestamp: int = 0) -> Mapping:
        """
        Add allocation to the pre-existing one from previous fork.
        """
        return {"test2": "test2"} | super(PreAllocFork, cls).pre_allocation(
            block_number, timestamp
        )


@transition_fork(to_fork=PreAllocFork, at_timestamp=15_000)
class PreAllocTransitionFork(PrePreAllocFork):
    """
    PrePreAllocFork to PreAllocFork transition at Timestamp 15k
    """

    pass


def test_pre_alloc():
    assert PrePreAllocFork.pre_allocation() == {"test": "test"}
    assert PreAllocFork.pre_allocation() == {"test": "test", "test2": "test2"}
    assert PreAllocTransitionFork.pre_allocation() == {
        "test": "test",
        "test2": "test2",
    }
    assert PreAllocTransitionFork.pre_allocation(block_number=0, timestamp=0) == {
        "test": "test",
        "test2": "test2",
    }


def test_precompiles():
    Cancun.precompiles() == list(range(11))[1:]


def test_tx_types():
    Cancun.tx_types() == list(range(4))
