"""
Pytest fixtures for the `consume wirex` simulator.

The client topology is `consume enginex`'s, one client per
pre-allocation group, but each client downloads the test's blocks from
a mock devp2p peer, so they travel its production full sync path.
Every chain forks at the group's genesis and there is no rewind between
tests. `client_policy` holds the exceptions to client reuse.
"""

import json
import logging
import os
import time
from enum import StrEnum
from functools import partial
from typing import TYPE_CHECKING, Dict, Generator, Mapping, NamedTuple

import pytest
from hive.client import Client, ClientType

from execution_testing.devp2p.chain import (
    Chain,
    ChainReconstructionError,
    block_from_payload,
    chain_from_payloads,
)
from execution_testing.devp2p.peer import MockPeer
from execution_testing.devp2p.protocol import (
    ETH_PROTOCOLS,
    EthVersion,
    ForkSchedule,
)
from execution_testing.devp2p.rlpx import RLPxError
from execution_testing.fixtures import BlockchainEngineXFixture, PreAllocGroup
from execution_testing.fixtures.blockchain import (
    FixtureEngineNewPayload,
    FixtureHeader,
)
from execution_testing.fixtures.consume import (
    TestCaseBase,
    TestCaseIndexFile,
    TestCaseStream,
)
from execution_testing.forks import Fork, TransitionFork
from execution_testing.forks.transition_base_fork import TransitionBaseClass

from ..helpers.test_tracker import (
    GroupVariants,
    count_tests_per_group,
    group_variant_of,
    group_variants_key,
    xdist_group_of,
)
from .sync_targets import (
    UNDECODABLE_BODY_INVALIDITIES,
    SyncTargetCase,
    raw_target_path_lengths,
    resolve_sync_paths,
    target_path_lengths,
)

if TYPE_CHECKING:
    from ..helpers.timing import TimingData
    from ..multi_test_client import MultiTestClientManager

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
    # After `multi_test_client`, whose `client` fixture this module
    # overrides: pytest prefers the most recently registered plugin.
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.wirex.client_policy",
    # After `multi_test_client` and this module: it extends their
    # `environment` and `test_suite_description` fixtures.
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.wirex.sync_loop_interval",
)

DEFAULT_NETWORK_ID = 1
"""Network identifier the client is started with, and the peer claims."""


class BalMode(StrEnum):
    """A `--wirex-bals` mode: whether the mock peer serves BALs."""

    WITHHOLD = "withhold"
    SERVE = "serve"
    BOTH = "both"


class BalVariant(StrEnum):
    """The BAL group variants, which are also the test ID suffixes."""

    WITHHELD = "bal_withheld"
    SERVED = "bal_served"


BAL_MODE_VARIANTS: Mapping[BalMode, tuple[BalVariant, ...]] = {
    BalMode.WITHHOLD: (BalVariant.WITHHELD,),
    BalMode.SERVE: (BalVariant.SERVED,),
    BalMode.BOTH: (BalVariant.WITHHELD, BalVariant.SERVED),
}
"""The group variants each `--wirex-bals` mode runs a fixture under."""

