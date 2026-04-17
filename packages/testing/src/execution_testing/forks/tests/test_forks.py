"""Test fork utilities."""

from typing import Dict

import pytest
from pydantic import BaseModel

from execution_testing.base_types import BlobSchedule

from ..forks.eips.paris.eip_3675 import EIP3675
from ..forks.forks import (
    BPO1,
    BPO2,
    BPO3,
    BPO4,
    Amsterdam,
    Berlin,
    Cancun,
    Frontier,
    Homestead,
    Istanbul,
    London,
    Osaka,
    Paris,
    Prague,
    Shanghai,
    SpuriousDragon,
)
from ..forks.transition import (
    BerlinToLondonAt5,
    BPO1ToBPO2AtTime15k,
    BPO2ToAmsterdamAtTime15k,
    BPO2ToBPO3AtTime15k,
    BPO3ToBPO4AtTime15k,
    CancunToPragueAtTime15k,
    OsakaToBPO1AtTime15k,
    ParisToShanghaiAtTime15k,
    PragueToOsakaAtTime15k,
    ShanghaiToCancunAtTime15k,
)
from ..helpers import (
    Fork,
    ForkAdapter,
    ForkOrNoneAdapter,
    ForkSetAdapter,
    TransitionFork,
    forks_from,
    forks_from_until,
    get_deployed_forks,
    get_forks,
    get_selected_fork_set,
    transition_fork_from_to,
    transition_fork_to,
)
from ..transition_base_fork import TransitionBaseClass, transition_fork

FIRST_DEPLOYED = Frontier
LAST_DEPLOYED = Osaka
LAST_DEVELOPMENT = Amsterdam
DEVELOPMENT_FORKS = [Amsterdam]


def test_transition_forks() -> None:
    """Test transition fork utilities."""
    assert transition_fork_from_to(Berlin, London) == BerlinToLondonAt5
    assert transition_fork_from_to(Berlin, Paris) is None
    assert transition_fork_to(Shanghai) == {ParisToShanghaiAtTime15k}

    # Test forks transitioned to and from
    assert BerlinToLondonAt5.transitions_to() == London
    assert BerlinToLondonAt5.transitions_from() == Berlin

    assert (
        BerlinToLondonAt5.fork_at(
            block_number=4, timestamp=0
        ).transition_tool_name()
        == "Berlin"
    )
    assert (
        BerlinToLondonAt5.fork_at(
            block_number=5, timestamp=0
        ).transition_tool_name()
        == "London"
    )

    assert (
        ParisToShanghaiAtTime15k.fork_at(
            block_number=0, timestamp=14_999
        ).transition_tool_name()
        == "Merge"
    )
    assert (
        ParisToShanghaiAtTime15k.fork_at(
            block_number=0, timestamp=15_000
        ).transition_tool_name()
        == "Shanghai"
    )

    assert (
        BerlinToLondonAt5.fork_at(
            block_number=4, timestamp=0
        ).header_base_fee_required()
        is False
    )
    assert (
        BerlinToLondonAt5.fork_at(
            block_number=5, timestamp=0
        ).header_base_fee_required()
        is True
    )

    assert (
        ParisToShanghaiAtTime15k.fork_at(
            block_number=0, timestamp=14_999
        ).header_withdrawals_required()
        is False
    )
    assert (
        ParisToShanghaiAtTime15k.fork_at(
            block_number=0, timestamp=15_000
        ).header_withdrawals_required()
        is True
    )

    assert (
        ParisToShanghaiAtTime15k.fork_at(
            block_number=0, timestamp=14_999
        ).engine_new_payload_version()
        == 1
    )
    assert (
        ParisToShanghaiAtTime15k.fork_at(
            block_number=0, timestamp=15_000
        ).engine_new_payload_version()
        == 2
    )

    assert BerlinToLondonAt5.fork_at(block_number=4, timestamp=0) is Berlin
    assert BerlinToLondonAt5.fork_at(block_number=5, timestamp=0) is London
    assert (
        ParisToShanghaiAtTime15k.fork_at(block_number=0, timestamp=14_999)
        is Paris
    )
    assert (
        ParisToShanghaiAtTime15k.fork_at(block_number=0, timestamp=15_000)
        is Shanghai
    )
    assert ParisToShanghaiAtTime15k.fork_at() is Paris
    assert (
        ParisToShanghaiAtTime15k.fork_at(
            block_number=10_000_000, timestamp=14_999
        )
        is Paris
    )


