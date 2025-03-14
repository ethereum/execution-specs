"""Common pytest fixtures for the RLP and Engine simulators."""

import io
import json
from pathlib import Path
from typing import Dict, Generator, List, Literal, cast

import pytest
import rich
from hive.client import Client, ClientType
from hive.testing import HiveTest

from ethereum_test_base_types import Number, to_json
from ethereum_test_fixtures import (
    BaseFixture,
    BlockchainFixtureCommon,
)
from ethereum_test_fixtures.consume import TestCaseIndexFile, TestCaseStream
from ethereum_test_fixtures.file import Fixtures
from ethereum_test_rpc import EthRPC
from pytest_plugins.consume.consume import FixturesSource
from pytest_plugins.consume.hive_simulators.ruleset import ruleset  # TODO: generate dynamically
from pytest_plugins.pytest_hive.hive_info import ClientInfo

from .timing import TimingData


def pytest_addoption(parser):
    """Hive simulator specific consume command line options."""
    consume_group = parser.getgroup(
        "consume", "Arguments related to consuming fixtures via a client"
    )
    consume_group.addoption(
        "--timing-data",
        action="store_true",
        dest="timing_data",
        default=False,
        help="Log the timing data for each test case execution.",
    )


@pytest.fixture(scope="function")
def eth_rpc(client: Client) -> EthRPC:
    """Initialize ethereum RPC client for the execution client under test."""
    return EthRPC(f"http://{client.ip}:8545")


@pytest.fixture(scope="function")
def hive_client_config_file_parameter(
    client_type: ClientType, client_file: List[ClientInfo]
) -> List[str]:
    """Return the hive client config file that is currently being used to configure tests."""
    for client in client_file:
        if client_type.name.startswith(client.client):
            return ["--client-file", f"<('{client.model_dump_json(exclude_none=True)}')"]
    return []


@pytest.fixture(scope="function")
def hive_consume_command(
    test_suite_name: str,
    client_type: ClientType,
    test_case: TestCaseIndexFile | TestCaseStream,
    hive_client_config_file_parameter: List[str],
) -> List[str]:
    """Command to run the test within hive."""
    command = ["./hive", "--sim", f"ethereum/{test_suite_name}"]
    if hive_client_config_file_parameter:
        command += hive_client_config_file_parameter
    command += ["--client", client_type.name, "--sim.limit", f'"{test_case.id}"']
    return command


@pytest.fixture(scope="function")
def hive_dev_command(
    client_type: ClientType,
    hive_client_config_file_parameter: List[str],
) -> List[str]:
    """Return the command used to instantiate hive alongside the `consume` command."""
    hive_dev = ["./hive", "--dev"]
    if hive_client_config_file_parameter:
        hive_dev += hive_client_config_file_parameter
    hive_dev += ["--client", client_type.name]
    return hive_dev


@pytest.fixture(scope="function")
def eest_consume_command(
    test_suite_name: str,
    test_case: TestCaseIndexFile | TestCaseStream,
    fixture_source_flags: List[str],
) -> List[str]:
    """Commands to run the test within EEST using a hive dev back-end."""
    return (
        ["consume", test_suite_name.split("-")[-1], "-v"]
        + fixture_source_flags
        + [
            "-k",
            f'"{test_case.id}"',
        ]
    )


@pytest.fixture(scope="function")
def test_case_description(
    fixture: BaseFixture,
    test_case: TestCaseIndexFile | TestCaseStream,
    hive_consume_command: List[str],
    hive_dev_command: List[str],
    eest_consume_command: List[str],
) -> str:
    """
    Create the description of the current blockchain fixture test case.
    Includes reproducible commands to re-run the test case against the target client.
    """
    description = f"Test id: {test_case.id}"
    if "url" in fixture.info:
        description += f"\n\nTest source: {fixture.info['url']}"
    if "description" not in fixture.info:
        description += "\n\nNo description field provided in the fixture's 'info' section."
    else:
        description += f"\n\n{fixture.info['description']}"
    description += (
        f"\n\nCommand to reproduce entirely in hive:"
        f"\n<code>{' '.join(hive_consume_command)}</code>"
    )
    eest_commands = "\n".join(
        f"{i + 1}. <code>{' '.join(cmd)}</code>"
        for i, cmd in enumerate([hive_dev_command, eest_consume_command])
    )
    description += (
        f"\n\nCommands to reproduce within EEST using a hive dev back-end:\n{eest_commands}"
    )
    description = description.replace("\n", "<br/>")
    return description


