"""Tests for the `consume reorg` simulator's client environment fixture."""

import json
import subprocess
import sys
from pathlib import Path

from execution_testing.client_clis import TransitionTool
from execution_testing.fixtures.reorg import BlockchainEngineReorgFixture
from execution_testing.forks import Cancun
from execution_testing.specs.reorg import ReorgTest
from execution_testing.test_types import Alloc

from ..simulators.reorg import reorg_depth
from .direct_calls import fixture_body


def reorg_fixture(
    t8n: TransitionTool, min_reorg_depth: int | None
) -> BlockchainEngineReorgFixture:
    """An empty reorg fixture with ``min_reorg_depth``."""
    fixture = (
        ReorgTest(
            fork=Cancun,
            pre=Alloc().with_genesis_accounts(),
            blocks=[],
            steps=[],
            min_reorg_depth=min_reorg_depth,
        )
        .generate(t8n=t8n, fixture_format=BlockchainEngineReorgFixture)
        .fixture
    )
    assert isinstance(fixture, BlockchainEngineReorgFixture)
    return fixture


def test_environment_maps_min_reorg_depth_to_hive_var(
    default_t8n: TransitionTool,
) -> None:
    """A set `minReorgDepth` becomes `HIVE_ENGINE_MAX_REORG_DEPTH`."""
    env = fixture_body(reorg_depth.environment)(
        {"HIVE_FORK_CANCUN": "0"}, reorg_fixture(default_t8n, 72)
    )
    assert env == {
        "HIVE_FORK_CANCUN": "0",
        "HIVE_ENGINE_MAX_REORG_DEPTH": "72",
    }


def test_environment_omits_var_when_min_reorg_depth_unset(
    default_t8n: TransitionTool,
) -> None:
    """No `minReorgDepth` means no depth override; client defaults apply."""
    env = fixture_body(reorg_depth.environment)(
        {"HIVE_FORK_CANCUN": "0"}, reorg_fixture(default_t8n, None)
    )
    assert env == {"HIVE_FORK_CANCUN": "0"}


def test_reorg_items_resolve_the_reorg_depth_environment(
    default_t8n: TransitionTool, tmp_path: Path
) -> None:
    """
    `consume reorg` resolves `environment` from `reorg_depth`, which a
    definition in the simulator's conftest could not override: pytest
    prefers `single_test_client`, registered after the conftest.
    """
    fixtures = tmp_path / "fixtures"
    fixture_file = fixtures / "blockchain_tests_engine_reorg" / "reorg.json"
    fixture_file.parent.mkdir(parents=True)
    fixture = reorg_fixture(default_t8n, 72)
    fixture_file.write_text(
        json.dumps({"reorg": fixture.json_dict_with_info()})
    )
    consume = (
        "import sys; "
        "from execution_testing.cli.pytest_commands.consume import consume; "
        "sys.exit(consume())"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            consume,
            "reorg",
            "--input",
            str(fixtures),
            "--fixtures-per-test",
            "--collect-only",
            "-p",
            "no:cacheprovider",
        ],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )
    resolved = [
        line
        for line in result.stdout.splitlines()
        if line.startswith("environment -- ")
    ]
    assert resolved, result.stdout + result.stderr
    assert all("/reorg/reorg_depth.py:" in line for line in resolved), resolved
