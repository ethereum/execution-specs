"""Pytest fixtures for multi-test client architecture."""

import logging
from typing import Generator

import pytest
from hive.client import Client

from execution_testing.base_types import to_json
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.pre_alloc_groups import PreAllocGroup

from ..consume import FixturesSource
from .helpers.ruleset import ruleset
from .helpers.test_tracker import PreAllocGroupTestTracker

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
                    client.stop()
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
def pre_alloc_group_cache() -> dict[str, PreAllocGroup]:
    """Cache for pre-allocation groups to avoid reloading from disk."""
    return {}


@pytest.fixture(scope="session")
def client_genesis_cache() -> dict[str, dict]:
    """Cache for client genesis configs to avoid redundant to_json calls."""
    return {}


@pytest.fixture(scope="session")
def environment_cache() -> dict[str, dict]:
    """Cache for environment configs to avoid redundant computation."""
    return {}


@pytest.fixture(scope="function")
def pre_alloc_group(
    fixture: BlockchainEngineXFixture,
    fixtures_source: FixturesSource,
    pre_alloc_group_cache: dict[str, PreAllocGroup],
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
    pre_alloc_group_obj = PreAllocGroup.from_file(pre_alloc_path)

    pre_alloc_group_cache[pre_hash] = pre_alloc_group_obj
    logger.info(f"Loaded pre-alloc group for {pre_hash}")

    return pre_alloc_group_obj


@pytest.fixture(scope="function")
def client_genesis(
    pre_alloc_group: PreAllocGroup,
    fixture: BlockchainEngineXFixture,
    client_genesis_cache: dict[str, dict],
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

    genesis = to_json(pre_alloc_group.genesis)
    alloc = to_json(pre_alloc_group.pre)
    # NOTE: nethermind requires account keys without '0x' prefix
    genesis["alloc"] = {k.replace("0x", ""): v for k, v in alloc.items()}

    client_genesis_cache[pre_hash] = genesis
    return genesis


@pytest.fixture(scope="function")
def environment(
    pre_alloc_group: PreAllocGroup,
    fixture: BlockchainEngineXFixture,
    check_live_port: int,
    environment_cache: dict[str, dict],
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
    }

    environment_cache[pre_hash] = env
    return env
