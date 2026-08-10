"""
Pytest fixtures for the `consume wirex` simulator.

The client topology is the one `consume enginex` established: one client
per pre-allocation group, reused by every test in that group. What
differs is how a test's blocks reach the client: instead of being handed
over one `engine_newPayload` call at a time, they are downloaded by the
client from a mock devp2p peer, so the blocks travel the client's
production full sync path. There is no rewind between tests - every
chain forks at the group's genesis, and the new head is announced.

The peer is created once per client and re-pointed at each test's chain,
which keeps the RLPx handshake out of the per-test cost.
"""

import io
import json
import logging
import os
import time
from typing import TYPE_CHECKING, Dict, Generator, cast

import pytest
from hive.client import Client, ClientType
from hive.testing import HiveTest

from execution_testing.devp2p.chain import (
    Chain,
    ChainReconstructionError,
    chain_from_payloads,
)
from execution_testing.devp2p.peer import MockPeer
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.blockchain import (
    FixtureEngineNewPayload,
    FixtureHeader,
)
from execution_testing.fixtures.pre_alloc_groups import PreAllocGroup

from ..helpers.test_tracker import (
    PreAllocGroupTestTracker,
    enginex_group_counts_key,
    make_group_identifier,
)

if TYPE_CHECKING:
    from ..multi_test_client import MultiTestClientManager
    from ..timing_data import TimingData

logger = logging.getLogger(__name__)

pytest_plugins = (
    "execution_testing.cli.pytest_commands.plugins.pytest_hive.pytest_hive",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.base",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.multi_test_client",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.test_case_description",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.timing_data",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.exceptions",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.helpers.test_tracker",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.engine_api",
)

