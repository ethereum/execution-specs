"""Pytest fixtures for multi-test client architecture."""

import io
import json
import logging
import time
from typing import TYPE_CHECKING, Generator, cast

import pytest
from hive.client import Client, ClientType
from hive.testing import HiveTest

from execution_testing.base_types import to_json
from execution_testing.fixtures import (
    BlockchainEngineXFixture,
    PreAllocGroup,
)
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.test_types import AllocGroupHash

from ..consume import FixturesSource
from .helpers.ruleset import ruleset
from .helpers.test_tracker import (
    PreAllocGroupTestTracker,
    make_group_identifier,
)

if TYPE_CHECKING:
    from .timing_data import TimingData

logger = logging.getLogger(__name__)


class MultiTestClientManager:
    """
    Session-scoped manager for client lifecycle across multiple tests.

    Coordinate client reuse across tests sharing the same
    pre-allocation group, enabling efficient test execution
    by avoiding redundant client restarts.
    """

    def __init__(self) -> None:
        """Initialize the multi-test client manager."""
        self.clients: dict[str, Client] = {}  # group_identifier -> Client
        self.test_tracker: PreAllocGroupTestTracker | None = None
        logger.debug("MultiTestClientManager initialized")

    def set_test_tracker(self, tracker: PreAllocGroupTestTracker) -> None:
        """
        Set the test tracker for automatic client cleanup.

        """
        self.test_tracker = tracker
        logger.debug("Test tracker registered with MultiTestClientManager")

    def get_client(self, group_identifier: str) -> Client | None:
        """
        Get the client instance for a group.

        """
        if group_identifier in self.clients:
            logger.debug(f"Found existing client for group {group_identifier}")
            return self.clients[group_identifier]

        logger.debug(f"No existing client for group {group_identifier}")
        return None

    def register_client(self, group_identifier: str, client: Client) -> None:
        """
        Register a newly started client for a group.

        """
        if group_identifier in self.clients:
            raise RuntimeError(
                f"Client already exists for group {group_identifier}"
            )

        self.clients[group_identifier] = client
        logger.info(f"Registered client for group {group_identifier}")

    def discard_client(self, group_identifier: str) -> None:
        """
        Stop and forget a group's client so the next request for the
        group starts a fresh one under the same identifier.

        The test tracker is untouched: the group's completed tests
        stay counted, and the replacement client registered after this
        call is the one stopped when the group completes.
        """
        client = self.clients.pop(group_identifier, None)
        if client is None:
            return
        logger.info(f"🛑 Discarding client for group {group_identifier}")
        try:
            client.stop()
        except Exception as e:
            logger.error(
                f"Error stopping discarded client for group "
                f"{group_identifier}: {e}"
            )

    def mark_test_completed(self, group_identifier: str, test_id: str) -> None:
        """
        Mark a test as completed and trigger cleanup.

        """
        if self.test_tracker is None:
            logger.warning(
                "Test tracker not set, cannot perform automatic cleanup"
            )
            return

        is_group_complete = self.test_tracker.mark_test_completed(
            group_identifier, test_id
        )

        # Stop the client immediately when all tests in the group are complete
        if is_group_complete:
            logger.info(f"✓ Group {group_identifier} complete")
            if group_identifier in self.clients:
                client = self.clients[group_identifier]
                try:
                    logger.info(
                        f"🛑 Stopping client for group {group_identifier}"
                    )
                    start = time.perf_counter()
                    client.stop()
                    logger.info(
                        f"⏱ phase=client_stop group={group_identifier} "
                        f"ms={(time.perf_counter() - start) * 1000:.1f}"
                    )
                except Exception as e:
                    logger.error(
                        "Error stopping client for group "
                        f"{group_identifier}: {e}"
                    )
                finally:
                    # Always remove from tracking, even if stop failed
                    del self.clients[group_identifier]

    def stop_all_clients(self) -> None:
        """Stop all remaining clients (called at session end)."""
        if not self.clients:
            logger.info("No clients to clean up")
            return

        logger.info(f"Stopping {len(self.clients)} remaining client(s)...")
        for group_identifier, client in list(self.clients.items()):
            try:
                logger.info(f"Stopping client for group {group_identifier}")
                client.stop()
            except Exception as e:
                logger.error(
                    f"Error stopping client for group {group_identifier}: {e}"
                )

        self.clients.clear()
        logger.info("All clients stopped")


@pytest.fixture(scope="session")
def multi_test_client_manager() -> Generator[
    MultiTestClientManager, None, None
]:
    """
    Provide session-scoped MultiTestClientManager with automatic cleanup.

    """
    manager = MultiTestClientManager()
    try:
        yield manager
    finally:
        logger.info("Session ending, cleaning up multi-test clients...")
        manager.stop_all_clients()


@pytest.fixture(scope="session")
def pre_alloc_group_cache() -> dict[AllocGroupHash, PreAllocGroup]:
    """Cache for pre-allocation groups to avoid reloading from disk."""
    return {}


