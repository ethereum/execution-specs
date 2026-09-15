"""
A hive based simulator that makes clients full sync fixture blocks.

Where `consume rlp` hands a client its blocks through a client specific
offline import mode, and `consume engine` hands them over one
`engine_newPayload` call at a time, this simulator makes the client
fetch them itself, from a mock peer speaking the production devp2p
protocols.

The control plane and the data plane are deliberately separate:

- The control plane is the Engine API. A post-merge client does not
  choose its own head, so it is told which block to sync to. That takes
  one `engine_newPayload` for the head block, which gives the client the
  header, and one `engine_forkchoiceUpdated` naming that head.
- The data plane is devp2p. Every block before the head is downloaded
  from the mock peer over RLPx and executed by the client's full sync
  path.

Because only the blocks before the announced head are guaranteed to
travel over devp2p - whether a client also re-fetches the head's body
from a peer is an implementation choice, and measured clients go both
ways - the filler builds one extra empty block above every leaf of the
authored payload graph, out-of-chain in the fixture's ordered
`syncPayloads` list. Each entry is one sync target: announcing it makes
every authored payload on its root-to-leaf path an ancestor whose
header and body a full-syncing client must fetch from the peer, on
every client, by chain structure rather than client courtesy. A
fixture usually has one target, but authored payload graphs can fan
out - an expected-invalid payload does not advance the canonical
parent, so a valid payload following it is its sibling - and then the
fixture carries one target per leaf, each run here against its own
served chain and judged on its own path (see
``wirex.sync_targets``). The fixtures without any target - chains
asserting an Engine API error code, chains above whose leaves the
filler could build no block, chains that opted out at fill time, and
corpora filled with `--no-sync-block` - announce their own head
instead. Targets whose chains are too short to put any block on the
wire are skipped where the limitation actually lives, in the
`sync_target_cases` fixture.
"""

import time
from typing import TYPE_CHECKING, Callable, ContextManager

from hive.client import Client

from execution_testing.devp2p.chain import Block, Chain
from execution_testing.devp2p.peer import MockPeer
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.logging import get_logger
from execution_testing.rpc import (
    EngineRPC,
    EthRPC,
    ForkchoiceUpdateTimeoutError,
)
from execution_testing.rpc.rpc_types import (
    ForkchoiceState,
    JSONRPCError,
    PayloadStatus,
    PayloadStatusEnum,
)

from ..helpers.exceptions import (
    GenesisBlockMismatchExceptionError,
    LoggedError,
)
from ..helpers.timing import TimingData
from ..wirex.sync_targets import (
    HEADER_JUDGEABLE_INVALIDITIES,
    SyncTargetCase,
)

if TYPE_CHECKING:
    from ..wirex.client_policy import TargetContext

logger = get_logger(__name__)

ACCEPTANCE_HOLD_TIME = 0.5
"""
Seconds a VALID verdict on an invalid head must hold to be believed.

A client answers `engine_newPayload` from the database state of that
instant, so while a chain is still arriving its answer can be a
transient artifact rather than a judgement: geth has been observed
answering VALID for a block its own backfill rejected fifteen
milliseconds later. Only a verdict that outlives its sync fails the
test, which costs this wait once per genuinely accepted chain.
"""


def required_wire_bodies(chain: Chain) -> list[Block]:
    """
    Return the blocks whose bodies must have traveled the wire.

    Every block below the announced head, except those whose body a
    client may derive from the header alone (empty transactions trie,
    empty withdrawals root). The head itself is exempt by protocol:
    its payload arrives through the Engine API, and whether a client
    also re-fetches its body from a peer is an implementation choice
    that measured clients answer both ways.
    """
    return [
        block
        for block in chain.blocks[:-1]
        if block.transactions or block.withdrawals
    ]


def required_wire_headers(chain: Chain) -> list[Block]:
    """
    Return the blocks whose headers must have traveled the wire.

    Every block below the announced head, none exempted: a header can
    never be derived from anything else, so a client that judged the
    chain must have downloaded each one from the peer. The head is
    exempt for the same reason as in `required_wire_bodies`: its
    payload arrives through the Engine API.
    """
    return chain.blocks[:-1]


