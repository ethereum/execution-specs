"""
Pytest fixtures for the `build-block` simulator.

Configures the hive back-end & EL clients for block building correctness
testing via the ``testing_buildBlockV1`` endpoint.
"""

import io
from typing import Generator, Mapping

import pytest
from hive.client import Client

from execution_testing.fixtures import BlockchainEngineFixture
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.rpc import TestingRPC

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
    """Set the supported fixture formats for the build-block simulator."""
    config.supported_fixture_formats = [BlockchainEngineFixture]  # type: ignore[attr-defined]


@pytest.fixture(scope="module")
def test_suite_name() -> str:
    """The name of the hive test suite used in this simulator."""
    return "eels/build-block"


@pytest.fixture(scope="module")
def test_suite_description() -> str:
    """The description of the hive test suite used in this simulator."""
    return (
        "Test block building correctness via the "
        "testing_buildBlockV1 endpoint."
    )


@pytest.fixture(scope="function")
def client_files(
    buffered_genesis: io.BufferedReader,
) -> Mapping[str, io.BufferedReader]:
    """Define the files that hive will start the client with."""
    return {"/genesis.json": buffered_genesis}


@pytest.fixture(scope="function")
def genesis_header(fixture: BlockchainEngineFixture) -> FixtureHeader:
    """Provide the genesis header from the fixture."""
    return fixture.genesis


@pytest.fixture(scope="function")
def testing_rpc(client: Client) -> Generator[TestingRPC, None, None]:
    """Initialize Testing RPC client for the execution client under test."""
    with TestingRPC(f"http://{client.ip}:8545") as rpc:
        yield rpc
