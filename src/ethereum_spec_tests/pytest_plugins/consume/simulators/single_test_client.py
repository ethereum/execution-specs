"""Common pytest fixtures for simulators with single-test client architecture."""

import io
import json
import logging
from typing import Generator, Literal, cast

import pytest
from hive.client import Client, ClientType
from hive.testing import HiveTest

from ethereum_test_base_types import Number, to_json
from ethereum_test_fixtures import BlockchainFixtureCommon
from ethereum_test_fixtures.blockchain import FixtureHeader

from .helpers.ruleset import (
    ruleset,  # TODO: generate dynamically
)
from .helpers.timing import TimingData

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def client_genesis(fixture: BlockchainFixtureCommon) -> dict:
    """Convert the fixture genesis block header and pre-state to a client genesis state."""
    genesis = to_json(fixture.genesis)
    alloc = to_json(fixture.pre)
    # NOTE: nethermind requires account keys without '0x' prefix
    genesis["alloc"] = {k.replace("0x", ""): v for k, v in alloc.items()}
    return genesis


@pytest.fixture(scope="function")
def environment(
    fixture: BlockchainFixtureCommon,
    check_live_port: Literal[8545, 8551],
) -> dict:
    """Define the environment that hive will start the client with."""
    assert fixture.fork in ruleset, f"fork '{fixture.fork}' missing in hive ruleset"
    chain_id = str(Number(fixture.config.chain_id))
    return {
        "HIVE_CHAIN_ID": chain_id,
        "HIVE_NETWORK_ID": chain_id,  # Use same value for P2P network compatibility
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
def genesis_header(fixture: BlockchainFixtureCommon) -> FixtureHeader:
    """Provide the genesis header from the shared pre-state group."""
    return fixture.genesis  # type: ignore


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
    logger.debug(f"Main client Network ID: {environment.get('HIVE_NETWORK_ID', 'NOT SET!')}")
    logger.debug(f"Main client Chain ID: {environment.get('HIVE_CHAIN_ID', 'NOT SET!')}")
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