def test_forks_from() -> None:  # noqa: D103
    assert forks_from(Paris)[0] == Paris
    assert forks_from(Paris)[-1] == LAST_DEPLOYED
    assert forks_from(Paris, deployed_only=True)[0] == Paris
    assert forks_from(Paris, deployed_only=True)[-1] == LAST_DEPLOYED
    assert forks_from(Paris, deployed_only=False)[0] == Paris
    # Too flaky
    # assert forks_from(Paris, deployed_only=False)[-1] == LAST_DEVELOPMENT


def test_forks() -> None:
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

    # Merge name will be changed to paris, but we need to check the inheriting
    # fork name is still the default
    assert Paris.transition_tool_name() == "Merge"
    assert Shanghai.transition_tool_name() == "Shanghai"
    assert f"{Paris}" == "Paris"
    assert f"{Shanghai}" == "Shanghai"
    assert f"{ParisToShanghaiAtTime15k}" == "ParisToShanghaiAtTime15k"

    # Test some fork properties
    assert Berlin.header_base_fee_required() is False
    assert London.header_base_fee_required() is True
    assert Paris.header_base_fee_required() is True
    # Default values of normal forks if the genesis block
    assert Paris.header_base_fee_required() is True

    # Transition forks too
    assert (
        BerlinToLondonAt5.fork_at(
            block_number=4, timestamp=0
        ).header_base_fee_required()
        is False
    )
    assert (
        BerlinToLondonAt5.fork_at(
            block_number=5, timestamp=0
        ).header_base_fee_required()
        is True
    )
    assert (
        ParisToShanghaiAtTime15k.fork_at(
            block_number=0, timestamp=14_999
        ).header_withdrawals_required()
        is False
    )
    assert (
        ParisToShanghaiAtTime15k.fork_at(
            block_number=0, timestamp=15_000
        ).header_withdrawals_required()
        is True
    )
    assert (
        ParisToShanghaiAtTime15k.fork_at().header_withdrawals_required()
        is False
    )


class ForkInPydanticModel(BaseModel):
    """Fork in pydantic model."""

    fork_1: Fork | TransitionFork
    fork_2: Fork | TransitionFork
    fork_3: Fork | TransitionFork | None


def test_fork_in_pydantic_model() -> None:
    """Test fork in pydantic model."""
    model = ForkInPydanticModel(
        fork_1=Paris, fork_2=ParisToShanghaiAtTime15k, fork_3=None
    )
    assert model.model_dump() == {
        "fork_1": "Paris",
        "fork_2": "ParisToShanghaiAtTime15k",
        "fork_3": None,
    }
    assert model.model_dump_json() == (
        '{"fork_1":"Paris","fork_2":"ParisToShanghaiAtTime15k","fork_3":null}'
    )
    model = ForkInPydanticModel.model_validate_json(
        '{"fork_1": "Paris", "fork_2": "ParisToShanghaiAtTime15k", '
        '"fork_3": null}'
    )
    assert model.fork_1 is Paris
    assert model.fork_2 is ParisToShanghaiAtTime15k
    assert model.fork_3 is None


def test_fork_comparison() -> None:
    """Test fork comparison operators."""
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


def test_transition_fork_comparison() -> None:
    """
    Test comparing to a transition fork.

    The comparison logic is based on the logic we use to generate the tests.

    E.g. given transition fork A->B, when filling, and given the from/until
    markers, we expect the following logic:

    Marker    Comparison   A->B Included
    --------- ------------ ---------------
    From A    fork >= A    True
    Until A   fork <= A    False
    From B    fork >= B    True
    Until B   fork <= B    True
    """
    assert BerlinToLondonAt5 >= Berlin
    assert not BerlinToLondonAt5 <= Berlin
    assert BerlinToLondonAt5 >= London
    assert BerlinToLondonAt5 <= London

    # Comparisons between transition forks is done against the `transitions_to`
    # fork
    assert BerlinToLondonAt5 < ParisToShanghaiAtTime15k
    assert ParisToShanghaiAtTime15k > BerlinToLondonAt5
    assert BerlinToLondonAt5 == BerlinToLondonAt5
    assert BerlinToLondonAt5 != ParisToShanghaiAtTime15k
    assert BerlinToLondonAt5 <= ParisToShanghaiAtTime15k
    assert ParisToShanghaiAtTime15k >= BerlinToLondonAt5

    assert sorted(
        {
            PragueToOsakaAtTime15k,
            CancunToPragueAtTime15k,
            ParisToShanghaiAtTime15k,
            ShanghaiToCancunAtTime15k,
            BerlinToLondonAt5,
        }
    ) == [
        BerlinToLondonAt5,
        ParisToShanghaiAtTime15k,
        ShanghaiToCancunAtTime15k,
        CancunToPragueAtTime15k,
        PragueToOsakaAtTime15k,
    ]