@pytest.fixture(scope="session")
def client_genesis_cache() -> dict[AllocGroupHash, dict]:
    """Cache for client genesis configs to avoid redundant to_json calls."""
    return {}


@pytest.fixture(scope="session")
def environment_cache() -> dict[AllocGroupHash, dict]:
    """Cache for environment configs to avoid redundant computation."""
    return {}


@pytest.fixture(scope="function")
def pre_alloc_group(
    fixture: BlockchainEngineXFixture,
    fixtures_source: FixturesSource,
    pre_alloc_group_cache: dict[AllocGroupHash, PreAllocGroup],
) -> PreAllocGroup:
    """Load the pre-allocation group for the current test case."""
    pre_hash = fixture.pre_hash

    # Check cache first
    if pre_hash in pre_alloc_group_cache:
        logger.debug(f"Using cached pre-alloc group for {pre_hash}")
        return pre_alloc_group_cache[pre_hash]

    # Load from disk
    if fixtures_source.is_stdin:
        raise ValueError(
            "Pre-allocation groups require file-based fixture input"
        )

    # Look for pre-allocation group file
    pre_alloc_path = (
        fixtures_source.path
        / "blockchain_tests_engine_x"
        / "pre_alloc"
        / f"{pre_hash}.json"
    )

    if not pre_alloc_path.exists():
        raise FileNotFoundError(
            f"Pre-allocation group file not found: {pre_alloc_path}"
        )

    # Load and cache
    logger.debug(f"Loading pre-alloc group from {pre_alloc_path}")
    start = time.perf_counter()
    pre_alloc_group_obj = PreAllocGroup.from_file(pre_alloc_path)

    pre_alloc_group_cache[pre_hash] = pre_alloc_group_obj
    logger.info(
        f"⏱ phase=pre_alloc_load group={pre_hash} "
        f"ms={(time.perf_counter() - start) * 1000:.1f}"
    )

    return pre_alloc_group_obj


@pytest.fixture(scope="function")
def client_genesis(
    pre_alloc_group: PreAllocGroup,
    fixture: BlockchainEngineXFixture,
    client_genesis_cache: dict[AllocGroupHash, dict],
) -> dict:
    """
    Convert pre-alloc group genesis header and pre-state to client genesis.

    Parallel to single_test_client.client_genesis but uses
    PreAllocGroup. Use caching to avoid redundant to_json calls
    for tests sharing the same pre_hash.
    """
    pre_hash = fixture.pre_hash

    if pre_hash in client_genesis_cache:
        return client_genesis_cache[pre_hash]

    start = time.perf_counter()
    genesis = to_json(pre_alloc_group.genesis)
    alloc = to_json(pre_alloc_group.pre)
    # NOTE: nethermind requires account keys without '0x' prefix
    genesis["alloc"] = {k.replace("0x", ""): v for k, v in alloc.items()}

    client_genesis_cache[pre_hash] = genesis
    logger.info(
        f"⏱ phase=genesis_prep group={pre_hash} "
        f"ms={(time.perf_counter() - start) * 1000:.1f}"
    )
    return genesis


@pytest.fixture(scope="function")
def environment(
    pre_alloc_group: PreAllocGroup,
    fixture: BlockchainEngineXFixture,
    check_live_port: int,
    environment_cache: dict[AllocGroupHash, dict],
) -> dict:
    """
    Define environment variables for multi-test client startup.

    Parallel to single_test_client.environment but uses
    PreAllocGroup. Use caching to avoid redundant computation
    for tests sharing the same pre_hash.
    """
    pre_hash = fixture.pre_hash

    if pre_hash in environment_cache:
        return environment_cache[pre_hash]

    fork = pre_alloc_group.fork
    assert fork in ruleset, f"fork '{fork}' missing in hive ruleset"
    env = {
        "HIVE_CHAIN_ID": "1",
        "HIVE_NETWORK_ID": "1",
        "HIVE_FORK_DAO_VOTE": "1",
        "HIVE_NODETYPE": "full",
        "HIVE_CHECK_LIVE_PORT": str(check_live_port),
        **{k: f"{v:d}" for k, v in ruleset[fork].items()},
        "HIVE_FORK": pre_alloc_group.fork.name(),
        # Tell client wrapper scripts this workload performs deep reorgs:
        # clients are reused across a group's tests with a rewind to genesis
        # in between, so wrappers can raise client-specific limits that would
        # otherwise reject them (e.g. geth's engine API max reorg depth).
        "HIVE_EXPECT_DEEP_REORGS": "1",
    }

    environment_cache[pre_hash] = env
    return env


@pytest.fixture(scope="session", autouse=True)
def _configure_client_manager(
    multi_test_client_manager: MultiTestClientManager,
    pre_alloc_group_test_tracker: PreAllocGroupTestTracker,
) -> None:
    """Wire the test tracker to the client manager at session start."""
    multi_test_client_manager.set_test_tracker(pre_alloc_group_test_tracker)


