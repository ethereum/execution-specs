"""
Common pytest fixtures for the RLP and Engine simulators.
"""

import io
import json
from typing import Generator, List, cast

import pytest
import rich
from hive.client import Client, ClientType
from hive.testing import HiveTest

from ethereum_test_base_types import to_json
from ethereum_test_fixtures import BlockchainFixtureCommon
from ethereum_test_fixtures.consume import TestCaseIndexFile, TestCaseStream
from ethereum_test_rpc import EthRPC
from pytest_plugins.consume.hive_simulators.ruleset import ruleset  # TODO: generate dynamically

from .timing import TimingData


def pytest_addoption(parser):
    """
    Hive simulator specific consume command line options.
    """
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
    """
    Initialize ethereum RPC client for the execution client under test.
    """
    return EthRPC(f"http://{client.ip}:8545")


@pytest.fixture(scope="function")
def hive_consume_command(
    test_suite_name: str,
    client_type: ClientType,
    test_case: TestCaseIndexFile | TestCaseStream,
) -> str:
    """
    Command to run the test within hive.
    """
    return (
        f"./hive --sim ethereum/{test_suite_name} "
        f"--client-file configs/develop.yaml "
        f"--client {client_type.name} "
        f'--sim.limit "{test_case.id}"'
    )


@pytest.fixture(scope="function")
def eest_consume_commands(
    test_suite_name: str,
    client_type: ClientType,
    test_case: TestCaseIndexFile | TestCaseStream,
) -> List[str]:
    """
    Commands to run the test within EEST using a hive dev back-end.
    """
    hive_dev = f"./hive --dev --client-file configs/develop.yaml --client {client_type.name}"
    consume = (
        f'consume {test_suite_name.split("-")[-1]} -v --input latest-develop-release -k '
        f'"{test_case.id}"'
    )
    return [hive_dev, consume]


@pytest.fixture(scope="function")
def fixture_description(
    blockchain_fixture: BlockchainFixtureCommon,
    test_case: TestCaseIndexFile | TestCaseStream,
    hive_consume_command: str,
    eest_consume_commands: List[str],
) -> str:
    """
    Create the description of the current blockchain fixture test case.
    Includes reproducible commands to re-run the test case against the target client.
    """
    description = f"Test id: {test_case.id}"
    if "url" in blockchain_fixture.info:
        description += f"\n\nTest source: {blockchain_fixture.info['url']}"
    if "description" not in blockchain_fixture.info:
        description += "\n\nNo description field provided in the fixture's 'info' section."
    else:
        description += f"\n\n{blockchain_fixture.info['description']}"
    description += (
        f"\n\nCommand to reproduce entirely in hive:" f"\n<code>{hive_consume_command}</code>"
    )
    eest_commands = "\n".join(
        f"{i+1}. <code>{cmd}</code>" for i, cmd in enumerate(eest_consume_commands)
    )
    description += (
        "\n\nCommands to reproduce within EEST using a hive dev back-end:" f"\n{eest_commands}"
    )
    description = description.replace("\n", "<br/>")
    return description


@pytest.fixture(scope="function", autouse=True)
def total_timing_data(request) -> Generator[TimingData, None, None]:
    """
    Helper to record timing data for various stages of executing test case.
    """
    with TimingData("Total (seconds)") as total_timing_data:
        yield total_timing_data
    if request.config.getoption("timing_data"):
        rich.print(f"\n{total_timing_data.formatted()}")
    if hasattr(request.node, "rep_call"):  # make available for test reports
        request.node.rep_call.timings = total_timing_data


@pytest.fixture(scope="function")
@pytest.mark.usefixtures("total_timing_data")
def client_genesis(blockchain_fixture: BlockchainFixtureCommon) -> dict:
    """
    Convert the fixture genesis block header and pre-state to a client genesis state.
    """
    genesis = to_json(blockchain_fixture.genesis)
    alloc = to_json(blockchain_fixture.pre)
    # NOTE: nethermind requires account keys without '0x' prefix
    genesis["alloc"] = {k.replace("0x", ""): v for k, v in alloc.items()}
    return genesis


@pytest.fixture(scope="function")
def environment(blockchain_fixture: BlockchainFixtureCommon) -> dict:
    """
    Define the environment that hive will start the client with using the fork
    rules specific for the simulator.
    """
    assert (
        blockchain_fixture.fork in ruleset
    ), f"fork '{blockchain_fixture.fork}' missing in hive ruleset"
    return {
        "HIVE_CHAIN_ID": "1",
        "HIVE_FORK_DAO_VOTE": "1",
        "HIVE_NODETYPE": "full",
        **{k: f"{v:d}" for k, v in ruleset[blockchain_fixture.fork].items()},
    }


@pytest.fixture(scope="function")
def buffered_genesis(client_genesis: dict) -> io.BufferedReader:
    """
    Create a buffered reader for the genesis block header of the current test
    fixture.
    """
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
    """
    Initialize the client with the appropriate files and environment variables.
    """
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
    """
    Helper to record timing data for the main execution of the test case.
    """
    with total_timing_data.time("Test case execution") as timing_data:
        yield timing_data