DEFAULT_NETWORK_ID = 1
"""Network identifier the client is started with, and the peer claims."""


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the wirex specific command line options."""
    group = parser.getgroup("wirex", "Arguments for the wirex simulator")
    group.addoption(
        "--wirex-min-blocks",
        action="store",
        dest="wirex_min_blocks",
        type=int,
        default=2,
        help=(
            "Skip fixtures whose chain is shorter than this. A fixture's "
            "announced head is delivered over the Engine API to name the "
            "sync target, so only the blocks before it travel over "
            "devp2p; at the default of 2 every executed test syncs at "
            "least one block from the peer. An appended sync payload "
            "counts toward the length: a valid single-block test plus "
            "its trailer is a two-block chain."
        ),
    )
    group.addoption(
        "--wirex-sort-by-chain-length",
        action="store_true",
        dest="wirex_sort_by_chain_length",
        default=False,
        help=(
            "Order the tests inside each pre-allocation group: valid "
            "chains before invalid ones, each by ascending chain "
            "length, so a reused client's head number never decreases "
            "and no valid sync follows a served bad block. Geth's "
            "beacon sync has been observed to stall when asked to "
            "sync a chain shorter than one the same client already "
            "synced, and to back off after syncing a chain with a bad "
            "block in a way that starves the next sync."
        ),
    )
    group.addoption(
        "--wirex-sync-timeout",
        action="store",
        dest="wirex_sync_timeout",
        type=float,
        default=60.0,
        help="Seconds to wait for a client to reach the fixture head.",
    )
    group.addoption(
        "--wirex-announce-interval",
        action="store",
        dest="wirex_announce_interval",
        type=float,
        default=3.0,
        help=(
            "Seconds between repeats of the sync target announcement "
            "while waiting for a client to reach it."
        ),
    )
    group.addoption(
        "--wirex-poll-interval",
        action="store",
        dest="wirex_poll_interval",
        type=float,
        default=0.05,
        help=(
            "Seconds between forkchoice updates while waiting for a sync "
            "to finish. Short chains sync in tens of milliseconds, so a "
            "long interval measures the poller rather than the client."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    """Set the supported fixture formats for the wirex simulator."""
    config.supported_fixture_formats = [BlockchainEngineXFixture]  # type: ignore[attr-defined]


def _chain_properties(
    config: pytest.Config, items: list[pytest.Item]
) -> Dict[str, tuple[bool, int]]:
    """
    Read each collected test case's chain properties for ordering: does
    the chain contain an invalid payload, and how long is it.

    An appended sync payload counts toward the length: it is a real
    block of the served chain, and the ordering must agree with the
    skip accounting, which counts it too. The fixture index records
    neither property, so the fixture files are read directly, one at a
    time: each file is parsed once, mined for all of its collected
    test cases, and dropped before the next is opened, so the peak
    footprint is one parsed file rather than the whole corpus.
    """
    properties: Dict[str, tuple[bool, int]] = {}
    cases_by_path: Dict[str, list[tuple[str, str]]] = {}
    source_path = getattr(config, "fixtures_source", None)
    for item in items:
        callspec = getattr(item, "callspec", None)
        if callspec is None:
            continue
        test_case = callspec.params.get("test_case")
        fixture = getattr(test_case, "fixture", None)
        if fixture is not None:  # stdin: the fixture is already loaded
            properties[item.nodeid] = (
                any(not payload.valid() for payload in fixture.payloads),
                len(sync_chain_payloads(fixture)),
            )
            continue
        json_path = getattr(test_case, "json_path", None)
        if json_path is None or source_path is None:
            continue
        path = str(source_path.path / json_path)
        cases_by_path.setdefault(path, []).append((item.nodeid, test_case.id))
    for path, cases in cases_by_path.items():
        with open(path) as file:
            raw = json.load(file)
        for nodeid, case_id in cases:
            raw_fixture = raw.get(case_id)
            if raw_fixture is None:
                continue
            payloads = raw_fixture.get("engineNewPayloads", [])
            properties[nodeid] = (
                any(
                    payload.get("validationError") is not None
                    for payload in payloads
                ),
                len(payloads) + (1 if raw_fixture.get("syncPayload") else 0),
            )
    return properties


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Count tests per pre-allocation group and sort largest first."""
    supported_formats = getattr(config, "supported_fixture_formats", [])
    if BlockchainEngineXFixture not in supported_formats:
        return

    group_counts: dict[str, int] = {}
    for item in items:
        for marker in item.iter_markers("xdist_group"):
            if "name" in marker.kwargs:
                group_counts[marker.kwargs["name"]] = (
                    group_counts.get(marker.kwargs["name"], 0) + 1
                )
                break

    session.stash[enginex_group_counts_key] = group_counts
    logger.info(
        f"Counted {len(group_counts)} pre-alloc groups with "
        f"{sum(group_counts.values())} total tests"
    )

    chain_properties: Dict[str, tuple[bool, int]] = {}
    if config.getoption("wirex_sort_by_chain_length", False):
        chain_properties = _chain_properties(config, items)
        logger.info(
            "Ordering tests inside each pre-allocation group: valid "
            "chains before invalid ones, each by ascending chain length"
        )

    def sort_key(item: pytest.Item) -> tuple[int, str, bool, int, str]:
        """
        Return sort key: largest group first, then by group id, then
        (when enabled) valid chains before invalid ones, each by
        ascending chain length inside the group.

        Invalid chains run last because serving a chain with a bad
        block leaves a client's sync machinery in a failure state that
        a following valid sync on the same client collides with
        (observed on geth as a backfill backoff whose delayed header
        retries race the peer's chain switches); once the group's
        valid tests are done, that state poisons nothing.
        """
        has_invalid, chain_length = chain_properties.get(
            item.nodeid, (False, 0)
        )
        for marker in item.iter_markers("xdist_group"):
            if "name" in marker.kwargs:
                group = marker.kwargs["name"]
                return (
                    -group_counts[group],
                    group,
                    has_invalid,
                    chain_length,
                    item.nodeid,
                )
        return (0, "", has_invalid, chain_length, item.nodeid)

    items.sort(key=sort_key)


