"""
Pytest fixtures for the `consume sync` simulator.

Configures the hive back-end & EL clients for each individual test execution.
"""

import io
import json
from typing import Generator, Mapping, cast

import pytest
from hive.client import Client, ClientType
from hive.testing import HiveTest

from ethereum_test_base_types import to_json
from ethereum_test_exceptions import ExceptionMapper
from ethereum_test_fixtures import BlockchainEngineSyncFixture
from ethereum_test_rpc import AdminRPC, EngineRPC, EthRPC, NetRPC

pytest_plugins = (
    "pytest_plugins.pytest_hive.pytest_hive",
    "pytest_plugins.consume.simulators.base",
    "pytest_plugins.consume.simulators.single_test_client",
    "pytest_plugins.consume.simulators.test_case_description",
    "pytest_plugins.consume.simulators.timing_data",
    "pytest_plugins.consume.simulators.exceptions",
)


def pytest_configure(config):
    """Set the supported fixture formats for the engine sync simulator."""
    config._supported_fixture_formats = [BlockchainEngineSyncFixture.format_name]


def pytest_generate_tests(metafunc):
    """Parametrize sync_client_type separately from client_type."""
    if "sync_client_type" in metafunc.fixturenames:
        client_ids = [f"sync_{client.name}" for client in metafunc.config.hive_execution_clients]
        metafunc.parametrize(
            "sync_client_type", metafunc.config.hive_execution_clients, ids=client_ids
        )


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(session, config, items):
    """Modify test IDs to show both client and sync client clearly."""
    for item in items:
        # Check if this test has both client_type and sync_client_type
        if (
            hasattr(item, "callspec")
            and "client_type" in item.callspec.params
            and "sync_client_type" in item.callspec.params
        ):
            # Get the client names and remove fork suffix if present
            client_name = item.callspec.params["client_type"].name.replace("-", "_")
            sync_client_name = item.callspec.params["sync_client_type"].name.replace("-", "_")

            # Format: ``-{client}_sync_{sync_client}``
            new_suffix = f"-{client_name}::sync_{sync_client_name}"

            # client_param-tests/path/to/test.py::test_name[test_params]-sync_client_param
            # 1. Remove the client prefix from the beginning
            # 2. Replace the -client_param part at the end with our new format
            nodeid = item.nodeid
            prefix_index = item.nodeid.find("-tests/")
            if prefix_index != -1:
                nodeid = item.nodeid[prefix_index + 1 :]

            # Find the last hyphen followed by client name pattern and replace
            if "-" in nodeid:
                # Split by the last hyphen to separate the client suffix
                parts = nodeid.rsplit("]-", 1)
                assert len(parts) == 2, (
                    # expect "..._end_of_test]-client_name" suffix...
                    f"Unexpected format to parse client name: {nodeid}"
                )

                base = parts[0]
                if base.endswith("sync_test"):
                    # Insert suffix before the closing bracket
                    base = base + new_suffix + "]"
                    item._nodeid = base
                else:
                    item._nodeid = base + new_suffix


@pytest.fixture(scope="function")
def engine_rpc(client: Client, client_exception_mapper: ExceptionMapper | None) -> EngineRPC:
    """Initialize engine RPC client for the execution client under test."""
    if client_exception_mapper:
        return EngineRPC(
            f"http://{client.ip}:8551",
            response_validation_context={
                "exception_mapper": client_exception_mapper,
            },
        )
    return EngineRPC(f"http://{client.ip}:8551")


@pytest.fixture(scope="function")
def eth_rpc(client: Client) -> EthRPC:
    """Initialize eth RPC client for the execution client under test."""
    return EthRPC(f"http://{client.ip}:8545")


@pytest.fixture(scope="function")
def net_rpc(client: Client) -> NetRPC:
    """Initialize net RPC client for the execution client under test."""
    return NetRPC(f"http://{client.ip}:8545")


@pytest.fixture(scope="function")
def admin_rpc(client: Client) -> AdminRPC:
    """Initialize admin RPC client for the execution client under test."""
    return AdminRPC(f"http://{client.ip}:8545")


@pytest.fixture(scope="function")
def sync_genesis(fixture: BlockchainEngineSyncFixture) -> dict:
    """Convert the fixture genesis block header and pre-state to a sync client genesis state."""
    genesis = to_json(fixture.genesis)
    alloc = to_json(fixture.pre)
    # NOTE: nethermind requires account keys without '0x' prefix
    genesis["alloc"] = {k.replace("0x", ""): v for k, v in alloc.items()}
    return genesis


@pytest.fixture(scope="function")
def sync_buffered_genesis(sync_genesis: dict) -> io.BufferedReader:
    """Create a buffered reader for the genesis block header of the sync client."""
    genesis_json = json.dumps(sync_genesis)
    genesis_bytes = genesis_json.encode("utf-8")
    return io.BufferedReader(cast(io.RawIOBase, io.BytesIO(genesis_bytes)))


@pytest.fixture(scope="function")
def sync_client_files(sync_buffered_genesis: io.BufferedReader) -> Mapping[str, io.BufferedReader]:
    """Define the files that hive will start the sync client with."""
    files = {}
    files["/genesis.json"] = sync_buffered_genesis
    return files


