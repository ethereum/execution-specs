"""Pytest fixtures for multi-test client architecture."""

import io
import json
import logging
import time
from concurrent.futures import Future, ThreadPoolExecutor
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, Generator, cast

import pytest
from _pytest.reports import TestReport
from hive.client import Client, ClientType
from hive.testing import HiveTest

from execution_testing.base_types import to_json
from execution_testing.fixtures import (
    BlockchainEngineXFixture,
    PreAllocGroup,
)
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.fixtures.consume import TestCaseBase
from execution_testing.test_types import AllocGroupHash

from ..consume import FixturesSource
from .client_start_pipeline import (
    next_group_item,
    pipeline_client_start,
    queued_items,
)
from .helpers.ruleset import ruleset
from .helpers.test_tracker import (
    PreAllocGroupTestTracker,
    group_identifier_of,
    xdist_group_of,
)

if TYPE_CHECKING:
    from .helpers.timing import TimingData

logger = logging.getLogger(__name__)

multi_test_client_manager_key: pytest.StashKey["MultiTestClientManager"] = (
    pytest.StashKey()
)
"""Session stash entry for the manager, read by the setup-outcome hook."""


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
        self.pending_start: tuple[str, Future[Client]] | None = None
        """
        The one client started ahead of its group, with the group's
        identifier, until a test of the group claims it (see
        `start_ahead`).
        """
        self._starter = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="client-start"
        )
        self.test_tracker: PreAllocGroupTestTracker | None = None
        self.stop_callbacks: list[Callable[[Client], None]] = []
        """
        Called with each client the manager stops, so a simulator can
        release what it holds for that client (such as a peer
        connection).
        """
        logger.debug("MultiTestClientManager initialized")

    def set_test_tracker(self, tracker: PreAllocGroupTestTracker) -> None:
        """
        Set the test tracker for automatic client cleanup.

        """
        self.test_tracker = tracker
        logger.debug("Test tracker registered with MultiTestClientManager")

    def start_ahead(
        self, group_identifier: str, start: Callable[[], Client]
    ) -> None:
        """
        Start a group's client on a background thread, ahead of its tests.

        At most one client is started ahead at a time; the group's first
        test claims it through `get_client`, waiting for the start to
        finish if it has not yet.
        """
        assert self.pending_start is None, "a client is already started ahead"
        logger.info(f"⏩ Starting client ahead for group {group_identifier}")
        self.pending_start = (group_identifier, self._starter.submit(start))

    def _claim_pending_start(self, group_identifier: str) -> None:
        """
        Wait for the client started ahead for this group and register it.

        A start that failed is logged and dropped, so the caller starts
        a client the usual way. The start stays pending until it is
        waited for, so an interrupted wait leaves it to the session-end
        cleanup.
        """
        if self.pending_start is None:
            return
        identifier, future = self.pending_start
        if identifier != group_identifier:
            return
        wait_start = time.perf_counter()
        try:
            client = future.result()
        except Exception as e:
            self.pending_start = None
            logger.warning(
                f"Starting the client ahead for group {group_identifier} "
                f"failed: {e!r}"
            )
            return
        self.pending_start = None
        logger.info(
            f"⏱ phase=client_start_wait group={group_identifier} "
            f"ms={(time.perf_counter() - wait_start) * 1000:.1f}"
        )
        self.register_client(group_identifier, client)

    def get_client(self, group_identifier: str) -> Client | None:
        """
        Get the client instance for a group.

        """
        self._claim_pending_start(group_identifier)
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
        self._notify_stopped(client)

    def _notify_stopped(self, client: Client) -> None:
        """Run the stop callbacks for `client`, logging any failure."""
        for callback in self.stop_callbacks:
            try:
                callback(client)
            except Exception as e:
                logger.error(f"Stop callback failed for {client.id}: {e}")

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
            # A group whose tests never asked for its client (all
            # skipped, say) still owns the client started ahead for it.
            self._claim_pending_start(group_identifier)
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
                    self._notify_stopped(client)

    def stop_all_clients(self) -> None:
        """Stop all remaining clients (at module and session end)."""
        if self.pending_start is not None:
            self._claim_pending_start(self.pending_start[0])
        self._starter.shutdown()
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
            self._notify_stopped(client)

        self.clients.clear()
        logger.info("All clients stopped")


