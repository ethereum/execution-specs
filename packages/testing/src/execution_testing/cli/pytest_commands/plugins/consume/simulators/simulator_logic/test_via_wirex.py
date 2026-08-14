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
ways - the filler appends one extra empty block to every eligible
engine_x chain, valid and invalid heads alike, out-of-chain in the
fixture's `syncPayload` field. This simulator announces that trailer
instead of the test's own head, which makes every one of the test's
blocks an ancestor whose header and body a full-syncing client must
fetch from the peer, on every client, by chain structure rather than
client courtesy. The fixtures without a trailer - chains asserting an
Engine API error code, chains marked ineligible at fill time, and
corpora filled with `--no-sync-block` - announce their own head
instead. Chains still too short to put any block on the wire are
skipped here, where the limitation actually lives.
"""

import time

from hive.client import Client

from execution_testing.devp2p.chain import Block, Chain
from execution_testing.devp2p.peer import MockPeer
from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.blockchain import (
    FixtureEngineNewPayload,
    FixtureHeader,
)
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


def announced_payload(
    fixture: BlockchainEngineXFixture,
) -> FixtureEngineNewPayload:
    """
    Return the payload this simulator announces as the sync target.

    The appended sync payload when the fixture carries one - the
    trailer exists precisely to be announced, so that every payload of
    the test's own chain is an ancestor the client must fetch from the
    peer - and the chain's own head otherwise. The fixtures without a
    trailer announce their own head by design: a chain asserting an
    Engine API error code is refused at the announcement itself, so
    announcing anything above it would unmake the test, and marked or
    `--no-sync-block` chains carry nothing above the author's head to
    announce.
    """
    return fixture.sync_payload or fixture.payloads[-1]


def expects_rejection(fixture: BlockchainEngineXFixture) -> bool:
    """
    Return whether the fixture passes by the client refusing it.

    A chain containing an intentionally invalid payload must be judged
    INVALID once its ancestry has arrived, and a declared Engine API
    error code is itself a rejection: the client must refuse the head,
    whether at the RPC layer or with an INVALID verdict, even when
    every payload is semantically valid.
    """
    return (
        any(not payload.valid() for payload in fixture.payloads)
        or announced_payload(fixture).error_code is not None
    )


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


def test_blockchain_via_wirex(
    timing_data: TimingData,
    eth_rpc: EthRPC,
    engine_rpc: EngineRPC,
    client: Client,
    genesis_verified_clients: set[str],
    fixture: BlockchainEngineXFixture,
    genesis_header: FixtureHeader,
    chain: Chain,
    mock_peer: MockPeer,
    wirex_sync_timeout: float,
    wirex_poll_interval: float,
    wirex_announce_interval: float,
) -> None:
    """
    Make a client full sync one test's chain from the mock peer.

    The sequence is:

    1. Verify the client's genesis matches the group's, once per client.
    2. Deliver the announced head over the Engine API so the client
       knows which chain to sync to, and name it in a forkchoice
       update. For a fixture carrying a sync payload that head is the
       trailer riding above the test's own chain, so every block the
       test author wrote is an ancestor the client must fetch from the
       peer.
    3. Wait for the client to download and execute the ancestors from the
       mock peer, polling the same forkchoice update until it is VALID.
       Each announcement's `newPayload` answer is read as the client's
       verdict: an INVALID means the client has executed the ancestry
       and refused the chain, so the test fails immediately with the
       client's reason instead of waiting out the sync timeout.
    4. Check the client's head really is the expected block.

    There is deliberately no rewind between tests. Every test's chain
    forks at genesis, so announcing the new head is all a consensus
    client would do, and a backwards forkchoice update is actively
    harmful to clients that act on it: nethermind moves its head back
    to genesis while its persisted state stays at the previous chain's
    tip, which lands it in a crash-recovery edge case where it fetches
    receipts instead of executing blocks (`BlockDownloader.
    ReceiptEdgeCase`); geth ignores the rewind entirely.

    Fixtures containing an intentionally invalid block are rejection
    tests: the peer serves the chain as-is and the client passes by
    refusing it - `engine_newPayload` for the head must answer INVALID
    once the ancestry is available over devp2p, and a VALID that holds
    fails the test. Only the fact of rejection is asserted: a devp2p
    peer observes acceptance or rejection, not error causes, so
    matching the fixture's specific exception over the wire is
    deliberately left for later. Fixtures whose invalid block cannot
    even be represented on the wire (declared hash inconsistent with
    the header) are skipped by the `chain` fixture. A rejection target
    below the reused client's head never reaches this function on that
    client: the wirex `client` fixture hands such a test a fresh
    client, because a client whose sync machinery refuses to walk its
    head backwards would starve the verdict, and delivering the
    ancestry over the Engine API instead would take the verdict off
    the sync path this simulator exists to exercise.
    """
    head_payload = announced_payload(fixture)
    head_hash = head_payload.params[0].block_hash

    if client.id not in genesis_verified_clients:
        with timing_data.time("Verify genesis"):
            genesis_block = eth_rpc.get_block_by_number(0)
            if genesis_block is None:
                raise LoggedError("Client returned no genesis block")
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
                f"Client refused the head with the wrong error code: "
                f"got {error.code}, expected {head_payload.error_code}"
            )
        logger.info(
            f"Client refused the invalid head at the RPC layer with "
            f"the expected error code {head_payload.error_code} "
            f"({error})"
        )
        return True

    expect_rejection = expects_rejection(fixture)

    announce_status: PayloadStatus | None = None
    with timing_data.time("Announce sync target"):
        logger.info(
            f"Announcing head block {chain.head.number} to trigger a sync "
            f"of {len(chain.blocks) - 1} ancestor block(s) over devp2p"
        )
        try:
            announce_status = announce()
        except JSONRPCError as error:
            if expected_rpc_refusal(error):
                return
            raise

    if expect_rejection:
        with timing_data.time("Reject invalid chain"):
            deadline = time.monotonic() + wirex_sync_timeout
            next_announcement = time.monotonic() + wirex_announce_interval
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
                        f"Client answered VALID for the invalid head "
                        f"{expected_head} (latestValidHash "
                        f"{payload_status.latest_valid_hash}) while the "
                        "chain may still be arriving; confirming before "
                        "failing the test"
                    )
                elif time.monotonic() - accepted_since >= ACCEPTANCE_HOLD_TIME:
                    raise LoggedError(
                        f"Client accepted the invalid chain: head "
                        f"{expected_head} returned VALID for "
                        f"{ACCEPTANCE_HOLD_TIME}s (latestValidHash "
                        f"{payload_status.latest_valid_hash}) but the "
                        "fixture expects the block to be rejected"
                    )
                if time.monotonic() >= next_announcement:
                    if not mock_peer.alive:
                        # A client may drop a peer that served it a bad
                        # chain; a real peer would simply redial.
                        logger.warning("Peer dropped mid-rejection; redialing")
                        mock_peer.reconnect(chain)
                    logger.info("Re-announcing the invalid sync target")
                    try:
                        announce()
                    except JSONRPCError as error:
                        if expected_rpc_refusal(error):
                            return
                        raise
                    next_announcement = (
                        time.monotonic() + wirex_announce_interval
                    )
                time.sleep(wirex_poll_interval)
            if status not in (
                PayloadStatusEnum.INVALID,
                PayloadStatusEnum.INVALID_BLOCK_HASH,
            ):
                raise LoggedError(
                    f"Client never rejected the invalid head "
                    f"{expected_head} within {wirex_sync_timeout}s (last "
                    f"status: {status}). Peer transcript: "
                    f"{mock_peer.statistics.transcript}"
                )
        statistics = mock_peer.statistics
        logger.info(
            f"Client rejected the invalid head at block "
            f"{chain.head.number} with {status} "
            f"(validationError: {validation_error}) after the peer "
            f"served {statistics.headers_served} header(s) and "
            f"{statistics.bodies_served} body/bodies"
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
                f"Client rejected the chain at head {expected_head}: "
                f"{payload_status.status} (validationError: "
                f"{payload_status.validation_error}). Peer transcript: "
                f"{mock_peer.statistics.transcript}"
            )

    with timing_data.time("Sync from peer"):
        # Wait by watching for the block rather than by repeating the
        # forkchoice update. A repeated update restarts the client's sync
        # cycle, and repeating it faster than a cycle takes prevents the
        # sync from ever finishing. The announcement is repeated on a much
        # slower cadence, as a consensus client would each slot, because a
        # client whose sync state was still settling may have ignored the
        # first one.
        raise_if_rejected(announce_status)
        deadline = time.monotonic() + wirex_sync_timeout
        next_announcement = time.monotonic() + wirex_announce_interval
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
                    logger.warning("Peer dropped mid-sync; redialing")
                    mock_peer.reconnect(chain)
                logger.info("Re-announcing the sync target")
                raise_if_rejected(announce())
                next_announcement = time.monotonic() + wirex_announce_interval
            time.sleep(wirex_poll_interval)
        if not synced:
            raise LoggedError(
                f"Client never imported the fixture head {expected_head} "
                f"within {wirex_sync_timeout}s. Peer transcript: "
                f"{mock_peer.statistics.transcript}"
            )

    with timing_data.time("Confirm head"):
        try:
            response = engine_rpc.forkchoice_updated_with_retry(
                forkchoice_state=head_state,
                forkchoice_version=head_payload.forkchoice_updated_version,
                max_attempts=10,
                wait_fixed=0.5,
            )
        except ForkchoiceUpdateTimeoutError as error:
            raise LoggedError(
                f"Client imported {expected_head} but never made it "
                f"canonical: {error}"
            ) from None
        if response.payload_status.status != PayloadStatusEnum.VALID:
            raise LoggedError(
                f"Client failed to sync to {expected_head}: "
                f"{response.payload_status.status}. Peer transcript: "
                f"{mock_peer.statistics.transcript}"
            )

    with timing_data.time("Verify head"):
        head_block = eth_rpc.get_block_by_number("latest")
        if head_block is None:
            raise LoggedError("Client returned no head block")
        if head_block["hash"] != expected_head:
            raise LoggedError(
                f"Client head is {head_block['hash']}, expected "
                f"{expected_head}"
            )

    statistics = mock_peer.statistics
    logger.info(
        f"Synced to block {chain.head.number}: peer served "
        f"{statistics.headers_served} header(s) in "
        f"{statistics.header_requests} request(s) and "
        f"{statistics.bodies_served} body/bodies in "
        f"{statistics.body_requests} request(s)"
    )
    # Every non-derivable body below the announced head must have
    # traveled the wire, block by block: an aggregate count would let
    # one downloaded body vouch for a chain whose other bodies arrived
    # some other way. The evidence is cumulative per client, not per
    # test: valid chains carry no per-test salt, so two tests of one
    # group may declare byte-identical chains, and the reused client
    # re-syncs nothing for the second - its blocks already traveled
    # the wire during the first.
    required = required_wire_bodies(chain)
    ever_served = mock_peer.body_hashes_ever_served
    missing_bodies = [
        block.number
        for block in required
        if block.block_hash not in ever_served
    ]
    prior_served = sum(
        1
        for block in required
        if block.block_hash not in statistics.body_hashes_served
        and block.block_hash in ever_served
    )
    if prior_served:
        logger.info(
            f"{prior_served} of {len(required)} required body/bodies "
            "already traveled the wire during an earlier test of this "
            "client (byte-identical chain content); the wire-coverage "
            "evidence is cumulative per client"
        )
    if missing_bodies:
        raise LoggedError(
            "The client reached the expected head, but the non-empty "
            "body/bodies of block(s) "
            f"{', '.join(str(n) for n in missing_bodies)} never "
            "traveled this client's wire connection, so those blocks "
            "were not verified over devp2p."
        )
    if statistics.receipt_requests:
        logger.warning(
            f"Client made {statistics.receipt_requests} receipt request(s), "
            "which this peer does not serve; the client may not be "
            "executing the blocks it downloads."
        )