def test_get_forks() -> None:  # noqa: D103
    all_forks = get_forks()
    assert all_forks[0] == FIRST_DEPLOYED
    # assert all_forks[-1] == LAST_DEVELOPMENT  # Too flaky


def test_deployed_forks() -> None:  # noqa: D103
    deployed_forks = get_deployed_forks()
    assert deployed_forks[0] == FIRST_DEPLOYED
    assert deployed_forks[-1] == LAST_DEPLOYED


class PrePreAllocFork(Shanghai):
    """Dummy fork used for testing."""

    @classmethod
    def pre_allocation(cls) -> Dict:
        """Return some starting point for allocation."""
        return {"test": "test"}


class PreAllocFork(PrePreAllocFork):
    """Dummy fork used for testing."""

    @classmethod
    def pre_allocation(cls) -> Dict:
        """Add allocation to the pre-existing one from previous fork."""
        return {"test2": "test2"} | super(PreAllocFork, cls).pre_allocation()


@transition_fork(
    to_fork=PreAllocFork, from_fork=PrePreAllocFork, at_timestamp=15_000
)
class PreAllocTransitionFork(TransitionBaseClass):
    """PrePreAllocFork to PreAllocFork transition at Timestamp 15k."""

    pass


def test_pre_alloc() -> None:  # noqa: D103
    assert PrePreAllocFork.pre_allocation() == {"test": "test"}
    assert PreAllocFork.pre_allocation() == {"test": "test", "test2": "test2"}
    assert PreAllocTransitionFork.transitions_to().pre_allocation() == {
        "test": "test",
        "test2": "test2",
    }
    assert PreAllocTransitionFork.transitions_from().pre_allocation() == {
        "test": "test",
    }


def test_precompiles() -> None:  # noqa: D103
    assert sorted(Cancun.precompiles()) == list(range(1, 11))


def test_tx_types() -> None:  # noqa: D103
    assert Cancun.tx_types() == list(reversed(range(4)))


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
def test_tx_intrinsic_gas_functions(  # noqa: D103
    fork: Fork, calldata: bytes, create_tx: bool
) -> None:
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


class FutureFork(Osaka):
    """
    Dummy fork used for testing.

    Contains no changes to the blob parameters from the parent fork in order to
    confirm that it's added to the blob schedule even if it doesn't have any
    changes.
    """

    pass


