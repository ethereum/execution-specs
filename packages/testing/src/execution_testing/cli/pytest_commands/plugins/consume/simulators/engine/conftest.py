"""
Pytest fixtures for the `consume engine` simulator.

Configures the hive back-end & EL clients for each individual test execution.
"""

import io
from typing import Mapping

import pytest

from execution_testing.fixtures import BlockchainEngineFixture
from execution_testing.fixtures.blockchain import FixtureHeader

pytest_plugins = (
    "execution_testing.cli.pytest_commands.plugins.pytest_hive.pytest_hive",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.base",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.single_test_client",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.test_case_description",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.timing_data",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.exceptions",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.engine_api",
)


def pytest_configure(config: pytest.Config) -> None:
    """Set the supported fixture formats for the engine simulator."""
    config.supported_fixture_formats = [BlockchainEngineFixture]  # type: ignore[attr-defined]


@pytest.fixture(scope="module")
def test_suite_name() -> str:
    """The name of the hive test suite used in this simulator."""
    return "eels/consume-engine"


@pytest.fixture(scope="module")
def test_suite_description() -> str:
    """The description of the hive test suite used in this simulator."""
    return "Execute blockchain tests against clients using the Engine API."


@pytest.fixture(scope="function")
def client_files(
    buffered_genesis: io.BufferedReader,
) -> Mapping[str, io.BufferedReader]:
    """Define the files that hive will start the client with."""
    files = {}
    files["/genesis.json"] = buffered_genesis
    return files


@pytest.fixture(scope="function")
def genesis_header(fixture: BlockchainEngineFixture) -> "FixtureHeader":
    """Provide the genesis header from the fixture."""
    return fixture.genesis