EVIDENCE_GRACE_TIME = 0.25
"""
Seconds to let the peer's serving evidence catch up before a missing
block fails the coverage check.

The peer records a response as served only after its socket write
succeeds, so a failed send never reads as service - but that ordering
means the evidence lands moments after the client already has the
data. A fast client can import the chain, answer the head poll and
reach the check inside that window, so a miss is re-read once after
this grace before it is believed. Blocks that arrived some other way
stay caught: evidence that was never going to appear does not appear
a quarter second later either.
"""


def assert_wire_coverage(
    chain: Chain,
    mock_peer: MockPeer,
    outcome: str,
    require_bodies: bool = True,
) -> None:
    """
    Assert per block hash that the test's blocks traveled the wire.

    Every block below the announced head must have had its header
    served by this peer, and every such block whose body a client
    cannot derive from the header alone its body too, block by block:
    an aggregate count would let one downloaded block vouch for a
    chain whose other blocks arrived some other way (a stale client
    left running with the same genesis really does serve them, and
    this check is what catches it). `outcome` names what the client
    got right, so a failure reads as the exact gap it is: a correct
    result reached off the wire.

    `require_bodies` is False for chains whose declared invalidity a
    client may judge from headers alone (see
    `HEADER_JUDGEABLE_INVALIDITIES`); the headers stay required, since
    even the shortcut cannot be taken over blocks the client never saw.

    The evidence is cumulative per client, not per test: the test's
    own blocks carry no per-test salt (the salt lives in the appended
    trailer), so two tests of one group may declare byte-identical
    chains, and the reused client re-syncs nothing for the second -
    its blocks already traveled the wire during the first.
    """

    def missing_blocks(
        required: list[Block], ever_served: set[bytes]
    ) -> list[int]:
        """Return the numbers of `required` blocks never served."""
        return [
            block.number
            for block in required
            if block.block_hash not in ever_served
        ]

    required_headers = required_wire_headers(chain)
    required_bodies = required_wire_bodies(chain) if require_bodies else []
    missing_headers = missing_blocks(
        required_headers, mock_peer.header_hashes_ever_served
    )
    missing_bodies = missing_blocks(
        required_bodies, mock_peer.body_hashes_ever_served
    )
    if missing_headers or missing_bodies:
        time.sleep(EVIDENCE_GRACE_TIME)
        missing_headers = missing_blocks(
            required_headers, mock_peer.header_hashes_ever_served
        )
        missing_bodies = missing_blocks(
            required_bodies, mock_peer.body_hashes_ever_served
        )

    statistics = mock_peer.statistics
    prior_served = sum(
        1
        for block in required_bodies
        if block.block_hash not in statistics.body_hashes_served
        and block.block_hash in mock_peer.body_hashes_ever_served
    )
    if prior_served:
        logger.info(
            f"{prior_served} of {len(required_bodies)} required "
            "body/bodies already traveled the wire during an earlier "
            "test of this client (byte-identical chain content); the "
            "wire-coverage evidence is cumulative per client"
        )

    complaints = []
    if missing_headers:
        complaints.append(
            "the header(s) of block(s) "
            f"{', '.join(str(n) for n in missing_headers)}"
        )
    if missing_bodies:
        complaints.append(
            "the non-empty body/bodies of block(s) "
            f"{', '.join(str(n) for n in missing_bodies)}"
        )
    if complaints:
        raise LoggedError(
            f"The client {outcome}, but {' and '.join(complaints)} "
            "never traveled this client's wire connection, so those "
            "blocks were not verified over devp2p. Peer transcript: "
            f"{statistics.transcript}"
        )
    if statistics.receipt_requests:
        logger.warning(
            f"Client made {statistics.receipt_requests} receipt "
            "request(s), which this peer does not serve; the client "
            "may not be executing the blocks it downloads."
        )