@pytest.fixture(scope="session")
def multi_test_client_manager(
    request: pytest.FixtureRequest,
) -> Generator[MultiTestClientManager, None, None]:
    """
    Provide session-scoped MultiTestClientManager with automatic cleanup.

    """
    manager = MultiTestClientManager()
    request.session.stash[multi_test_client_manager_key] = manager
    try:
        yield manager
    finally:
        logger.info("Session ending, cleaning up multi-test clients...")
        manager.stop_all_clients()


@pytest.fixture(scope="module", autouse=True)
def _stop_clients_before_shared_test_ends(
    multi_test_hive_test: HiveTest,
    multi_test_client_manager: MultiTestClientManager,
) -> Generator[None, None, None]:
    """
    Stop the remaining clients before the shared hive test ends.

    Every client belongs to the module's shared hive test. Stopped only at
    session end, after that test has ended, a client whose start ahead was
    still running when the run was interrupted would never be stopped.
    Requesting the shared test here tears this fixture down first.
    """
    del multi_test_hive_test  # requested only so it ends after this
    yield
    multi_test_client_manager.stop_all_clients()


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


def load_pre_alloc_group(
    pre_hash: AllocGroupHash,
    fixtures_source: FixturesSource,
    pre_alloc_group_cache: dict[AllocGroupHash, PreAllocGroup],
) -> PreAllocGroup:
    """Load a pre-allocation group from the fixtures, through the cache."""
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
def pre_alloc_group(
    fixture: BlockchainEngineXFixture,
    fixtures_source: FixturesSource,
    pre_alloc_group_cache: dict[AllocGroupHash, PreAllocGroup],
) -> PreAllocGroup:
    """Load the pre-allocation group for the current test case."""
    return load_pre_alloc_group(
        fixture.pre_hash, fixtures_source, pre_alloc_group_cache
    )


def build_client_genesis(
    pre_hash: AllocGroupHash,
    pre_alloc_group: PreAllocGroup,
    client_genesis_cache: dict[AllocGroupHash, dict],
) -> dict:
    """Convert a pre-alloc group to client genesis, through the cache."""
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
    return build_client_genesis(
        fixture.pre_hash, pre_alloc_group, client_genesis_cache
    )


def build_environment(
    pre_hash: AllocGroupHash,
    pre_alloc_group: PreAllocGroup,
    check_live_port: int,
    environment_cache: dict[AllocGroupHash, dict],
) -> dict:
    """Build a pre-alloc group's client environment, through the cache."""
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
        # Tell client wrapper scripts to leave the alloc out of the genesis
        # they print at start: it is the whole pre-alloc group shared by many
        # tests (up to thousands of accounts), so dumping it floods the client
        # log without saying much about any single test.
        "HIVE_OMIT_GENESIS_ALLOC": "1",
        # Tell client wrapper scripts that the client needs no KZG at start:
        # it only verifies KZG proofs, in the point-evaluation precompile,
        # and computes none (nothing sends it blob transactions with
        # sidecars). Scripts may make the trusted setup load cheaper: later
        # or in the background. Results do not change; the first
        # point-evaluation call may wait for the load.
        "HIVE_KZG_FAST_SETUP": "1",
    }

    environment_cache[pre_hash] = env
    return env


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
    return build_environment(
        fixture.pre_hash, pre_alloc_group, check_live_port, environment_cache
    )


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