@pytest.fixture(scope="session", autouse=True)
def _configure_client_manager(
    multi_test_client_manager: "MultiTestClientManager",
    pre_alloc_group_test_tracker: PreAllocGroupTestTracker,
) -> None:
    """Wire the test tracker to the client manager at session start."""
    multi_test_client_manager.set_test_tracker(pre_alloc_group_test_tracker)


@pytest.fixture(scope="module")
def test_suite_name() -> str:
    """The name of the hive test suite used in this simulator."""
    return "eels/consume-wirex"


@pytest.fixture(scope="module")
def test_suite_description() -> str:
    """The description of the hive test suite used in this simulator."""
    return (
        "Execute blockchain tests against clients by making them full sync "
        "the fixture blocks from a mock devp2p peer."
    )


@pytest.fixture(scope="function", autouse=True)
def _per_test_reporting(client: Client, hive_test: HiveTest) -> None:
    """Register a test for execution against a multi-test client."""
    hive_test.register_multi_test_client(client)


@pytest.fixture(scope="function")
def client(
    multi_test_hive_test: HiveTest,
    multi_test_client_manager: "MultiTestClientManager",
    fixture: BlockchainEngineXFixture,
    client_type: ClientType,
    environment: dict,
    client_genesis: dict,
    total_timing_data: "TimingData",
    request: pytest.FixtureRequest,
) -> Generator[Client, None, None]:
    """Get or create the client serving this pre-allocation group."""
    group_identifier = make_group_identifier(
        fixture.pre_hash, client_type.name
    )

    resolved_client = multi_test_client_manager.get_client(group_identifier)
    if resolved_client is not None:
        logger.info(f"♻️  Reusing client for group {group_identifier}")
    else:
        genesis_bytes = json.dumps(client_genesis).encode("utf-8")
        buffered_genesis = io.BufferedReader(
            cast(io.RawIOBase, io.BytesIO(genesis_bytes))
        )
        logger.info(
            f"🚀 Starting client ({client_type.name}) "
            f"for group {group_identifier}"
        )
        with total_timing_data.time("Start client"):
            resolved_client = multi_test_hive_test.start_client(
                client_type=client_type,
                environment=environment,
                files={"/genesis.json": buffered_genesis},
            )
        assert resolved_client is not None, (
            f"Unable to connect to client ({client_type.name}) via Hive. "
            "Check the client or Hive server logs for more information."
        )
        multi_test_client_manager.register_client(
            group_identifier, resolved_client
        )
        resolved_client.multi_test = True

    try:
        yield resolved_client
    finally:
        multi_test_client_manager.mark_test_completed(
            group_identifier, request.node.nodeid
        )


@pytest.fixture(scope="session")
def wirex_min_blocks(request: pytest.FixtureRequest) -> int:
    """Return the smallest chain length worth syncing."""
    return int(request.config.getoption("wirex_min_blocks"))


@pytest.fixture(scope="session")
def wirex_sync_timeout(request: pytest.FixtureRequest) -> float:
    """Return how long to wait for a client to reach the fixture head."""
    return float(request.config.getoption("wirex_sync_timeout"))


@pytest.fixture(scope="session")
def wirex_announce_interval(request: pytest.FixtureRequest) -> float:
    """Return how often to repeat the sync target announcement."""
    return float(request.config.getoption("wirex_announce_interval"))


@pytest.fixture(scope="session")
def wirex_poll_interval(request: pytest.FixtureRequest) -> float:
    """Return the interval between forkchoice updates while syncing."""
    return float(request.config.getoption("wirex_poll_interval"))


@pytest.fixture(scope="function")
def genesis_header(pre_alloc_group: PreAllocGroup) -> FixtureHeader:
    """Provide the genesis header from the pre-allocation group."""
    return pre_alloc_group.genesis


