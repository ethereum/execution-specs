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

One exception to the topology: a fixture announcing several sync
targets (see `sync_targets`) runs each target against its own isolated
client, so the group client and its peer connection are never touched
by multi-target fixtures - the isolation policy lives in
`client_policy`.
"""

import json
import logging
import os
import time
from typing import TYPE_CHECKING, Dict, Generator

import pytest
from hive.client import Client

from execution_testing.devp2p.chain import (
    Chain,
    ChainReconstructionError,
    chain_from_payloads,
)
from execution_testing.devp2p.peer import MockPeer
from execution_testing.devp2p.protocol import ETH_PROTOCOLS
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.blockchain import FixtureHeader

from ..helpers.test_tracker import count_tests_per_group
from .sync_targets import (
    UNDECODABLE_BODY_INVALIDITIES,
    SyncTargetCase,
    raw_target_path_lengths,
    resolve_sync_paths,
    target_path_lengths,
)

if TYPE_CHECKING:
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
    # Last on purpose: this module overrides the `client` fixture that
    # `multi_test_client` (above) defines, and pytest resolves duplicate
    # plugin fixtures in favor of the most recently registered plugin.
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.wirex.client_policy",
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
            "Skip sync targets whose served chain, target included, is "
            "shorter than this. The target arrives over the Engine API, "
            "so the default of 2 puts at least one block on devp2p. A "
            "fixture skips only when every one of its targets does."
        ),
    )
    group.addoption(
        "--wirex-no-sort-by-chain-length",
        action="store_false",
        dest="wirex_sort_by_chain_length",
        default=True,
        help=(
            "Do not order the tests inside each pre-allocation group "
            "(valid chains first, each by ascending length). The "
            "ordering avoids sync stalls on reused clients; disable it "
            "to reproduce them."
        ),
    )
    group.addoption(
        "--wirex-eth-version",
        action="store",
        dest="wirex_eth_version",
        choices=["auto"] + [str(v) for v in sorted(ETH_PROTOCOLS)],
        default="auto",
        help=(
            "eth protocol version the mock peer advertises. 'auto' "
            "(default) advertises every implemented version and lets "
            "RLPx negotiation pick the highest the client shares; an "
            "explicit version advertises exactly that one, so the "
            "client either speaks it or the handshake fails loudly. "
            "Valid values: auto, "
            + ", ".join(str(int(v)) for v in sorted(ETH_PROTOCOLS))
            + "."
        ),
    )
    group.addoption(
        "--wirex-sync-timeout",
        action="store",
        dest="wirex_sync_timeout",
        type=float,
        default=60.0,
        help=(
            "Seconds to wait for a client to reach the fixture head. "
            "Default: 60."
        ),
    )
    group.addoption(
        "--wirex-announce-interval",
        action="store",
        dest="wirex_announce_interval",
        type=float,
        default=3.0,
        help=(
            "Seconds between repeats of the sync target announcement "
            "while waiting for a client to reach it. Default: 3."
        ),
    )
    group.addoption(
        "--wirex-poll-interval",
        action="store",
        dest="wirex_poll_interval",
        type=float,
        default=0.005,
        help=(
            "Seconds between result polls while waiting for a verdict: "
            "eth_getBlockByHash during a valid sync, the head's "
            "newPayload for a rejection. Short chains sync in tens of "
            "milliseconds, so a long interval measures the poller "
            "rather than the client. Default: 0.005."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    """Set the supported fixture formats for the wirex simulator."""
    config.supported_fixture_formats = [BlockchainEngineXFixture]  # type: ignore[attr-defined]


def _chain_properties(
    config: pytest.Config, items: list[pytest.Item]
) -> Dict[str, tuple[bool, int]]:
    """
    Return, per node ID, whether a test declares an invalid payload and
    the length of its longest served chain.

    The fixture index records neither, so read each fixture file once
    and drop it before opening the next.
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
                max(target_path_lengths(fixture)),
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
                max(raw_target_path_lengths(raw_fixture)),
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

    group_counts = count_tests_per_group(session, items)

    chain_properties: Dict[str, tuple[bool, int]] = {}
    if config.getoption("wirex_sort_by_chain_length", True):
        chain_properties = _chain_properties(config, items)
        logger.info(
            "Ordering tests inside each pre-allocation group: valid "
            "chains before invalid ones, each by ascending chain length"
        )

    def sort_key(item: pytest.Item) -> tuple[int, str, bool, int, str]:
        """Order by group size, group ID, validity, then chain length."""
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


@pytest.fixture(scope="session")
def wirex_min_blocks(request: pytest.FixtureRequest) -> int:
    """Return the smallest chain length worth syncing."""
    return int(request.config.getoption("wirex_min_blocks"))


