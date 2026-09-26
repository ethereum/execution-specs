"""Tests for the `consume reorg` simulator's client environment fixture."""

from execution_testing.client_clis import TransitionTool
from execution_testing.fixtures.reorg import BlockchainEngineReorgFixture
from execution_testing.forks import Cancun
from execution_testing.specs.reorg import ReorgTest
from execution_testing.test_types import Alloc

from ..simulators.reorg.conftest import environment


def client_env(t8n: TransitionTool, min_reorg_depth: int | None) -> dict:
    """The client environment for an empty fixture."""
    test = ReorgTest(
        fork=Cancun,
        pre=Alloc(),
        blocks=[],
        steps=[],
        min_reorg_depth=min_reorg_depth,
    )
    fixture = test.generate(
        t8n=t8n, fixture_format=BlockchainEngineReorgFixture
    ).fixture
    return environment.__wrapped__(fixture, 8545)  # type: ignore[attr-defined]


def test_environment_maps_min_reorg_depth_to_hive_var(
    default_t8n: TransitionTool,
) -> None:
    """A set `minReorgDepth` becomes `HIVE_ENGINE_MAX_REORG_DEPTH`."""
    env = client_env(default_t8n, 72)
    assert env["HIVE_ENGINE_MAX_REORG_DEPTH"] == "72"


def test_environment_omits_var_when_min_reorg_depth_unset(
    default_t8n: TransitionTool,
) -> None:
    """No `minReorgDepth` means no depth override; client defaults apply."""
    env = client_env(default_t8n, None)
    assert "HIVE_ENGINE_MAX_REORG_DEPTH" not in env