@pytest.fixture(scope="function")
def client_enode_url(client: Client) -> str:
    """Get the enode URL from the client under test."""
    import logging

    logger = logging.getLogger(__name__)

    enode = client.enode()
    logger.info(f"Client enode object: {enode}")

    # Build the enode URL string with container IP
    enode_url = f"enode://{enode.id}@{client.ip}:{enode.port}"
    logger.info(f"Client enode URL: {enode_url}")
    return enode_url


@pytest.fixture(scope="function")
def sync_client(
    hive_test: HiveTest,
    client: Client,  # The main client under test
    sync_client_files: dict,
    environment: dict,
    sync_client_type: ClientType,  # Separate parametrization for sync client
    client_enode_url: str,  # Get the enode URL from fixture
) -> Generator[Client, None, None]:
    """Start a sync client that will sync from the client under test."""
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Starting sync client setup for {sync_client_type.name}")

    # Start with the same environment as the main client
    sync_environment = environment.copy()

    # Only override what's necessary for sync client
    sync_environment["HIVE_MINER"] = ""  # Disable mining on sync client

    # Set bootnode even though we also use admin_addPeer
    # Some clients use this for initial P2P configuration
    sync_environment["HIVE_BOOTNODE"] = client_enode_url

    # Ensure both network and chain IDs are properly set
    if "HIVE_NETWORK_ID" not in sync_environment and "HIVE_CHAIN_ID" in sync_environment:
        # Some clients need explicit HIVE_NETWORK_ID
        sync_environment["HIVE_NETWORK_ID"] = sync_environment["HIVE_CHAIN_ID"]

    logger.info(f"Starting sync client ({sync_client_type.name})")
    logger.info(f"  Network ID: {sync_environment.get('HIVE_NETWORK_ID', 'NOT SET!')}")
    logger.info(f"  Chain ID: {sync_environment.get('HIVE_CHAIN_ID', 'NOT SET!')}")

    # Debug: log all HIVE_ variables
    hive_vars = {k: v for k, v in sync_environment.items() if k.startswith("HIVE_")}
    logger.debug(f"All HIVE_ environment variables: {hive_vars}")

    # Use the separately parametrized sync client type
    sync_client = hive_test.start_client(
        client_type=sync_client_type,
        environment=sync_environment,
        files=sync_client_files,
    )

    error_message = (
        f"Unable to start sync client ({sync_client_type.name}) via Hive. "
        "Check the client or Hive server logs for more information."
    )
    assert sync_client is not None, error_message

    logger.info(f"Sync client ({sync_client_type.name}) started with IP: {sync_client.ip}")

    yield sync_client

    # Cleanup
    sync_client.stop()


@pytest.fixture(scope="function")
def sync_client_exception_mapper(
    sync_client_type: ClientType, client_exception_mapper_cache
) -> ExceptionMapper | None:
    """Return the exception mapper for the sync client type, with caching."""
    if sync_client_type.name not in client_exception_mapper_cache:
        from ..exceptions import EXCEPTION_MAPPERS

        for client in EXCEPTION_MAPPERS:
            if client in sync_client_type.name:
                client_exception_mapper_cache[sync_client_type.name] = EXCEPTION_MAPPERS[client]
                break
        else:
            client_exception_mapper_cache[sync_client_type.name] = None

    return client_exception_mapper_cache[sync_client_type.name]


@pytest.fixture(scope="function")
def sync_engine_rpc(
    sync_client: Client, sync_client_exception_mapper: ExceptionMapper | None
) -> EngineRPC:
    """Initialize engine RPC client for the sync client."""
    if sync_client_exception_mapper:
        return EngineRPC(
            f"http://{sync_client.ip}:8551",
            response_validation_context={
                "exception_mapper": sync_client_exception_mapper,
            },
        )
    return EngineRPC(f"http://{sync_client.ip}:8551")


@pytest.fixture(scope="function")
def sync_eth_rpc(sync_client: Client) -> EthRPC:
    """Initialize eth RPC client for the sync client."""
    return EthRPC(f"http://{sync_client.ip}:8545")


@pytest.fixture(scope="function")
def sync_net_rpc(sync_client: Client) -> NetRPC:
    """Initialize net RPC client for the sync client."""
    return NetRPC(f"http://{sync_client.ip}:8545")


@pytest.fixture(scope="function")
def sync_admin_rpc(sync_client: Client) -> AdminRPC:
    """Initialize admin RPC client for the sync client."""
    return AdminRPC(f"http://{sync_client.ip}:8545")


@pytest.fixture(scope="module")
def test_suite_name() -> str:
    """The name of the hive test suite used in this simulator."""
    return "eest/consume-sync"


@pytest.fixture(scope="module")
def test_suite_description() -> str:
    """The description of the hive test suite used in this simulator."""
    return "Execute blockchain sync tests against clients using the Engine API."


@pytest.fixture(scope="function")
def client_files(buffered_genesis: io.BufferedReader) -> Mapping[str, io.BufferedReader]:
    """Define the files that hive will start the client with."""
    files = {}
    files["/genesis.json"] = buffered_genesis
    return files