@pytest.fixture(scope="function", autouse=True)
def _start_next_group_client(
    client: Client,
    multi_test_hive_test: HiveTest,
    multi_test_client_manager: MultiTestClientManager,
    fixture: BlockchainEngineXFixture,
    fixtures_source: FixturesSource,
    environment: dict[str, str],
    check_live_port: int,
    pre_alloc_group_cache: dict[AllocGroupHash, PreAllocGroup],
    client_genesis_cache: dict[AllocGroupHash, dict],
    environment_cache: dict[AllocGroupHash, dict],
    request: pytest.FixtureRequest,
) -> None:
    """
    Start the next queued group's client once this test's is ready.

    Only while pipelining client starts (`--no-pipeline-client-start`
    turns it off), and only when no client is already started ahead.
    The next group's environment is this test's with the group-specific
    part swapped, so it keeps what a simulator adds to the environment
    fixture (as wirex does).
    """
    del client  # requested only so this runs once the client is ready
    if not pipeline_client_start(request.config):
        return
    if multi_test_client_manager.pending_start is not None:
        return
    next_item = next_group_item(
        queued_items(request.node), group_identifier_of(request.node)
    )
    if next_item is None:
        return
    next_group = group_identifier_of(next_item)
    if next_group in multi_test_client_manager.clients:
        return
    try:
        params = cast(pytest.Function, next_item).callspec.params
        pre_hash = cast(TestCaseBase, params["test_case"]).pre_hash
        assert pre_hash is not None, "the next test has no pre-alloc group"
        group = load_pre_alloc_group(
            pre_hash, fixtures_source, pre_alloc_group_cache
        )
        genesis = build_client_genesis(pre_hash, group, client_genesis_cache)
        current_base = environment_cache[fixture.pre_hash]
        next_environment = {
            **build_environment(
                pre_hash, group, check_live_port, environment_cache
            ),
            **{
                k: v
                for k, v in environment.items()
                if current_base.get(k) != v
            },
        }
    except Exception as e:
        logger.warning(f"Cannot start the client of {next_group} ahead: {e!r}")
        return
    multi_test_client_manager.start_ahead(
        next_group,
        partial(
            start_hive_client,
            multi_test_hive_test,
            next_group,
            cast(ClientType, params["client_type"]),
            next_environment,
            genesis,
        ),
    )


def start_hive_client(
    multi_test_hive_test: HiveTest,
    identifier: str,
    client_type: ClientType,
    environment: dict[str, str],
    client_genesis: dict[str, Any],
) -> Client:
    """
    Start a multi-test client for `identifier` under the shared hive test.

    Safe to call from a background thread (see `start_ahead`).
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
    resolved_client.multi_test = True
    return resolved_client


def boot_managed_client(
    multi_test_hive_test: HiveTest,
    multi_test_client_manager: MultiTestClientManager,
    identifier: str,
    client_type: ClientType,
    environment: dict[str, str],
    client_genesis: dict[str, Any],
    total_timing_data: "TimingData",
) -> Client:
    """
    Start a client and register it with the manager under `identifier`.

    `identifier` is usually a group's, but any unique key works; the
    session-end cleanup stops every registered client.
    """
    with total_timing_data.time("Start client"):
        resolved_client = start_hive_client(
            multi_test_hive_test,
            identifier,
            client_type,
            environment,
            client_genesis,
        )
    multi_test_client_manager.register_client(identifier, resolved_client)
    return resolved_client


def group_client(
    multi_test_hive_test: HiveTest,
    multi_test_client_manager: MultiTestClientManager,
    client_type: ClientType,
    environment: dict[str, str],
    client_genesis: dict[str, Any],
    total_timing_data: "TimingData",
    request: pytest.FixtureRequest,
) -> Generator[Client, None, None]:
    """
    Get or create the client for this test's group.

    The body of the `client` fixture, callable so a simulator can wrap
    it in its own `client` fixture, as `consume wirex` does.
    """
    group_identifier = group_identifier_of(request.node)
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
    client_type: ClientType,
    environment: dict[str, str],
    client_genesis: dict[str, Any],
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


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, TestReport, TestReport]:
    """
    Count a test that did not get past setup toward its group.

    A group's client is stopped once every test of the group has
    completed, and completion is normally recorded when the `client`
    fixture tears down. A test that skips or errors in a fixture
    requested before `client` never reaches it, so without this hook
    its group would never complete and its client would stay alive
    until the session ends. Recording the same test twice is harmless.
    """
    del call
    report = yield
    if report.when != "setup" or report.passed:
        return report
    manager = item.session.stash.get(multi_test_client_manager_key, None)
    group_identifier = xdist_group_of(item)
    if manager is not None and group_identifier is not None:
        manager.mark_test_completed(group_identifier, item.nodeid)
    return report
