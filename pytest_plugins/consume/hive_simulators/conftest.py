"""Common pytest fixtures for the RLP and Engine simulators."""

import io
import json
import logging
import textwrap
import urllib
import warnings
from pathlib import Path
from typing import Dict, Generator, List, Literal, cast

import pytest
import rich
from hive.client import Client, ClientType
from hive.testing import HiveTest

from ethereum_test_base_types import Number, to_json
from ethereum_test_exceptions import ExceptionMapper
from ethereum_test_fixtures import (
    BaseFixture,
    BlockchainFixtureCommon,
)
from ethereum_test_fixtures.consume import TestCaseIndexFile, TestCaseStream
from ethereum_test_fixtures.file import Fixtures
from ethereum_test_rpc import EthRPC
from pytest_plugins.consume.consume import FixturesSource
from pytest_plugins.consume.hive_simulators.ruleset import ruleset  # TODO: generate dynamically
from pytest_plugins.pytest_hive.hive_info import ClientFile, HiveInfo

from .exceptions import EXCEPTION_MAPPERS
from .timing import TimingData

logger = logging.getLogger(__name__)


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
    consume_group.addoption(
        "--disable-strict-exception-matching",
        action="store",
        dest="disable_strict_exception_matching",
        default="",
        help=(
            "Comma-separated list of client names and/or forks which should NOT use strict "
            "exception matching."
        ),
    )


@pytest.fixture(scope="function")
def eth_rpc(client: Client) -> EthRPC:
    """Initialize ethereum RPC client for the execution client under test."""
    return EthRPC(f"http://{client.ip}:8545")


@pytest.fixture(scope="function")
def hive_clients_yaml_target_filename() -> str:
    """Return the name of the target clients YAML file."""
    return "clients_eest.yaml"


@pytest.fixture(scope="function")
def hive_clients_yaml_generator_command(
    client_type: ClientType,
    client_file: ClientFile,
    hive_clients_yaml_target_filename: str,
    hive_info: HiveInfo,
) -> str:
    """Generate a shell command that creates a clients YAML file for the current client."""
    try:
        if not client_file:
            raise ValueError("No client information available - try updating hive")
        client_config = [c for c in client_file.root if c.client in client_type.name]
        if not client_config:
            raise ValueError(f"Client '{client_type.name}' not found in client file")
        try:
            yaml_content = ClientFile(root=[client_config[0]]).yaml().replace(" ", "&nbsp;")
            return f'echo "\\\n{yaml_content}" > {hive_clients_yaml_target_filename}'
        except Exception as e:
            raise ValueError(f"Failed to generate YAML: {str(e)}") from e
    except ValueError as e:
        error_message = str(e)
        warnings.warn(
            f"{error_message}. The Hive clients YAML generator command will not be available.",
            stacklevel=2,
        )

        issue_title = f"Client {client_type.name} configuration issue"
        issue_body = f"Error: {error_message}\nHive version: {hive_info.commit}\n"
        issue_url = f"https://github.com/ethereum/execution-spec-tests/issues/new?title={urllib.parse.quote(issue_title)}&body={urllib.parse.quote(issue_body)}"

        return (
            f"Error: {error_message}\n"
            f'Please <a href="{issue_url}">create an issue</a> to report this problem.'
        )


@pytest.fixture(scope="function")
def filtered_hive_options(hive_info: HiveInfo) -> List[str]:
    """Filter Hive command options to remove unwanted options."""
    logger.info("Hive info: %s", hive_info.command)

    unwanted_options = [
        "--client",  # gets overwritten: we specify a single client; the one from the test case
        "--client-file",  # gets overwritten: we'll write our own client file
        "--results-root",  # use default value instead (or you have to pass it to ./hiveview)
        "--sim.limit",  # gets overwritten: we only run the current test case id
        "--sim.parallelism",  # skip; we'll only be running a single test
    ]

    command_parts = []
    skip_next = False
    for part in hive_info.command:
        if skip_next:
            skip_next = False
            continue

        if part in unwanted_options:
            skip_next = True
            continue

        if any(part.startswith(f"{option}=") for option in unwanted_options):
            continue

        command_parts.append(part)

    return command_parts


@pytest.fixture(scope="function")
def hive_client_config_file_parameter(hive_clients_yaml_target_filename: str) -> str:
    """Return the hive client config file parameter."""
    return f"--client-file {hive_clients_yaml_target_filename}"


@pytest.fixture(scope="function")
def hive_consume_command(
    test_case: TestCaseIndexFile | TestCaseStream,
    hive_client_config_file_parameter: str,
    filtered_hive_options: List[str],
    client_type: ClientType,
) -> str:
    """Command to run the test within hive."""
    command_parts = filtered_hive_options.copy()
    command_parts.append(f"{hive_client_config_file_parameter}")
    command_parts.append(f"--client={client_type.name}")
    command_parts.append(f'--sim.limit="id:{test_case.id}"')

    return " ".join(command_parts)