def _run_sync_target(
    case: SyncTargetCase,
    client: Client,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    mock_peer: MockPeer,
    timing_data: TimingData,
    genesis_verified_clients: set[str],
    genesis_header: FixtureHeader,
    sync_timeout: float,
    poll_interval: float,
    announce_interval: float,
) -> None:
    """
    Make one client sync or reject one target's served chain.

    All verdict and coverage decisions here are branch-local: the
    rejection expectation, the declared-invalidity sets, and the
    per-hash wire coverage all belong to the selected path, never to
    sibling payloads absent from it. For a fixture with one target
    this is exactly the whole-fixture judgement it always was.
    """
    chain = case.chain
    head_payload = case.target
    head_hash = head_payload.params[0].block_hash
    expect_rejection = case.expects_rejection

    # A single-target fixture keeps its established, unprefixed
    # messages; a multi-target one names the branch in everything it
    # logs or raises, so a failure identifies the target.
    prefix = f"{case.name}: " if case.path.total > 1 else ""
    if prefix:
        logger.info(
            f"Running {case.label}, expecting the branch to be "
            + ("rejected" if expect_rejection else "synchronized")
        )

    if client.id not in genesis_verified_clients:
        with timing_data.time(f"{prefix}Verify genesis"):
            genesis_block = eth_rpc.get_block_by_number(0)
            if genesis_block is None:
                raise LoggedError(f"{prefix}Client returned no genesis block")
            if genesis_block["hash"] != str(genesis_header.block_hash):
                raise GenesisBlockMismatchExceptionError(
                    expected_header=genesis_header,
                    got_genesis_block=genesis_block,
                )
            genesis_verified_clients.add(client.id)

    expected_head = "0x" + chain.head.block_hash.hex()

    head_state = ForkchoiceState(
        head_block_hash=head_hash,
        safe_block_hash=genesis_header.block_hash,
        finalized_block_hash=genesis_header.block_hash,
    )

    def announce() -> PayloadStatus:
        """
        Tell the client which block to sync to.

        The `newPayload` response is returned because it carries the
        client's verdict on the head: SYNCING while the ancestry is
        still traveling, VALID once imported, and INVALID as soon as
        the client has executed the ancestry and refused the chain.
        """
        payload_status = engine_rpc.new_payload(
            *head_payload.params, version=head_payload.new_payload_version
        )
        engine_rpc.forkchoice_updated(
            forkchoice_state=head_state,
            payload_attributes=None,
            version=head_payload.forkchoice_updated_version,
        )
        return payload_status

    def expected_rpc_refusal(error: JSONRPCError) -> bool:
        """
        Return whether `error` is the rejection the fixture declares.

        A head payload that violates the Engine API's rules for the
        fork (e.g. a pre-fork block carrying blob fields) is refused
        at the RPC layer before any chain context matters. When the
        fixture declares that error code, the refusal is the expected
        rejection - but only with the declared code, so a client
        failing for an unrelated reason still fails the test.
        """
        if head_payload.error_code is None:
            return False
        if error.code != head_payload.error_code:
            raise LoggedError(
                f"{prefix}Client refused the head with the wrong error "
                f"code: got {error.code}, expected "
                f"{head_payload.error_code}"
            )
        logger.info(
            f"{prefix}Client refused the invalid head at the RPC layer "
            f"with the expected error code {head_payload.error_code} "
            f"({error})"
        )
        return True

    announce_status: PayloadStatus | None = None
    with timing_data.time(f"{prefix}Announce sync target"):
        logger.info(
            f"{prefix}Announcing head block {chain.head.number} to "
            f"trigger a sync of {len(chain.blocks) - 1} ancestor "
            "block(s) over devp2p"
        )
        try:
            announce_status = announce()
        except JSONRPCError as error:
            if expected_rpc_refusal(error):
                return
            raise

    if expect_rejection:
        with timing_data.time(f"{prefix}Reject invalid chain"):
            deadline = time.monotonic() + sync_timeout
            next_announcement = time.monotonic() + announce_interval
            status: PayloadStatusEnum | None = None
            validation_error: object = None
            accepted_since: float | None = None
            while time.monotonic() < deadline:
                # Once the ancestry has arrived over devp2p the client
                # can judge the head; until then it answers SYNCING (or
                # ACCEPTED if it merely stored the payload).
                try:
                    payload_status = engine_rpc.new_payload(
                        *head_payload.params,
                        version=head_payload.new_payload_version,
                    )
                except JSONRPCError as error:
                    if expected_rpc_refusal(error):
                        return
                    raise
                status = payload_status.status
                validation_error = payload_status.validation_error
                if status in (
                    PayloadStatusEnum.INVALID,
                    PayloadStatusEnum.INVALID_BLOCK_HASH,
                ):
                    break
                if status != PayloadStatusEnum.VALID:
                    accepted_since = None
                elif accepted_since is None:
                    # A client whose sync is still in flight answers
                    # about the database state of that instant, and a
                    # lone VALID is not proof that it accepted the
                    # chain: geth has been observed answering a
                    # well-formed VALID for a block its own backfill
                    # rejected milliseconds later, then INVALID on
                    # every ask thereafter. A real acceptance holds, so
                    # the verdict is read only once it has.
                    accepted_since = time.monotonic()
                    logger.warning(
                        f"{prefix}Client answered VALID for the invalid "
                        f"head {expected_head} (latestValidHash "
                        f"{payload_status.latest_valid_hash}) while the "
                        "chain may still be arriving; confirming before "
                        "failing the test"
                    )
                elif time.monotonic() - accepted_since >= ACCEPTANCE_HOLD_TIME:
                    raise LoggedError(
                        f"{prefix}Client accepted the invalid chain: "
                        f"head {expected_head} returned VALID for "
                        f"{ACCEPTANCE_HOLD_TIME}s (latestValidHash "
                        f"{payload_status.latest_valid_hash}) but the "
                        "fixture expects the block to be rejected"
                    )
                if time.monotonic() >= next_announcement:
                    if not mock_peer.alive:
                        # A client may drop a peer that served it a bad
                        # chain; a real peer would simply redial.
                        logger.warning(
                            f"{prefix}Peer dropped mid-rejection; redialing"
                        )
                        mock_peer.reconnect(chain)
                    logger.info(
                        f"{prefix}Re-announcing the invalid sync target"
                    )
                    try:
                        announce()
                    except JSONRPCError as error:
                        if expected_rpc_refusal(error):
                            return
                        raise
                    next_announcement = time.monotonic() + announce_interval
                time.sleep(poll_interval)
            if status not in (
                PayloadStatusEnum.INVALID,
                PayloadStatusEnum.INVALID_BLOCK_HASH,
            ):
                raise LoggedError(
                    f"{prefix}Client never rejected the invalid head "
                    f"{expected_head} within {sync_timeout}s (last "
                    f"status: {status}). Peer transcript: "
                    f"{mock_peer.statistics.transcript}"
                )
        statistics = mock_peer.statistics
        logger.info(
            f"{prefix}Client rejected the invalid head at block "
            f"{chain.head.number} with {status} "
            f"(validationError: {validation_error}) after the peer "
            f"served {statistics.headers_served} header(s) and "
            f"{statistics.bodies_served} body/bodies"
        )
        if not case.announces_scaffolding:
            # The announced head is the test's own invalid block, so
            # the client may answer from the announcement alone and owes
            # the wire nothing: a header field it can validate on its
            # own is enough, and a client that already
            # refused an ancestor of this chain answers from that memory
            # (nethermind: `Block 2 ... is known to be a part of an
            # invalid chain`). Both are correct, so there is no wire
            # claim to make here - which is exactly why the filler
            # builds a target wherever it can.
            logger.info(
                f"{prefix}Not asserting wire coverage: this chain "
                "carries no framework sync target, so its own head was "
                "announced and the client may judge it without fetching "
                "an ancestor"
            )
            return
        # The verdict alone is not the test: it must have been reached
        # on the sync path, over blocks this peer served. The invalid
        # block sits below the announced target, so its transport is
        # guaranteed by chain structure and asserted like any other
        # ancestor's. Bodies are exempt only when the client may have
        # judged the declared invalidity from headers alone; `any`
        # rather than `all`, because a chain that might fail either
        # way lets the client take the header shortcut. The invalidity
        # census is this path's, never a sibling's.
        header_judgeable = bool(
            case.invalidities & HEADER_JUDGEABLE_INVALIDITIES
        )
        if header_judgeable:
            logger.info(
                f"{prefix}Not requiring bodies on the wire: the "
                "declared invalidity is judgeable from the headers alone"
            )
        assert_wire_coverage(
            chain,
            mock_peer,
            "rejected the invalid chain",
            require_bodies=not header_judgeable,
        )
        return

    def raise_if_rejected(payload_status: PayloadStatus | None) -> None:
        """
        Fail immediately when the client has refused the chain.

        An INVALID verdict for the head means the client has already
        downloaded and executed the ancestry and decided against it -
        waiting out the sync timeout cannot import the chain, and the
        verdict carries the client's reason while a timeout carries
        nothing. Reading the verdict from the announcement that was
        sent anyway costs no extra requests.
        """
        if payload_status is not None and payload_status.status in (
            PayloadStatusEnum.INVALID,
            PayloadStatusEnum.INVALID_BLOCK_HASH,
        ):
            raise LoggedError(
                f"{prefix}Client rejected the chain at head "
                f"{expected_head}: {payload_status.status} "
                f"(validationError: {payload_status.validation_error}). "
                f"Peer transcript: {mock_peer.statistics.transcript}"
            )

    with timing_data.time(f"{prefix}Sync from peer"):
        # Wait by watching for the block rather than by repeating the
        # forkchoice update. A repeated update restarts the client's sync
        # cycle, and repeating it faster than a cycle takes prevents the
        # sync from ever finishing. The announcement is repeated on a much
        # slower cadence, as a consensus client would each slot, because a
        # client whose sync state was still settling may have ignored the
        # first one.
        raise_if_rejected(announce_status)
        deadline = time.monotonic() + sync_timeout
        next_announcement = time.monotonic() + announce_interval
        synced = False
        while time.monotonic() < deadline:
            if eth_rpc.get_block_by_hash(head_hash, full_txs=False):
                synced = True
                break
            if time.monotonic() >= next_announcement:
                if not mock_peer.alive:
                    # A mid-sync drop would otherwise strand the test
                    # peerless until its timeout; redial like a real
                    # peer would.
                    logger.warning(f"{prefix}Peer dropped mid-sync; redialing")
                    mock_peer.reconnect(chain)
                logger.info(f"{prefix}Re-announcing the sync target")
                raise_if_rejected(announce())
                next_announcement = time.monotonic() + announce_interval
            time.sleep(poll_interval)
        if not synced:
            raise LoggedError(
                f"{prefix}Client never imported the fixture head "
                f"{expected_head} within {sync_timeout}s. Peer "
                f"transcript: {mock_peer.statistics.transcript}"
            )

    with timing_data.time(f"{prefix}Confirm head"):
        try:
            response = engine_rpc.forkchoice_updated_with_retry(
                forkchoice_state=head_state,
                forkchoice_version=head_payload.forkchoice_updated_version,
                max_attempts=10,
                wait_fixed=0.5,
            )
        except ForkchoiceUpdateTimeoutError as error:
            raise LoggedError(
                f"{prefix}Client imported {expected_head} but never made "
                f"it canonical: {error}"
            ) from None
        if response.payload_status.status != PayloadStatusEnum.VALID:
            raise LoggedError(
                f"{prefix}Client failed to sync to {expected_head}: "
                f"{response.payload_status.status}. Peer transcript: "
                f"{mock_peer.statistics.transcript}"
            )

    with timing_data.time(f"{prefix}Verify head"):
        head_block = eth_rpc.get_block_by_number("latest")
        if head_block is None:
            raise LoggedError(f"{prefix}Client returned no head block")
        if head_block["hash"] != expected_head:
            raise LoggedError(
                f"{prefix}Client head is {head_block['hash']}, expected "
                f"{expected_head}"
            )

    statistics = mock_peer.statistics
    logger.info(
        f"{prefix}Synced to block {chain.head.number}: peer served "
        f"{statistics.headers_served} header(s) in "
        f"{statistics.header_requests} request(s) and "
        f"{statistics.bodies_served} body/bodies in "
        f"{statistics.body_requests} request(s)"
    )
    assert_wire_coverage(chain, mock_peer, "reached the expected head")