@pytest.fixture(scope="function", autouse=True)
def _per_test_reporting(
    client: Client,
    hive_test: HiveTest,
) -> None:
    """
    Register a test for execution against a multi-test client.

    Activate log segment capturing in the Hive backend for correct
    client log reporting in the multi-test client case.

    Parameter order matters: `client` listed before `hive_test`
    ensures pytest sets up `client` first and tears it down last.
    This guarantees `hive_test` teardown (`test.end()`) runs while
    the hive node still exists, before `client` teardown calls
    `mark_test_completed` / `client.stop()`.
    """
    hive_test.register_multi_test_client(client)


def boot_managed_client(
    multi_test_hive_test: HiveTest,
    multi_test_client_manager: MultiTestClientManager,
    identifier: str,
    client_type: ClientType,
    environment: dict,
    client_genesis: dict,
    total_timing_data: "TimingData",
) -> Client:
    """
    Start a client and register it with the manager under `identifier`.

    The identifier is usually a pre-allocation group's, but a simulator
    may register a client under any unique key (`consume wirex` boots
    one isolated client per sync target of a multi-target fixture); the
    manager's session-end cleanup covers every registered client either
    way.
    """
    serialize_start = time.perf_counter()
    genesis_bytes = json.dumps(client_genesis).encode("utf-8")
    buffered_genesis = io.BufferedReader(
        cast(io.RawIOBase, io.BytesIO(genesis_bytes))
    )
    logger.info(
        f"⏱ phase=genesis_serialize group={identifier} "
        f"ms={(time.perf_counter() - serialize_start) * 1000:.1f}"
    )

    logger.info(f"🚀 Starting client ({client_type.name}) for {identifier}")

    start_requested = time.perf_counter()
    with total_timing_data.time("Start client"):
        resolved_client = multi_test_hive_test.start_client(
            client_type=client_type,
            environment=environment,
            files={"/genesis.json": buffered_genesis},
        )

    assert resolved_client is not None, (
        f"Unable to connect to client ({client_type.name}) via "
        "Hive. Check the client or Hive server logs for more "
        "information."
    )

    # The hive start-client API only returns once the client answers its
    # liveness check, so this spans container creation, boot and that wait.
    logger.info(
        f"⏱ phase=client_start group={identifier} "
        f"ms={(time.perf_counter() - start_requested) * 1000:.1f}"
    )
    logger.info(f"Client ({client_type.name}) ready for {identifier}")

    multi_test_client_manager.register_client(identifier, resolved_client)
    resolved_client.multi_test = True
    return resolved_client


def group_client(
    multi_test_hive_test: HiveTest,
    multi_test_client_manager: MultiTestClientManager,
    fixture: BlockchainEngineXFixture,
    client_type: ClientType,
    environment: dict,
    client_genesis: dict,
    total_timing_data: "TimingData",
    request: pytest.FixtureRequest,
) -> Generator[Client, None, None]:
    """
    Get or create a multi-test client for this pre-allocation group.

    The body of the `client` fixture, callable so a simulator with its
    own replacement policy (`consume wirex` discards a client whose
    head sits above a rejection target) can wrap it in an overriding
    fixture instead of duplicating the lifecycle logic.
    """
    group_identifier = make_group_identifier(
        fixture.pre_hash, client_type.name
    )
    test_id = request.node.nodeid

    resolved_client = multi_test_client_manager.get_client(group_identifier)
    if resolved_client is not None:
        logger.info(f"♻️  Reusing client for group {group_identifier}")
    else:
        resolved_client = boot_managed_client(
            multi_test_hive_test,
            multi_test_client_manager,
            group_identifier,
            client_type,
            environment,
            client_genesis,
            total_timing_data,
        )
    try:
        yield resolved_client
    finally:
        multi_test_client_manager.mark_test_completed(
            group_identifier, test_id
        )


@pytest.fixture(scope="function")
def client(
    multi_test_hive_test: HiveTest,
    multi_test_client_manager: MultiTestClientManager,
    fixture: BlockchainEngineXFixture,
    client_type: ClientType,
    environment: dict,
    client_genesis: dict,
    total_timing_data: "TimingData",
    request: pytest.FixtureRequest,
) -> Generator[Client, None, None]:
    """
    Provide the multi-test client for this pre-allocation group.

    Called for each test, but reuses clients across tests that
    share the same pre-allocation group.
    """
    yield from group_client(
        multi_test_hive_test,
        multi_test_client_manager,
        fixture,
        client_type,
        environment,
        client_genesis,
        total_timing_data,
        request,
    )


@pytest.fixture(scope="function")
def genesis_header(pre_alloc_group: PreAllocGroup) -> FixtureHeader:
    """Provide the genesis header from the pre-allocation group."""
    return pre_alloc_group.genesis