@pytest.fixture(scope="session")
def wirex_eth_versions(request: pytest.FixtureRequest) -> tuple[int, ...]:
    """Return the eth capability versions the mock peer advertises."""
    option = str(request.config.getoption("wirex_eth_version"))
    if option == "auto":
        return tuple(sorted(ETH_PROTOCOLS))
    return (int(option),)


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
def sync_target_cases(
    genesis_header: FixtureHeader,
    fixture: BlockchainEngineXFixture,
    wirex_min_blocks: int,
) -> list[SyncTargetCase]:
    """
    Rebuild the served chain behind each of this test's sync targets.

    Every announced target selects one root-to-leaf path through the
    authored payloads (see `sync_targets`), and each path is judged on
    its own: a path skips when it is too short to put any block on the
    wire, when its declared invalidity leaves a block with no wire
    representation, or when an invalid path cannot be reconstructed at
    all. The fixture skips only when every one of its paths does; a
    fixture that loses some paths but keeps others runs the keepers
    and logs each omission.

    Paths containing payloads flagged invalid still reconstruct and
    are served as rejection tests (see ``test_blockchain_via_wirex``):
    their blocks are semantically invalid but hash-consistent, so they
    travel the wire like any other block. Two classes cannot be
    presented over devp2p at all and drop with an explicit reason: a
    payload whose declared block hash does not match its own header (a
    header corrupted at fill via ``rlp_modifier``), because devp2p has
    no way to present a block whose hash differs from its header's
    keccak; and a payload whose declared invalidity is in the encoding
    of a transaction itself (see ``UNDECODABLE_BODY_INVALIDITIES``),
    because the client discards such a body instead of judging the
    block it belongs to.
    """
    paths = resolve_sync_paths(genesis_header.block_hash, fixture)
    cases: list[SyncTargetCase] = []
    drops: list[str] = []
    for path in paths:
        undecodable = path.invalidities & UNDECODABLE_BODY_INVALIDITIES
        if undecodable:
            drops.append(
                "invalid fixture cannot be represented over devp2p: no "
                "conformant client decodes a body declaring "
                f"{', '.join(sorted(str(e) for e in undecodable))}"
            )
            continue
        if path.length < wirex_min_blocks:
            drops.append(
                f"chain has {path.length} block(s); at least "
                f"{wirex_min_blocks} are needed for any block to be "
                "transferred over devp2p rather than the Engine API"
            )
            continue
        try:
            chain = chain_from_payloads(genesis_header, path.served_payloads)
        except ChainReconstructionError as error:
            if any(not payload.valid() for payload in path.served_payloads):
                drops.append(
                    "invalid fixture cannot be represented over "
                    f"devp2p: {error}"
                )
                continue
            raise
        cases.append(SyncTargetCase(path=path, chain=chain))
    if not cases:
        pytest.skip("; ".join(drops))
    for reason in drops:
        logger.info(
            f"Omitting one of this fixture's {len(paths)} sync "
            f"targets: {reason}"
        )
    return cases


@pytest.fixture(scope="session")
def mock_peers() -> Generator[Dict[str, MockPeer], None, None]:
    """Hold one peer per client for the lifetime of the session."""
    peers: Dict[str, MockPeer] = {}
    yield peers
    for peer in peers.values():
        peer.close()


def dial_mock_peer(
    client: Client,
    chain: Chain,
    eth_versions: tuple[int, ...],
    total_timing_data: "TimingData",
) -> MockPeer:
    """
    Dial a fresh peer connection to `client`, serving `chain`.

    Shared by the per-group `mock_peer` fixture and the per-target
    isolated clients of multi-target fixtures (see `client_policy`).
    """
    enode = client.enode()
    logger.info(f"Connecting mock peer to {enode}")
    peer = MockPeer(
        host=str(client.ip),
        port=enode.port,
        remote_public_key=bytes.fromhex(enode.id),
        private_key=os.urandom(32),
        network_id=DEFAULT_NETWORK_ID,
        eth_versions=eth_versions,
    )
    with total_timing_data.time("Connect mock peer"):
        # The client readiness gate waits on the Engine API port only;
        # a freshly started client may open its devp2p listener a
        # moment later, so the first dial gets a deadline rather than
        # a single attempt.
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
    logger.info(f"Mock peer connected to {peer.remote_name}")
    return peer


@pytest.fixture(scope="function")
def mock_peer(
    client: Client,
    sync_target_cases: list[SyncTargetCase],
    mock_peers: Dict[str, MockPeer],
    wirex_eth_versions: tuple[int, ...],
    total_timing_data: "TimingData",
) -> MockPeer:
    """
    Return the peer connected to this test's client.

    The connection is established once per client and then re-pointed
    at each test's chain, so the RLPx handshake is paid once per group
    rather than once per test. The chain installed here is the first
    sync target's; a multi-target fixture's later targets run on their
    own isolated clients, each dialed by its own peer (see
    `client_policy`).
    """
    chain = sync_target_cases[0].chain
    peer = mock_peers.get(client.id)
    if peer is None:
        peer = dial_mock_peer(
            client, chain, wirex_eth_versions, total_timing_data
        )
        mock_peers[client.id] = peer
        return peer

    if peer.alive:
        try:
            peer.set_chain(chain)  # also starts the test's statistics
            return peer
        except OSError:
            pass
    # A client may hang up mid-group (nethermind drops peers it deems
    # idle); a dead connection would otherwise fail every remaining test
    # in the group, so redial exactly as a real peer would, and start
    # the test's own statistics so its transcript holds only its own
    # traffic.
    logger.warning("Peer connection lost; redialing the client")
    with total_timing_data.time("Reconnect mock peer"):
        peer.reconnect(chain)
    peer.reset_statistics()
    return peer
