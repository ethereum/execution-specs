"""
The wirex client policy: when a test may reuse its group's client.

A single-target fixture runs on the pre-allocation group's reused
client unless `replacement_reason` gives a reason to boot a fresh one.
A fixture announcing several sync targets runs each target on its own
isolated client. The "Rejection Tests" and "Test Ordering and Client
Reuse" sections of `docs/running_tests/consume/wirex.md` explain why.

This module overrides `multi_test_client`'s `client` fixture, so the
wirex conftest lists it after `multi_test_client` in `pytest_plugins`.
It cannot live in the conftest itself: the conftest registers before
the plugins it lists, and pytest prefers the fixture of the most
recently registered plugin.
"""

import logging
from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    Any,
    Generator,
    Iterator,
    NamedTuple,
)

import pytest
from hive.client import Client, ClientType
from hive.testing import HiveTest

from execution_testing.base_types import Hash, HexNumber
from execution_testing.devp2p.chain import Chain
from execution_testing.devp2p.peer import MockPeer
from execution_testing.devp2p.protocol import EthVersion, ForkSchedule
from execution_testing.exceptions import ExceptionMapper
from execution_testing.rpc import EngineRPC, EthRPC

from ..helpers.test_tracker import group_identifier_of
from ..multi_test_client import (
    MultiTestClientManager,
    boot_managed_client,
    group_client,
)
from .conftest import dial_mock_peer
from .sync_targets import SyncTargetCase, TargetContext, TargetContextFactory

if TYPE_CHECKING:
    from ..helpers.timing import TimingData

logger = logging.getLogger(__name__)


def isolated_identifier(group_identifier: str, index: int) -> str:
    """
    Return the identifier of the isolated client for target `index`.

    Targets run one after another and release their identifier, so it
    never collides.
    """
    return f"{group_identifier}-t{index}"


MAX_REORG_DEPTH = 64
"""
Deepest reorg, in blocks, a reused client is asked to make.

Clients keep state only for their most recent blocks and cannot full
sync from a fork point below that: nethermind's beacon sync stops 64
blocks below its head (`Reorganization.MaxDepth`), ethrex keeps 128
blocks of state (`DB_COMMIT_THRESHOLD`), and reth falls back to a path
taking minutes.
"""

HEAD_LOOKUP_TIMEOUT = (5.0, 10.0)
"""
(connect, read) timeout of each attempt of the head lookup a reuse
decision needs. The RPC client retries a timed out request, so a client
that never answers is given up on after about a minute.
"""


class ClientHead(NamedTuple):
    """The number and hash of a client's current head block."""

    number: int
    block_hash: Hash


def client_head(client: Client) -> ClientHead:
    """Return the number and hash of `client`'s current head."""
    with EthRPC(
        f"http://{client.ip}:8545", request_timeout=HEAD_LOOKUP_TIMEOUT
    ) as rpc:
        head_block = rpc.get_block_by_number("latest")
    if head_block is None:
        raise LookupError("client returned no head block")
    return ClientHead(
        number=int(HexNumber(head_block["number"])),
        block_hash=Hash(head_block["hash"]),
    )


def reorg_depth(
    head_number: int, head_chain: Chain | None, chain: Chain
) -> int:
    """
    Return how many blocks a client must unwind to sync `chain`.

    `head_chain` is the served chain holding the client's head, which
    determines the head's ancestry; the depth is the head's distance
    above the highest block that ancestry shares with `chain`. A head
    on no served chain shares only genesis with it.
    """
    common = 0
    if head_chain is not None:
        for block in chain.blocks:
            if block.number > head_number:
                break
            if head_chain.number_of(block.block_hash) != block.number:
                break
            common = block.number
    return head_number - common


def build_engine_rpc(
    client: Client, exception_mapper: ExceptionMapper | None
) -> EngineRPC:
    """Return an Engine RPC handle for `client`, mapper attached."""
    context = (
        {"exception_mapper": exception_mapper}
        if exception_mapper is not None
        else None
    )
    return EngineRPC(
        f"http://{client.ip}:8551", response_validation_context=context
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
    sync_target_cases: list[SyncTargetCase],
    mock_peers: dict[str, MockPeer],
) -> Generator[Client, None, None]:
    """
    Provide this test's client, per the wirex client policy.

    A multi-target fixture gets an isolated client for its first target
    (the test body opens the rest) and never touches the group's
    client: a rejected branch can leave a client's sync machinery
    backing off and starve whatever syncs next. The fixture still
    counts toward its group's completion, so the group's client is
    torn down on time.

    A single-target fixture gets the group's client, first replaced by
    a fresh one when `replacement_reason` says reuse would fail. The
    group's later tests reuse the replacement.
    """
    group_identifier = group_identifier_of(request.node)

    if len(sync_target_cases) > 1:
        first_case = sync_target_cases[0]
        identifier = isolated_identifier(
            group_identifier, first_case.path.index
        )
        logger.info(
            f"Fixture announces {first_case.path.total} sync targets; "
            f"running {first_case.path.name} on an isolated client"
        )
        isolated = boot_managed_client(
            multi_test_hive_test,
            multi_test_client_manager,
            identifier,
            client_type,
            environment,
            client_genesis,
            total_timing_data,
        )
        try:
            yield isolated
        finally:
            # Discarding the client also closes its peer (see the
            # `mock_peers` fixture).
            multi_test_client_manager.discard_client(identifier)
            multi_test_client_manager.mark_test_completed(
                group_identifier, request.node.nodeid
            )
        return

    (case,) = sync_target_cases
    running = multi_test_client_manager.get_client(group_identifier)
    if running is not None:
        reason = replacement_reason(running, case, mock_peers.get(running.id))
        if reason is not None:
            # Loud, because a reason given on every test, such as a
            # failing head lookup, would quietly turn client reuse off.
            logger.warning(f"{reason}; replacing the client")
            multi_test_client_manager.discard_client(group_identifier)
    yield from group_client(
        multi_test_hive_test,
        multi_test_client_manager,
        client_type,
        environment,
        client_genesis,
        total_timing_data,
        request,
    )


