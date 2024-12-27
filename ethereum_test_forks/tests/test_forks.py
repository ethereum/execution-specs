"""Test fork utilities."""

from typing import Mapping, cast

import pytest
from semver import Version

from ..base_fork import Fork
from ..forks.forks import (
    Berlin,
    Cancun,
    Frontier,
    Homestead,
    Istanbul,
    London,
    Paris,
    Prague,
    Shanghai,
)
from ..forks.transition import BerlinToLondonAt5, ParisToShanghaiAtTime15k
from ..helpers import (
    forks_from,
    forks_from_until,
    get_closest_fork_with_solc_support,
    get_deployed_forks,
    get_forks,
    get_forks_with_solc_support,
    transition_fork_from_to,
    transition_fork_to,
)
from ..transition_base_fork import transition_fork

FIRST_DEPLOYED = Frontier
LAST_DEPLOYED = Cancun
LAST_DEVELOPMENT = Prague
DEVELOPMENT_FORKS = [Prague]


def test_transition_forks():
    """Test transition fork utilities."""
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
    assert forks_from(Paris)[0] == Paris
    assert forks_from(Paris)[-1] == LAST_DEPLOYED
    assert forks_from(Paris, deployed_only=True)[0] == Paris
    assert forks_from(Paris, deployed_only=True)[-1] == LAST_DEPLOYED
    assert forks_from(Paris, deployed_only=False)[0] == Paris
    # assert forks_from(Paris, deployed_only=False)[-1] == LAST_DEVELOPMENT  # Too flaky


def test_forks():
    """Test fork utilities."""
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
    assert Paris.blockchain_test_network_name() == "Paris"
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
    # assert all_forks[-1] == LAST_DEVELOPMENT  # Too flaky


def test_deployed_forks():  # noqa: D103
    deployed_forks = get_deployed_forks()
    assert deployed_forks[0] == FIRST_DEPLOYED
    assert deployed_forks[-1] == LAST_DEPLOYED


class PrePreAllocFork(Shanghai):
    """Dummy fork used for testing."""

    @classmethod
    def pre_allocation(cls) -> Mapping:
        """Return some starting point for allocation."""
        return {"test": "test"}


class PreAllocFork(PrePreAllocFork):
    """Dummy fork used for testing."""

    @classmethod
    def pre_allocation(cls) -> Mapping:
        """Add allocation to the pre-existing one from previous fork."""
        return {"test2": "test2"} | super(PreAllocFork, cls).pre_allocation()


@transition_fork(to_fork=PreAllocFork, at_timestamp=15_000)
class PreAllocTransitionFork(PrePreAllocFork):
    """PrePreAllocFork to PreAllocFork transition at Timestamp 15k."""

    pass


def test_pre_alloc():  # noqa: D103
    assert PrePreAllocFork.pre_allocation() == {"test": "test"}
    assert PreAllocFork.pre_allocation() == {"test": "test", "test2": "test2"}
    assert PreAllocTransitionFork.pre_allocation() == {
        "test": "test",
        "test2": "test2",
    }
    assert PreAllocTransitionFork.pre_allocation() == {
        "test": "test",
        "test2": "test2",
    }


def test_precompiles():  # noqa: D103
    Cancun.precompiles() == list(range(11))[1:]  # noqa: B015


def test_tx_types():  # noqa: D103
    Cancun.tx_types() == list(range(4))  # noqa: B015


def test_solc_versioning():  # noqa: D103
    assert len(get_forks_with_solc_support(Version.parse("0.8.20"))) == 13
    assert len(get_forks_with_solc_support(Version.parse("0.8.24"))) > 13


def test_closest_fork_supported_by_solc():  # noqa: D103
    assert get_closest_fork_with_solc_support(Paris, Version.parse("0.8.20")) == Paris
    assert get_closest_fork_with_solc_support(Cancun, Version.parse("0.8.20")) == Shanghai
    assert get_closest_fork_with_solc_support(Cancun, Version.parse("0.8.24")) == Cancun
    assert get_closest_fork_with_solc_support(Prague, Version.parse("0.8.24")) == Cancun


@pytest.mark.parametrize(
    "fork",
    [
        pytest.param(Berlin, id="Berlin"),
        pytest.param(Istanbul, id="Istanbul"),
        pytest.param(Homestead, id="Homestead"),
        pytest.param(Frontier, id="Frontier"),
    ],
)
@pytest.mark.parametrize(
    "calldata",
    [
        pytest.param(b"\0", id="zero-data"),
        pytest.param(b"\1", id="non-zero-data"),
    ],
)
@pytest.mark.parametrize(
    "create_tx",
    [False, True],
)
def test_tx_intrinsic_gas_functions(fork: Fork, calldata: bytes, create_tx: bool):  # noqa: D103
    intrinsic_gas = 21_000
    if calldata == b"\0":
        intrinsic_gas += 4
    else:
        if fork >= Istanbul:
            intrinsic_gas += 16
        else:
            intrinsic_gas += 68

    if create_tx:
        if fork >= Homestead:
            intrinsic_gas += 32000
        intrinsic_gas += 2
    assert (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=calldata,
            contract_creation=create_tx,
        )
        == intrinsic_gas
    )