def test_blockchain_via_wirex(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    client: Client,
    genesis_verified_clients: set[str],
    genesis_header: FixtureHeader,
    sync_target_cases: list[SyncTargetCase],
    mock_peer: MockPeer,
    target_context_factory: Callable[
        [SyncTargetCase], "ContextManager[TargetContext]"
    ],
    wirex_sync_timeout: float,
    wirex_poll_interval: float,
    wirex_announce_interval: float,
) -> None:
    """
    Make a client full sync each of one test's chains from a mock peer.

    A fixture announces one sync target per leaf of its authored
    payload graph, and each target selects one root-to-leaf path (see
    ``wirex.sync_targets``). The sequence per target is:

    1. Verify the client's genesis matches the group's, once per client.
    2. Deliver the announced target over the Engine API so the client
       knows which chain to sync to, and name it in a forkchoice
       update. The target rides above the path's leaf, so every
       authored block on the path is an ancestor the client must
       fetch from the peer.
    3. Wait for the client to download and execute the ancestors from the
       mock peer, polling the same forkchoice update until it is VALID.
       Each announcement's `newPayload` answer is read as the client's
       verdict: an INVALID means the client has executed the ancestry
       and refused the chain, so the test fails immediately with the
       client's reason instead of waiting out the sync timeout.
    4. Check the client's head really is the expected block.

    Most fixtures carry one target and run exactly as they always
    have, on the pre-allocation group's reused client: every test's
    chain forks at genesis, so announcing the new head is all a
    consensus client would do, and there is deliberately no rewind
    between tests - a backwards forkchoice update is actively harmful
    to clients that act on it (nethermind moves its head back to
    genesis while its persisted state stays at the previous chain's
    tip, landing in a crash-recovery edge case where it fetches
    receipts instead of executing blocks; geth ignores the rewind
    entirely).

    A fixture with several targets runs each on its own isolated
    client, first target included (see ``wirex.client_policy``): its
    rejected branches would otherwise leave the shared client's sync
    machinery in a backoff state that starves whatever syncs next.
    Each target gets its own client, peer connection, timing entries
    and log lines, labeled by its position and leaf so a failure names
    the branch.

    A path containing an intentionally invalid block is a rejection
    case: the peer serves the chain as-is and the client passes by
    refusing it - `engine_newPayload` for the target must answer
    INVALID once the ancestry is available over devp2p, and a VALID
    that holds fails the test. Only the fact of rejection is asserted,
    never its cause - a devp2p peer observes acceptance or rejection,
    not error causes, so matching the fixture's specific exception
    over the wire is deliberately left for later - and, for a chain
    announcing a framework target, the verdict must have been reached
    on the wire: the same per-hash coverage check the valid path runs
    is applied to everything below the announced target, the invalid
    block included. A chain without a target announces its own invalid
    head, which a client may judge without fetching anything, so no
    wire claim is made for those. Paths whose invalid block cannot
    even be represented on the wire (declared hash inconsistent with
    the header) are dropped by the `sync_target_cases` fixture. A
    single-target rejection below the reused client's head never
    reaches this function on that client: the wirex `client` fixture
    hands such a test a fresh client, because a client whose sync
    machinery refuses to walk its head backwards would starve the
    verdict, and delivering the ancestry over the Engine API instead
    would take the verdict off the sync path this simulator exists to
    exercise.
    """
    first, *rest = sync_target_cases
    _run_sync_target(
        case=first,
        client=client,
        eth_rpc=eth_rpc,
        engine_rpc=engine_rpc,
        mock_peer=mock_peer,
        timing_data=timing_data,
        genesis_verified_clients=genesis_verified_clients,
        genesis_header=genesis_header,
        sync_timeout=wirex_sync_timeout,
        poll_interval=wirex_poll_interval,
        announce_interval=wirex_announce_interval,
    )
    for case in rest:
        with target_context_factory(case) as context:
            _run_sync_target(
                case=case,
                client=context.client,
                eth_rpc=context.eth_rpc,
                engine_rpc=context.engine_rpc,
                mock_peer=context.mock_peer,
                timing_data=timing_data,
                genesis_verified_clients=genesis_verified_clients,
                genesis_header=genesis_header,
                sync_timeout=wirex_sync_timeout,
                poll_interval=wirex_poll_interval,
                announce_interval=wirex_announce_interval,
            )
