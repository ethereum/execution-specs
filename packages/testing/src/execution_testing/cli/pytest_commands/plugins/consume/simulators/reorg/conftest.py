"""
Pytest fixtures for the `consume reorg` simulator.

One fresh client per fixture; the client environment is the standard engine
environment plus the fixture's ``requires`` (``HIVE_*``) variables, if any.
"""

import io
import logging
from typing import Literal, Mapping

import pytest

from execution_testing.fixtures import BlockchainEngineReorgFixture
from execution_testing.fixtures.blockchain import FixtureHeader

from ..single_test_client import client_environment

pytest_plugins = (
    "execution_testing.cli.pytest_commands.plugins.pytest_hive.pytest_hive",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.base",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.single_test_client",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.test_case_description",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.timing_data",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.exceptions",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.engine_api",
)

logger = logging.getLogger(__name__)


def pytest_configure(config: pytest.Config) -> None:
    """Set the supported fixture formats for the reorg simulator."""
    config.supported_fixture_formats = [BlockchainEngineReorgFixture]  # type: ignore[attr-defined]


@pytest.fixture(scope="module")
def test_suite_name() -> str:
    """The name of the hive test suite used in this simulator."""
    return "eels/consume-reorg"


@pytest.fixture(scope="module")
def test_suite_description() -> str:
    """The description of the hive test suite used in this simulator."""
    return (
        "Execute Engine API reorg tests against clients: a DAG of payloads "
        "and an ordered list of newPayload/forkchoiceUpdated/RPC steps with "
        "expected outcomes."
    )


@pytest.fixture(scope="function")
def environment(
    fixture: BlockchainEngineReorgFixture,
    check_live_port: Literal[8545, 8551],
) -> dict:
    """
    Client environment: standard engine ruleset plus the fixture's
    ``requires`` variables (client tuning such as reorg-depth caps).
    """
    env = client_environment(
        fixture.fork, fixture.config.chain_id, check_live_port
    )
    if fixture.requires:
        env.update(fixture.requires)
    return env


@pytest.fixture(scope="function")
def client_files(
    buffered_genesis: io.BufferedReader,
) -> Mapping[str, io.BufferedReader]:
    """Define the files that hive will start the client with."""
    return {"/genesis.json": buffered_genesis}


@pytest.fixture(scope="function")
def genesis_header(fixture: BlockchainEngineReorgFixture) -> FixtureHeader:
    """Provide the genesis header from the fixture."""
    return fixture.genesis