@pytest.mark.parametrize(
    "fork,expected_schedule",
    [
        pytest.param(Frontier, None, id="Frontier"),
        pytest.param(
            Cancun,
            {
                "Cancun": {
                    "target_blobs_per_block": 3,
                    "max_blobs_per_block": 6,
                    "baseFeeUpdateFraction": 3338477,
                },
            },
            id="Cancun",
        ),
        pytest.param(
            Prague,
            {
                "Cancun": {
                    "target_blobs_per_block": 3,
                    "max_blobs_per_block": 6,
                    "baseFeeUpdateFraction": 3338477,
                },
                "Prague": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
            },
            id="Prague",
        ),
        pytest.param(
            Osaka,
            {
                "Cancun": {
                    "target_blobs_per_block": 3,
                    "max_blobs_per_block": 6,
                    "baseFeeUpdateFraction": 3338477,
                },
                "Prague": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
                "Osaka": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
            },
            id="Osaka",
        ),
        pytest.param(
            CancunToPragueAtTime15k,
            {
                "Cancun": {
                    "target_blobs_per_block": 3,
                    "max_blobs_per_block": 6,
                    "baseFeeUpdateFraction": 3338477,
                },
                "Prague": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
            },
            id="CancunToPragueAtTime15k",
        ),
        pytest.param(
            PragueToOsakaAtTime15k,
            {
                "Cancun": {
                    "target_blobs_per_block": 3,
                    "max_blobs_per_block": 6,
                    "baseFeeUpdateFraction": 3338477,
                },
                "Prague": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
                "Osaka": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
            },
            id="PragueToOsakaAtTime15k",
        ),
        pytest.param(
            FutureFork,
            {
                "Cancun": {
                    "target_blobs_per_block": 3,
                    "max_blobs_per_block": 6,
                    "baseFeeUpdateFraction": 3338477,
                },
                "Prague": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
                "Osaka": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
                "FutureFork": {
                    "target_blobs_per_block": 6,
                    "max_blobs_per_block": 9,
                    "baseFeeUpdateFraction": 5007716,
                },
            },
            id="FutureFork",
        ),
    ],
)
def test_blob_schedules(
    fork: Fork | TransitionFork, expected_schedule: Dict | None
) -> None:
    """Test blob schedules for different forks."""
    if expected_schedule is None:
        assert fork.transitions_to().blob_schedule() is None
    else:
        assert fork.transitions_to().blob_schedule() == BlobSchedule(
            **expected_schedule
        )


def test_bpo_fork() -> None:  # noqa: D103
    assert Osaka.bpo_fork() is False
    assert BPO1.bpo_fork() is True
    assert BPO2.bpo_fork() is True
    assert BPO3.bpo_fork() is True
    assert BPO4.bpo_fork() is True
    assert OsakaToBPO1AtTime15k.fork_at().bpo_fork() is False
    assert BPO1ToBPO2AtTime15k.fork_at().bpo_fork() is True
    assert BPO2ToBPO3AtTime15k.fork_at().bpo_fork() is True
    assert BPO3ToBPO4AtTime15k.fork_at().bpo_fork() is True


def test_fork_adapters() -> None:  # noqa: D103
    assert Osaka == ForkAdapter.validate_python("Osaka")
    assert Osaka == ForkOrNoneAdapter.validate_python("Osaka")
    assert ForkOrNoneAdapter.validate_python(None) is None
    assert {Osaka, Prague} == ForkSetAdapter.validate_python("Osaka, Prague")
    assert {Osaka, Prague} == ForkSetAdapter.validate_python("osaka, Prague")
    assert {Osaka, Prague} == ForkSetAdapter.validate_python(
        {"osaka", "Prague"}
    )
    assert {Osaka} == ForkSetAdapter.validate_python("Osaka")
    assert {Osaka} == ForkSetAdapter.validate_python({Osaka})
    assert set() == ForkSetAdapter.validate_python("")