def sync_chain_payloads(
    fixture: BlockchainEngineXFixture,
) -> list[FixtureEngineNewPayload]:
    """
    Return the payload sequence a sync-based consumer serves.

    The author's chain, plus the appended sync payload when the fixture
    carries one: the trailer is a real block above the test's head, and
    it is the block this simulator announces, so the peer must hold it
    like any other. Prepend-class fixtures need no assembly - their
    extra block is already ``payloads[0]``.
    """
    payloads = list(fixture.payloads)
    if fixture.sync_payload is not None:
        payloads.append(fixture.sync_payload)
    return payloads


@pytest.fixture(scope="function")
def chain(
    genesis_header: FixtureHeader,
    fixture: BlockchainEngineXFixture,
    wirex_min_blocks: int,
) -> Chain:
    """
    Rebuild the chain of blocks this test expects a client to hold.

    The chain is the author's payloads plus the appended sync payload
    when the fixture carries one, so an appended-class single-block
    test is a two-block chain here. Chains too short to put any block
    on the wire skip here, before any reconstruction or peer setup is
    spent on them.

    Fixtures whose payloads are flagged invalid still reconstruct and
    are served as rejection tests (see ``test_blockchain_via_wirex``):
    their blocks are semantically invalid but hash-consistent, so they
    travel the wire like any other block. The exception is a payload
    whose declared block hash does not match its own header (a header
    corrupted at fill via ``rlp_modifier``): devp2p has no way to
    present a block whose hash differs from its header's keccak, so
    such fixtures are skipped rather than reported as setup errors.
    """
    payloads = sync_chain_payloads(fixture)
    if len(payloads) < wirex_min_blocks:
        pytest.skip(
            f"chain has {len(payloads)} block(s); at least "
            f"{wirex_min_blocks} are needed for any block to be "
            "transferred over devp2p rather than the Engine API"
        )
    try:
        return chain_from_payloads(genesis_header, payloads)
    except ChainReconstructionError as error:
        if any(not payload.valid() for payload in fixture.payloads):
            pytest.skip(
                f"invalid fixture cannot be represented over devp2p: {error}"
            )
        raise


@pytest.fixture(scope="session")
def mock_peers() -> Generator[Dict[str, MockPeer], None, None]:
    """Hold one peer per client for the lifetime of the session."""
    peers: Dict[str, MockPeer] = {}
    yield peers
    for peer in peers.values():
        peer.close()


@pytest.fixture(scope="function")
def mock_peer(
    client: Client,
    chain: Chain,
    mock_peers: Dict[str, MockPeer],
    total_timing_data: "TimingData",
) -> MockPeer:
    """
    Return the peer connected to this test's client.

    The connection is established once per client and then re-pointed at
    each test's chain, so the RLPx handshake is paid once per group
    rather than once per test.
    """
    peer = mock_peers.get(client.id)
    if peer is None:
        enode = client.enode()
        logger.info(f"Connecting mock peer to {enode}")
        peer = MockPeer(
            host=str(client.ip),
            port=enode.port,
            remote_public_key=bytes.fromhex(enode.id),
            private_key=os.urandom(32),
            network_id=DEFAULT_NETWORK_ID,
        )
        with total_timing_data.time("Connect mock peer"):
            # The readiness gate behind `client` waits on the Engine
            # API port only; a freshly started client may open its
            # devp2p listener a moment later, so the first dial gets
            # a deadline rather than a single attempt.
            deadline = time.monotonic() + 10.0
            while True:
                try:
                    peer.connect(chain)
                    break
                except OSError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.25)
            peer.start()
        mock_peers[client.id] = peer
        logger.info(f"Mock peer connected to {peer.remote_name}")
        return peer

    # A client may hang up mid-group (nethermind drops peers it deems
    # idle); a dead connection would otherwise fail every remaining test
    # in the group, so redial exactly as a real peer would.
    if not peer.alive:
        logger.warning("Peer connection lost; redialing the client")
        with total_timing_data.time("Reconnect mock peer"):
            peer.reconnect(chain)
        return peer
    try:
        peer.set_chain(chain)
    except OSError:
        logger.warning("Connection died announcing the chain; redialing")
        with total_timing_data.time("Reconnect mock peer"):
            peer.reconnect(chain)
    return peer