WITHHOLD_ONLY_CLIENTS = ("nethermind",)
"""
Clients that run only `withhold` under `--wirex-bals both`.

nethermind requests BALs only for finalized blocks, and WireX finalizes
only genesis, so its served tests would repeat its withheld ones.
Matched as a substring of the Hive client name.
"""


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
        choices=["auto"] + [str(int(v)) for v in sorted(ETH_PROTOCOLS)],
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
        "--wirex-bals",
        action="store",
        dest="wirex_bals",
        choices=[mode.value for mode in BalMode],
        default="both",
        help=(
            "Whether the mock peer serves BALs in reply to eth/71 "
            "GetBlockAccessLists. 'withhold' answers every entry as "
            "unavailable, so the client must execute each block itself; "
            "'serve' answers from each block's payload. 'both' (default) "
            "runs each Amsterdam-onward fixture once per mode, except on "
            + ", ".join(WITHHOLD_ONLY_CLIENTS)
            + " (withhold only). Amsterdam-onward test IDs end in "
            "'-bal_withheld' or '-bal_served'."
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
    mode = BalMode(str(config.getoption("wirex_bals", "both")))
    group_variants: GroupVariants = partial(bal_variants, mode=mode)
    config.stash[group_variants_key] = group_variants


def pytest_report_header(config: pytest.Config) -> list[str]:
    """State the BAL mode, and the clients that run one mode only."""
    mode = BalMode(str(config.getoption("wirex_bals", "both")))
    if mode != BalMode.BOTH:
        return [f"wirex BALs: {mode}"]
    return [
        "wirex BALs: both (withhold only on "
        + ", ".join(WITHHOLD_ONLY_CLIENTS)
        + ")"
    ]


def withholds_only(client_name: str) -> bool:
    """Return whether the client runs `withhold` only under `both`."""
    return any(client in client_name for client in WITHHOLD_ONLY_CLIENTS)


def bal_variants(
    test_case: TestCaseBase, client_type: ClientType, mode: BalMode
) -> tuple[str, ...]:
    """
    Return the BAL modes to run `test_case` under on `client_type`.

    Only Amsterdam-onward blocks carry a BAL, so an earlier fixture runs
    once, unsuffixed.
    """
    fork = test_case.fork
    if fork is None or not fork.transitions_to().header_bal_hash_required():
        return ("",)
    if mode == BalMode.BOTH and withholds_only(client_type.name):
        return (BalVariant.WITHHELD,)
    return BAL_MODE_VARIANTS[mode]


class ChainProperties(NamedTuple):
    """What the collection order reads of one test's served chains."""

    has_invalid: bool
    """Whether the test declares an invalid payload."""

    longest_chain: int
    """The length of the test's longest served chain."""


def _chain_properties(
    config: pytest.Config, items: list[pytest.Item]
) -> Dict[str, ChainProperties]:
    """
    Return, per node ID, whether a test declares an invalid payload and
    the length of its longest served chain.

    The fixture index records neither, so read each fixture file once
    and drop it before opening the next.
    """
    properties: Dict[str, ChainProperties] = {}
    cases_by_path: Dict[str, list[tuple[str, str]]] = {}
    source_path = getattr(config, "fixtures_source", None)
    for item in items:
        callspec = getattr(item, "callspec", None)
        if callspec is None:
            continue
        test_case = callspec.params.get("test_case")
        if isinstance(test_case, TestCaseStream):
            # stdin: the fixture is already loaded.
            fixture = test_case.fixture
            if isinstance(fixture, BlockchainEngineXFixture):
                properties[item.nodeid] = ChainProperties(
                    any(not payload.valid() for payload in fixture.payloads),
                    max(target_path_lengths(fixture)),
                )
            continue
        if not isinstance(test_case, TestCaseIndexFile) or source_path is None:
            continue
        path = str(source_path.path / test_case.json_path)
        cases_by_path.setdefault(path, []).append((item.nodeid, test_case.id))
    for path, cases in cases_by_path.items():
        with open(path) as file:
            raw = json.load(file)
        for nodeid, case_id in cases:
            raw_fixture = raw.get(case_id)
            if raw_fixture is None:
                continue
            payloads = raw_fixture.get("engineNewPayloads", [])
            properties[nodeid] = ChainProperties(
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

    chain_properties: Dict[str, ChainProperties] = {}
    if config.getoption("wirex_sort_by_chain_length", True):
        chain_properties = _chain_properties(config, items)
        logger.info(
            "Ordering tests inside each pre-allocation group: valid "
            "chains before invalid ones, each by ascending chain length"
        )

    def sort_key(item: pytest.Item) -> tuple[int, str, bool, int, str]:
        """Order by group size, group ID, validity, then chain length."""
        has_invalid, chain_length = chain_properties.get(
            item.nodeid, ChainProperties(False, 0)
        )
        group = xdist_group_of(item)
        count = 0 if group is None else group_counts[group]
        return (-count, group or "", has_invalid, chain_length, item.nodeid)

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
def wirex_eth_versions(
    request: pytest.FixtureRequest,
) -> tuple[EthVersion, ...]:
    """Return the eth capability versions the mock peer advertises."""
    option = str(request.config.getoption("wirex_eth_version"))
    if option == "auto":
        return tuple(sorted(ETH_PROTOCOLS))
    return (EthVersion(int(option)),)


@pytest.fixture(scope="function")
def wirex_serve_bals(request: pytest.FixtureRequest) -> bool:
    """
    Return whether this test's peer serves BALs.

    A test without a variant predates Amsterdam and has no BAL to serve.
    """
    return group_variant_of(request.node) == BalVariant.SERVED


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
    """Return the interval between polls while waiting for a verdict."""
    return float(request.config.getoption("wirex_poll_interval"))


def _unrebuildable(payload: FixtureEngineNewPayload) -> bool:
    """Return whether `payload`'s own block cannot be rebuilt from it."""
    try:
        block_from_payload(payload)
    except ChainReconstructionError:
        return True
    return False


@pytest.fixture(scope="function")
def sync_target_cases(
    genesis_header: FixtureHeader,
    fixture: BlockchainEngineXFixture,
    wirex_min_blocks: int,
) -> list[SyncTargetCase]:
    """
    Rebuild the served chain behind each of this test's sync targets.

    Drop a path that is too short to put a block on devp2p, that
    declares a body no client can decode, or whose invalid header
    cannot be rebuilt from its own payload (a commitment modified at
    fill leaves no trace in the payload); the drop message names the
    cause. Any other rebuild failure is a defect and raises.
    Skip the test only when every path is dropped, and log each drop.
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
            if any(
                _unrebuildable(payload)
                for payload in path.served_payloads
                if not payload.valid()
            ):
                drops.append(
                    "invalid fixture's header cannot be rebuilt from its "
                    "Engine API payload: the declared block hash commits "
                    "to a header value the payload does not carry, such "
                    f"as a commitment modified at fill; {error}"
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
def mock_peers(
    multi_test_client_manager: "MultiTestClientManager",
) -> Generator[Dict[str, MockPeer], None, None]:
    """
    Hold one peer per live client.

    A peer keeps every chain it has served, so it is closed and
    dropped as soon as the client manager stops its client, rather
    than at the end of the session.
    """
    peers: Dict[str, MockPeer] = {}

    def close_peer(client: Client) -> None:
        peer = peers.pop(client.id, None)
        if peer is not None:
            peer.close()

    multi_test_client_manager.stop_callbacks.append(close_peer)
    yield peers
    for peer in peers.values():
        peer.close()


def fork_schedule_of(fork: Fork | TransitionFork) -> ForkSchedule:
    """
    Return when the network a client runs for `fork` forks after genesis.

    The client is configured from the Hive ruleset of the group's fork
    (see `multi_test_client`), which activates every fork of a post-merge
    network at genesis except the second fork of a transition fork:
    Shanghai at timestamp 15000 for `ParisToShanghaiAtTime15k`, say.
    """
    if not issubclass(fork, TransitionBaseClass):
        return ForkSchedule()
    return ForkSchedule(
        block_numbers=(fork.at_block,), timestamps=(fork.at_timestamp,)
    )


@pytest.fixture(scope="function")
def wirex_fork_schedule(pre_alloc_group: PreAllocGroup) -> ForkSchedule:
    """Return the fork schedule of the network the group's client runs."""
    return fork_schedule_of(pre_alloc_group.fork)


def dial_mock_peer(
    client: Client,
    chain: Chain,
    eth_versions: tuple[EthVersion, ...],
    serve_bals: bool,
    fork_schedule: ForkSchedule,
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
        serve_bals=serve_bals,
        fork_schedule=fork_schedule,
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
    wirex_eth_versions: tuple[EthVersion, ...],
    wirex_serve_bals: bool,
    wirex_fork_schedule: ForkSchedule,
    total_timing_data: "TimingData",
) -> MockPeer:
    """
    Return this client's peer, re-pointed at the test's first target.

    The peer is dialed once per client, so the RLPx handshake is paid
    once per group. Later targets of a multi-target fixture use their
    own peers (see `client_policy`).
    """
    chain = sync_target_cases[0].chain
    peer = mock_peers.get(client.id)
    if peer is None:
        peer = dial_mock_peer(
            client,
            chain,
            wirex_eth_versions,
            wirex_serve_bals,
            wirex_fork_schedule,
            total_timing_data,
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
    # in the group, so redial exactly as a real peer would. The test's
    # own statistics start before the redial, since a client asks for
    # headers as soon as the session is up, and those requests belong
    # to this test's transcript.
    logger.warning("Peer connection lost; redialing the client")
    peer.reset_statistics()
    with total_timing_data.time("Reconnect mock peer"):
        try:
            peer.reconnect(chain)
        except (OSError, RLPxError) as error:
            # The test's sync loop redials at its next announcement.
            logger.warning(
                f"Redial failed ({error}); the test retries it at its "
                "next announcement"
            )
    return peer