class TestSelectedForkSetWithTransitionBoundaries:
    """Test `get_selected_fork_set` with transition fork boundaries."""

    @staticmethod
    def _normal_forks(fork_set: set) -> set:
        """Return the set of normal (non-transition) forks."""
        return {f for f in fork_set if not issubclass(f, TransitionBaseClass)}

    @staticmethod
    def _transition_forks(fork_set: set) -> set:
        """Return the set of transition forks."""
        return {f for f in fork_set if issubclass(f, TransitionBaseClass)}

    def test_transition_from_and_until(self) -> None:
        """Test range with transition forks as both boundaries."""
        result = get_selected_fork_set(
            single_fork=set(),
            forks_from={OsakaToBPO1AtTime15k},  # type: ignore[arg-type]
            forks_until={BPO2ToAmsterdamAtTime15k},  # type: ignore[arg-type]
        )
        assert self._normal_forks(result) == {BPO1, BPO2}
        assert self._transition_forks(result) == {
            OsakaToBPO1AtTime15k,
            BPO1ToBPO2AtTime15k,
            BPO2ToAmsterdamAtTime15k,
        }

    def test_transition_until_excludes_target(self) -> None:
        """Transition fork `--until` must not include `transitions_to()`."""
        result = get_selected_fork_set(
            single_fork=set(),
            forks_from={OsakaToBPO1AtTime15k},  # type: ignore[arg-type]
            forks_until={BPO2ToAmsterdamAtTime15k},  # type: ignore[arg-type]
        )
        assert Amsterdam not in result

    def test_non_bpo_transition_boundaries(self) -> None:
        """Test non-BPO transition fork boundaries."""
        result = get_selected_fork_set(
            single_fork=set(),
            forks_from={CancunToPragueAtTime15k},  # type: ignore[arg-type]
            forks_until={PragueToOsakaAtTime15k},  # type: ignore[arg-type]
        )
        assert self._normal_forks(result) == {Prague}
        assert self._transition_forks(result) == {
            CancunToPragueAtTime15k,
            PragueToOsakaAtTime15k,
        }
        assert Osaka not in result

    def test_normal_boundaries_unchanged(self) -> None:
        """Normal fork boundaries still work as before."""
        result = get_selected_fork_set(
            single_fork=set(),
            forks_from={Prague},
            forks_until={Osaka},
        )
        assert self._normal_forks(result) == {Prague, Osaka}
        assert CancunToPragueAtTime15k in result
        assert PragueToOsakaAtTime15k in result

    def test_transition_from_normal_until(self) -> None:
        """Test transition `--from` with normal `--until`."""
        result = get_selected_fork_set(
            single_fork=set(),
            forks_from={OsakaToBPO1AtTime15k},  # type: ignore[arg-type]
            forks_until={BPO2},
        )
        assert self._normal_forks(result) == {BPO1, BPO2}
        assert OsakaToBPO1AtTime15k in result
        assert BPO1ToBPO2AtTime15k in result
        assert BPO2ToAmsterdamAtTime15k not in result


def test_blob_constants() -> None:  # noqa: D103
    assert Osaka.get_blob_constant("AMOUNT_CELL_PROOFS") == 128


def test_method_versions() -> None:  # noqa: D103
    assert London.engine_get_blobs_version() is None
    assert London.engine_get_payload_version() is None
    assert London.engine_new_payload_version() is None
    assert London.engine_forkchoice_updated_version() is None

    assert Paris.engine_get_blobs_version() is None
    assert Paris.engine_get_payload_version() == 1
    assert Paris.engine_new_payload_version() == 1
    assert Paris.engine_forkchoice_updated_version() == 1

    assert Shanghai.engine_get_blobs_version() is None
    assert Shanghai.engine_get_payload_version() == 2
    assert Shanghai.engine_new_payload_version() == 2
    assert Shanghai.engine_forkchoice_updated_version() == 2

    assert Cancun.engine_get_blobs_version() == 1
    assert Cancun.engine_get_payload_version() == 3
    assert Cancun.engine_new_payload_version() == 3
    assert Cancun.engine_forkchoice_updated_version() == 3

    assert Prague.engine_get_blobs_version() == 1
    assert Prague.engine_get_payload_version() == 4
    assert Prague.engine_new_payload_version() == 4
    assert Prague.engine_forkchoice_updated_version() == 3

    assert Osaka.engine_get_blobs_version() == 2
    assert Osaka.engine_get_payload_version() == 5
    assert Osaka.engine_new_payload_version() == 4
    assert Osaka.engine_forkchoice_updated_version() == 3

    assert Amsterdam.engine_get_payload_version() == 6
    assert Amsterdam.engine_new_payload_version() == 5


def test_eips() -> None:  # noqa: D103
    assert EIP3675.enabling_forks() == {Paris}
    assert Paris.is_eip_enabled(3675)
    assert Paris.is_eip_enabled(3675, 1559)
    assert Shanghai.is_eip_enabled(3675)
    assert not Paris.is_eip_enabled(3855)
    assert not Paris.is_eip_enabled(3675, 3855)
    assert not Paris.is_eip_enabled(3855, 3675)
    assert Shanghai.is_eip_enabled(3855)


def test_fork_variant_ordering() -> None:
    """
    Variants from `with_env_gas_limit` must compare consistently with
    their canonical parent: equal to the parent, ordered identically
    against other canonical forks.
    """
    variant = London.with_env_gas_limit(30_000_000)

    assert variant == London
    assert hash(variant) == hash(London)

    assert variant > SpuriousDragon
    assert variant >= SpuriousDragon
    assert variant < Cancun
    assert variant <= Cancun

    assert not (variant > London)
    assert not (variant < London)
    assert variant >= London
    assert variant <= London