@pytest.fixture(scope="function", autouse=True)
def total_timing_data(request) -> Generator[TimingData, None, None]:
    """Record timing data for various stages of executing test case."""
    with TimingData("Total (seconds)") as total_timing_data:
        yield total_timing_data
    if request.config.getoption("timing_data"):
        rich.print(f"\n{total_timing_data.formatted()}")
    if hasattr(request.node, "rep_call"):  # make available for test reports
        request.node.rep_call.timings = total_timing_data


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("total_timing_data")
def client_genesis(fixture: BlockchainFixtureCommon) -> dict:
    """Convert the fixture genesis block header and pre-state to a client genesis state."""
    genesis = to_json(fixture.genesis)
    alloc = to_json(fixture.pre)
    # NOTE: nethermind requires account keys without '0x' prefix
    genesis["alloc"] = {k.replace("0x", ""): v for k, v in alloc.items()}
    return genesis


@pytest.fixture(scope="function")
def check_live_port(test_suite_name: str) -> Literal[8545, 8551]:
    """Port used by hive to check for liveness of the client."""
    if test_suite_name == "eest/consume-rlp":
        return 8545
    elif test_suite_name == "eest/consume-engine":
        return 8551
    raise ValueError(
        f"Unexpected test suite name '{test_suite_name}' while setting HIVE_CHECK_LIVE_PORT."
    )


@pytest.fixture(scope="function")
def environment(
    fixture: BlockchainFixtureCommon,
    check_live_port: Literal[8545, 8551],
) -> dict:
    """Define the environment that hive will start the client with."""
    assert fixture.fork in ruleset, f"fork '{fixture.fork}' missing in hive ruleset"
    return {
        "HIVE_CHAIN_ID": str(Number(fixture.config.chain_id)),
        "HIVE_FORK_DAO_VOTE": "1",
        "HIVE_NODETYPE": "full",
        "HIVE_CHECK_LIVE_PORT": str(check_live_port),
        **{k: f"{v:d}" for k, v in ruleset[fixture.fork].items()},
    }


@pytest.fixture(scope="function")
def buffered_genesis(client_genesis: dict) -> io.BufferedReader:
    """Create a buffered reader for the genesis block header of the current test fixture."""
    genesis_json = json.dumps(client_genesis)
    genesis_bytes = genesis_json.encode("utf-8")
    return io.BufferedReader(cast(io.RawIOBase, io.BytesIO(genesis_bytes)))


@pytest.fixture(scope="function")
def client(
    hive_test: HiveTest,
    client_files: dict,  # configured within: rlp/conftest.py & engine/conftest.py
    environment: dict,
    client_type: ClientType,
    total_timing_data: TimingData,
) -> Generator[Client, None, None]:
    """Initialize the client with the appropriate files and environment variables."""
    with total_timing_data.time("Start client"):
        client = hive_test.start_client(
            client_type=client_type, environment=environment, files=client_files
        )
    error_message = (
        f"Unable to connect to the client container ({client_type.name}) via Hive during test "
        "setup. Check the client or Hive server logs for more information."
    )
    assert client is not None, error_message
    yield client
    with total_timing_data.time("Stop client"):
        client.stop()


@pytest.fixture(scope="function", autouse=True)
def timing_data(
    total_timing_data: TimingData, client: Client
) -> Generator[TimingData, None, None]:
    """Record timing data for the main execution of the test case."""
    with total_timing_data.time("Test case execution") as timing_data:
        yield timing_data


class FixturesDict(Dict[Path, Fixtures]):
    """
    A dictionary caches loaded fixture files to avoid reloading the same file
    multiple times.
    """

    def __init__(self) -> None:
        """Initialize the dictionary that caches loaded fixture files."""
        self._fixtures: Dict[Path, Fixtures] = {}

    def __getitem__(self, key: Path) -> Fixtures:
        """Return the fixtures from the index file, if not found, load from disk."""
        assert key.is_file(), f"Expected a file path, got '{key}'"
        if key not in self._fixtures:
            self._fixtures[key] = Fixtures.model_validate_json(key.read_text())
        return self._fixtures[key]


@pytest.fixture(scope="session")
def fixture_file_loader() -> Dict[Path, Fixtures]:
    """Return a singleton dictionary that caches loaded fixture files used in all tests."""
    return FixturesDict()


@pytest.fixture(scope="function")
def fixture(
    fixtures_source: FixturesSource,
    fixture_file_loader: Dict[Path, Fixtures],
    test_case: TestCaseIndexFile | TestCaseStream,
) -> BaseFixture:
    """
    Load the fixture from a file or from stream in any of the supported
    fixture formats.

    The fixture is either already available within the test case (if consume
    is taking input on stdin) or loaded from the fixture json file if taking
    input from disk (fixture directory with index file).
    """
    fixture: BaseFixture
    if fixtures_source.is_stdin:
        assert isinstance(test_case, TestCaseStream), "Expected a stream test case"
        fixture = test_case.fixture
    else:
        assert isinstance(test_case, TestCaseIndexFile), "Expected an index file test case"
        fixtures_file_path = fixtures_source.path / test_case.json_path
        fixtures: Fixtures = fixture_file_loader[fixtures_file_path]
        fixture = fixtures[test_case.id]
    assert isinstance(fixture, test_case.format), (
        f"Expected a {test_case.format.format_name} test fixture"
    )
    return fixture
