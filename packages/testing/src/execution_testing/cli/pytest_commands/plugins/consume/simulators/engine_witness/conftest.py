"""
Pytest fixtures for the `consume engine-witness` simulator.

Drives the Hive back-end and EL clients through the REST
`POST /new-payload-with-witness` endpoint (execution-apis PR #773),
asserting the client-generated execution witness matches the fixture.
"""

import io
from typing import Mapping

import pytest
from hive.client import Client

from execution_testing.exceptions import ExceptionMapper
from execution_testing.fixtures import BlockchainEngineFixture
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.rpc import EngineWitnessRPC

pytest_plugins = (
    "execution_testing.cli.pytest_commands.plugins.pytest_hive.pytest_hive",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.base",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.single_test_client",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.test_case_description",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.timing_data",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.exceptions",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.engine_api",
)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the `--ssz` transport flag for the engine-witness simulator."""
    parser.addoption(
        "--ssz",
        action="store_true",
        default=False,
        help=(
            "Use the REST POST /new-payload-with-witness endpoint with "
            "SSZ-encoded response (execution-apis PR #773) instead of the "
            "default JSON-RPC engine_newPayloadWithWitnessVX with "
            "RLP-encoded witness (geth-style)."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    """Set the supported fixture formats for the engine-witness simulator."""
    config.supported_fixture_formats = [BlockchainEngineFixture]  # type: ignore[attr-defined]


@pytest.fixture(scope="session")
def use_ssz_transport(request: pytest.FixtureRequest) -> bool:
    """Return True when `--ssz` was passed on the CLI."""
    return bool(request.config.getoption("--ssz"))


@pytest.fixture(scope="module")
def test_suite_name() -> str:
    """The name of the hive test suite used in this simulator."""
    return "eels/consume-engine-witness"


@pytest.fixture(scope="module")
def test_suite_description() -> str:
    """The description of the hive test suite used in this simulator."""
    return (
        "Execute blockchain-engine fixtures via the REST "
        "POST /new-payload-with-witness endpoint (execution-apis PR #773), "
        "verifying the client-generated execution witness against the "
        "fixture witness."
    )


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


@pytest.fixture(scope="function")
def engine_witness_rpc(
    client: Client, client_exception_mapper: ExceptionMapper | None
) -> EngineWitnessRPC:
    """Provide a REST client for POST /new-payload-with-witness."""
    if client_exception_mapper:
        return EngineWitnessRPC(
            f"http://{client.ip}:8551",
            response_validation_context={
                "exception_mapper": client_exception_mapper,
            },
        )
    return EngineWitnessRPC(f"http://{client.ip}:8551")