def replacement_reason(
    running: Client, case: SyncTargetCase, peer: MockPeer | None
) -> str | None:
    """
    Return why `case` must not run on the reused client `running`.

    `None` means the client may be reused. Reuse fails for a rejection
    below the client's head (clients refuse to walk their head
    backwards, so the ancestry would never travel the wire), for a
    chain whose wire coverage is checked and whose ancestry holds a
    block the client got only over the Engine API (see
    `engine_only_ancestors`), for a reorg deeper than `MAX_REORG_DEPTH`,
    and when the client's head cannot be looked up.
    """
    try:
        head = client_head(running)
    except Exception as error:
        return f"The reused client's head lookup failed ({error!r})"
    if case.path.expects_rejection and case.chain.head.number < head.number:
        return (
            f"Rejection target {case.chain.head.number} is below the "
            f"reused client's head {head.number}, so the verdict would "
            "leave the sync path"
        )
    # A chain whose coverage is not checked cannot fail on a block the
    # client already holds, so replacing the client would buy nothing.
    engine_only = (
        engine_only_ancestors(case, peer)
        if peer is not None and case.path.checks_wire_coverage
        else []
    )
    if engine_only:
        return (
            f"Block(s) {', '.join(map(str, engine_only))} of this chain "
            "reached the reused client only over the Engine API, so they "
            "would never travel the wire as its ancestry"
        )
    head_chain = (
        None if peer is None else peer.served_chain_holding(head.block_hash)
    )
    depth = reorg_depth(head.number, head_chain, case.chain)
    if depth > MAX_REORG_DEPTH:
        return (
            f"Syncing this chain would reorg the reused client {depth} "
            f"blocks below its head {head.number}, deeper than "
            f"{MAX_REORG_DEPTH}"
        )
    return None


def engine_only_ancestors(case: SyncTargetCase, peer: MockPeer) -> list[int]:
    """
    Return the numbers of `case`'s ancestors that never traveled `peer`.

    These are blocks of an earlier test's chain whose header the peer
    never served: the head a fixture without sync targets announces
    over the Engine API, or a block the client never fetched. The
    client keeps such a head without fetching it, so a later chain that
    needs it as ancestry would fail its coverage check on a correct
    client. Blocks of no earlier chain will be fetched and are fine.
    """
    return [
        block.number
        for block in case.chain.blocks[:-1]
        if block.block_hash not in peer.header_hashes_ever_served
        and peer.served_chain_holding(block.block_hash) is not None
    ]


@pytest.fixture(scope="function")
def target_context_factory(
    multi_test_hive_test: HiveTest,
    hive_test: HiveTest,
    multi_test_client_manager: MultiTestClientManager,
    client_type: ClientType,
    environment: dict[str, str],
    client_genesis: dict[str, Any],
    total_timing_data: "TimingData",
    wirex_eth_versions: tuple[EthVersion, ...],
    wirex_serve_bals: bool,
    wirex_fork_schedule: ForkSchedule,
    client_exception_mapper: ExceptionMapper | None,
    request: pytest.FixtureRequest,
) -> TargetContextFactory:
    """
    Return a context manager running one sync target on its own client.

    Used for each target after the first: boot a fresh client at the
    group's genesis, register it with the Hive test so its logs land in
    the result, dial it with its own mock peer serving the target's
    chain, and close the peer and discard the client on exit.

    Register the client with the per-test `hive_test`, never the
    module-scoped test it was started under: hive's multi-test
    registration copies the client record without its stop authority,
    so registering a client with its own test makes the later stop a
    silent no-op and leaks the container.
    """
    group_identifier = group_identifier_of(request.node)

    @contextmanager
    def open_target_context(case: SyncTargetCase) -> Iterator[TargetContext]:
        identifier = isolated_identifier(group_identifier, case.path.index)
        logger.info(f"Running {case.path.name} on an isolated client")
        target_client = boot_managed_client(
            multi_test_hive_test,
            multi_test_client_manager,
            identifier,
            client_type,
            environment,
            client_genesis,
            total_timing_data,
        )
        peer: MockPeer | None = None
        try:
            hive_test.register_multi_test_client(target_client)
            with (
                EthRPC(f"http://{target_client.ip}:8545") as eth_rpc,
                build_engine_rpc(
                    target_client, client_exception_mapper
                ) as engine_rpc,
            ):
                peer = dial_mock_peer(
                    target_client,
                    case.chain,
                    wirex_eth_versions,
                    wirex_serve_bals,
                    wirex_fork_schedule,
                    total_timing_data,
                )
                yield TargetContext(
                    client=target_client,
                    eth_rpc=eth_rpc,
                    engine_rpc=engine_rpc,
                    mock_peer=peer,
                )
        finally:
            if peer is not None:
                peer.close()
            multi_test_client_manager.discard_client(identifier)

    return open_target_context