@pytest.fixture(scope="function")
def hive_dev_command(
    client_type: ClientType,
    hive_client_config_file_parameter: str,
) -> str:
    """Return the command used to instantiate hive alongside the `consume` command."""
    return f"./hive --dev {hive_client_config_file_parameter} --client {client_type.name}"


@pytest.fixture(scope="function")
def eest_consume_command(
    test_suite_name: str,
    test_case: TestCaseIndexFile | TestCaseStream,
    fixture_source_flags: List[str],
) -> str:
    """Commands to run the test within EEST using a hive dev back-end."""
    flags = " ".join(fixture_source_flags)
    return (
        f"uv run consume {test_suite_name.split('-')[-1]} "
        f'{flags} --sim.limit="id:{test_case.id}" -v -s'
    )


@pytest.fixture(scope="function")
def test_case_description(
    fixture: BaseFixture,
    test_case: TestCaseIndexFile | TestCaseStream,
    hive_clients_yaml_generator_command: str,
    hive_consume_command: str,
    hive_dev_command: str,
    eest_consume_command: str,
) -> str:
    """Create the description of the current blockchain fixture test case."""
    test_url = fixture.info.get("url", "")

    if "description" not in fixture.info or fixture.info["description"] is None:
        test_docstring = "No documentation available."
    else:
        # this prefix was included in the fixture description field for fixtures <= v4.3.0
        test_docstring = fixture.info["description"].replace("Test function documentation:\n", "")  # type: ignore

    description = textwrap.dedent(f"""
        <b>Test Details</b>
        <code>{test_case.id}</code>
        {f'<a href="{test_url}">[source]</a>' if test_url else ""}

        {test_docstring}

        <b>Run This Test Locally:</b>
        To run this test in <a href="https://github.com/ethereum/hive">hive</a></i>:
        <code>{hive_clients_yaml_generator_command}
            {hive_consume_command}</code>

        <b>Advanced: Run the test against a hive developer backend using EEST's <code>consume</code> command</b>
        Create the client YAML file, as above, then:
        1. Start hive in dev mode: <code>{hive_dev_command}</code>
        2. In the EEST repository root: <code>{eest_consume_command}</code>
    """)  # noqa: E501

    description = description.strip()
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


@pytest.fixture(scope="session")
def client_exception_mapper_cache():
    """Cache for exception mappers by client type."""
    return {}


@pytest.fixture(scope="function")
def client_exception_mapper(
    client_type: ClientType, client_exception_mapper_cache
) -> ExceptionMapper | None:
    """Return the exception mapper for the client type, with caching."""
    if client_type.name not in client_exception_mapper_cache:
        for client in EXCEPTION_MAPPERS:
            if client in client_type.name:
                client_exception_mapper_cache[client_type.name] = EXCEPTION_MAPPERS[client]
                break
        else:
            client_exception_mapper_cache[client_type.name] = None

    return client_exception_mapper_cache[client_type.name]


@pytest.fixture(scope="session")
def disable_strict_exception_matching(request: pytest.FixtureRequest) -> List[str]:
    """Return the list of clients or forks that should NOT use strict exception matching."""
    config_string = request.config.getoption("disable_strict_exception_matching")
    return config_string.split(",") if config_string else []


@pytest.fixture(scope="function")
def client_strict_exception_matching(
    client_type: ClientType,
    disable_strict_exception_matching: List[str],
) -> bool:
    """Return True if the client type should use strict exception matching."""
    return not any(
        client.lower() in client_type.name.lower() for client in disable_strict_exception_matching
    )


@pytest.fixture(scope="function")
def fork_strict_exception_matching(
    fixture: BlockchainFixtureCommon,
    disable_strict_exception_matching: List[str],
) -> bool:
    """Return True if the fork should use strict exception matching."""
    # NOTE: `in` makes it easier for transition forks ("Prague" in "CancunToPragueAtTime15k")
    return not any(
        fork.lower() in fixture.fork.lower() for fork in disable_strict_exception_matching
    )


@pytest.fixture(scope="function")
def strict_exception_matching(
    client_strict_exception_matching: bool,
    fork_strict_exception_matching: bool,
) -> bool:
    """Return True if the test should use strict exception matching."""
    return client_strict_exception_matching and fork_strict_exception_matching


@pytest.fixture(scope="function")
def client(
    hive_test: HiveTest,
    client_files: dict,  # configured within: rlp/conftest.py & engine/conftest.py
    environment: dict,
    client_type: ClientType,
    total_timing_data: TimingData,
) -> Generator[Client, None, None]:
    """Initialize the client with the appropriate files and environment variables."""
    logger.info(f"Starting client ({client_type.name})...")
    with total_timing_data.time("Start client"):
        client = hive_test.start_client(
            client_type=client_type, environment=environment, files=client_files
        )
    error_message = (
        f"Unable to connect to the client container ({client_type.name}) via Hive during test "
        "setup. Check the client or Hive server logs for more information."
    )
    assert client is not None, error_message
    logger.info(f"Client ({client_type.name}) ready!")
    yield client
    logger.info(f"Stopping client ({client_type.name})...")
    with total_timing_data.time("Stop client"):
        client.stop()
    logger.info(f"Client ({client_type.name}) stopped!")


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
