"""
Pytest fixtures for the `consume reorg` simulator.

One fresh client per fixture; the client environment is the standard engine
environment plus the fixture's ``requires`` (``HIVE_*``) variables, if any.
Additional clients declared in ``fixture.clients`` are started with the same
client type and peered with the main client (bootnode + ``admin_addPeer``).
"""

import io
import json
import logging
import time
from contextlib import ExitStack
from typing import Any, Dict, Generator, Literal, Mapping

import pytest
from hive.client import Client, ClientType
from hive.testing import HiveTest

from execution_testing.exceptions import ExceptionMapper
from execution_testing.fixtures import BlockchainEngineReorgFixture
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.rpc import AdminRPC, EngineRPC, EthRPC

from ..helpers.timing import TimingData
from ..simulator_logic.test_via_reorg import ClientRPC
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


@pytest.fixture(scope="function")
def peer_rpcs(
    request: pytest.FixtureRequest,
    fixture: BlockchainEngineReorgFixture,
    hive_test: HiveTest,
    client: Client,
    client_type: ClientType,
    client_genesis: dict,
    environment: dict,
    client_exception_mapper: ExceptionMapper | None,
    total_timing_data: TimingData,
) -> Generator[Dict[str, ClientRPC], None, None]:
    """
    Start the fixture's additional clients (same client type as ``main``),
    peered with the main client, and expose their RPC endpoints by name.
    """
    if not fixture.clients:
        yield {}
        return

    enode = client.enode()
    main_enode = f"enode://{enode.id}@{client.ip}:{enode.port}"
    peer_env = dict(environment)
    peer_env["HIVE_MINER"] = ""
    peer_env["HIVE_BOOTNODE"] = main_enode

    peers: Dict[str, Client] = {}
    rpcs: Dict[str, ClientRPC] = {}
    with ExitStack() as stack:
        for name in fixture.clients:
            genesis_bytes = json.dumps(client_genesis).encode("utf-8")
            files = {
                "/genesis.json": io.BufferedReader(io.BytesIO(genesis_bytes))
            }
            with total_timing_data.time(f"Start peer {name}"):
                peer = hive_test.start_client(
                    client_type=client_type, environment=peer_env, files=files
                )
            assert peer is not None, f"Unable to start peer client {name!r}"
            peers[name] = peer
            eth = stack.enter_context(EthRPC(f"http://{peer.ip}:8545"))
            engine_kwargs: Dict[str, Any] = (
                {
                    "response_validation_context": {
                        "exception_mapper": client_exception_mapper
                    }
                }
                if client_exception_mapper
                else {}
            )
            engine = stack.enter_context(
                EngineRPC(f"http://{peer.ip}:8551", **engine_kwargs)
            )
            rpcs[name] = ClientRPC(name, eth, engine)
            with AdminRPC(f"http://{peer.ip}:8545") as admin:
                try:
                    admin.add_peer(main_enode)
                except Exception as e:  # noqa: BLE001 - best effort
                    logger.warning(f"admin_addPeer on {name} failed: {e}")
            logger.info(
                f"Peer {name} ({client_type.name}) started at {peer.ip}"
            )
        yield rpcs
        result_call = getattr(request.node, "result_call", None)
        if result_call is not None and result_call.failed:
            time.sleep(1)
        for name, peer in peers.items():
            with total_timing_data.time(f"Stop peer {name}"):
                peer.stop()
