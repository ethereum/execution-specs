"""
A hive based simulator that makes clients full sync fixture blocks.

The client is told its head over the Engine API (one `newPayload` and
one `forkchoiceUpdated`) and downloads every block below that head from
a mock devp2p peer, through its production full sync path. Each sync
target of a fixture (see `wirex.sync_targets`) runs and is judged on
its own served chain. `docs/running_tests/consume/wirex.md` describes
the chain classes, rejection tests and wire coverage.
"""

import time
from contextlib import AbstractContextManager, nullcontext
from typing import Callable

from hive.client import Client

from execution_testing.base_types import Hash
from execution_testing.devp2p.chain import Block, Chain
from execution_testing.devp2p.peer import MockPeer
from execution_testing.devp2p.rlpx import RLPxError
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
    SyncPath,
    SyncTargetCase,
    TargetContext,
    TargetContextFactory,
)

logger = get_logger(__name__)

ACCEPTANCE_HOLD_TIME = 0.5
"""
Seconds a VALID verdict on an invalid head must hold to be believed.

A client answers `engine_newPayload` from its database state of that
instant, so while the chain is still arriving a VALID can be transient:
geth has answered VALID for a block its own backfill rejected moments
later.
"""

REJECTED_STATUSES = frozenset({PayloadStatusEnum.INVALID})
"""
The `newPayload` statuses that reject the head.

INVALID_BLOCK_HASH is not one: every served payload hashes to its
`blockHash` (`chain_from_payloads` checks it), and `newPayloadV2` onward
answers INVALID where V1 answered INVALID_BLOCK_HASH, so that status is
always a wrong answer.
"""


def required_wire_bodies(chain: Chain) -> list[Block]:
    """
    Return the blocks below the head whose bodies must be served.

    A body with no transactions and no withdrawals is derived from its
    header, so it is not owed.
    """
    return [
        block
        for block in chain.blocks[:-1]
        if block.transactions or block.withdrawals
    ]


def required_wire_headers(chain: Chain) -> list[Block]:
    """Return the blocks below the head, whose headers must be served."""
    return chain.blocks[:-1]


EVIDENCE_GRACE_TIME = 2.0
"""
Seconds the peer's serving evidence may lag the client's verdict before
a missing block fails the coverage check.

The peer records a response only after writing it, so a fast client
can import the chain and answer the head poll before the evidence
lands, the more so on a loaded host that holds the peer's thread back.
A miss is re-read every `EVIDENCE_POLL_INTERVAL` until this grace has
passed; a block that arrived some other way stays missing, and a
complete record costs no wait at all.
"""

EVIDENCE_POLL_INTERVAL = 0.01
"""Seconds between re-reads of the serving evidence during its grace."""


def assert_wire_coverage(
    chain: Chain,
    mock_peer: MockPeer,
    outcome: str,
    require_bodies: bool = True,
) -> None:
    """
    Assert per block hash that the chain below its head traveled the wire.

    Every header below the announced head, and every body among them
    that `required_wire_bodies` lists, must have been served by
    `mock_peer`; an aggregate count would let one downloaded block
    vouch for blocks that arrived some other way. The head is exempt:
    its payload arrives over the Engine API. `outcome` names what the
    client got right, for the failure message, and `require_bodies` is
    False for a header-judgeable invalidity (see
    `HEADER_JUDGEABLE_INVALIDITIES`).

    The evidence is cumulative per client: tests of one group may
    declare byte-identical blocks, which the reused client downloads
    only once.
    """

    def missing_blocks(
        required: list[Block], ever_served: set[Hash]
    ) -> list[int]:
        """Return the numbers of `required` blocks never served."""
        return [
            block.number
            for block in required
            if block.block_hash not in ever_served
        ]

    required_headers = required_wire_headers(chain)
    required_bodies = required_wire_bodies(chain) if require_bodies else []

    def missing() -> tuple[list[int], list[int]]:
        """Return the numbers of required headers and bodies never served."""
        return (
            missing_blocks(
                required_headers, mock_peer.header_hashes_ever_served
            ),
            missing_blocks(required_bodies, mock_peer.body_hashes_ever_served),
        )

    grace_ends = time.monotonic() + EVIDENCE_GRACE_TIME
    missing_headers, missing_bodies = missing()
    while (missing_headers or missing_bodies) and (
        time.monotonic() < grace_ends
    ):
        time.sleep(EVIDENCE_POLL_INTERVAL)
        missing_headers, missing_bodies = missing()

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
            "body/bodies were served to this client during an earlier "
            "test (byte-identical blocks)"
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


LATEST_VALID_HASH_CHECK = "latestValidHash check:"
"""
The prefix of every log line and failure of the `latestValidHash` check.

Each is followed by `match`, `null`, `mismatch` or `unchecked`, so a
Hive run's logs can be grepped for how each client answers.
"""


def check_latest_valid_hash(
    path: SyncPath,
    chain: Chain,
    payload_status: PayloadStatus,
    prefix: str,
) -> None:
    """
    Check the `latestValidHash` of a rejection of `path`'s head.

    An INVALID answer that names a latest valid hash must name the
    parent of the first invalid block on the path (see
    `SyncPath.expected_latest_valid_hash`); any other hash means the
    client blamed the wrong block, perhaps a valid ancestor. A null or
    all-zero hash, which the Engine API allows when the client cannot
    determine one, passes and is logged.
    """
    expected = path.expected_latest_valid_hash
    got = payload_status.latest_valid_hash
    status = payload_status.status

    def describe(block_hash: Hash) -> str:
        """Return `block_hash` with its block number on `chain`, if any."""
        if block_hash == chain.genesis.block_hash:
            return f"{block_hash} (block 0)"
        for block in chain.blocks:
            if block.block_hash == block_hash:
                return f"{block_hash} (block {block.number})"
        return f"{block_hash} (not on the served chain)"

    if got is None or got == Hash(0):
        logger.info(
            f"{prefix}{LATEST_VALID_HASH_CHECK} null: the client gave no "
            f"latest valid hash with {status} (latestValidHash {got})"
        )
        return
    if expected is None:
        logger.info(
            f"{prefix}{LATEST_VALID_HASH_CHECK} unchecked: no block on "
            f"the path is invalid, so the client's {describe(got)} has "
            "nothing to match"
        )
        return
    if got != expected:
        raise LoggedError(
            f"{prefix}{LATEST_VALID_HASH_CHECK} mismatch: the client "
            f"answered {status} with latestValidHash {describe(got)}, "
            f"expected {describe(expected)}, the parent of the first "
            "invalid block; the client blamed the wrong block"
        )
    logger.info(
        f"{prefix}{LATEST_VALID_HASH_CHECK} match: {describe(got)}, the "
        "parent of the first invalid block"
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

    Both wait loops read the client before checking the deadline: an
    Engine API call can block past the deadline, so the last action
    before giving up is always a fresh read.
    """
    path = case.path
    chain = case.chain
    head_payload = path.target
    head_hash = head_payload.params[0].block_hash
    expect_rejection = path.expects_rejection

    # Name the target in messages only when the fixture has several.
    prefix = f"{path.name}: " if path.total > 1 else ""
    if prefix:
        logger.info(
            f"Running {path.label}, expecting the branch to be "
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

    expected_head = chain.head.block_hash

    head_state = ForkchoiceState(
        head_block_hash=head_hash,
        safe_block_hash=genesis_header.block_hash,
        finalized_block_hash=genesis_header.block_hash,
    )

    def poll() -> PayloadStatus:
        """Send the head payload and return the client's verdict on it."""
        return engine_rpc.new_payload(
            *head_payload.params, version=head_payload.new_payload_version
        )

    def announce() -> PayloadStatus:
        """
        Send the head payload and name it in a forkchoice update.

        Return the `newPayload` status, which is the client's verdict:
        SYNCING while the ancestry travels, then VALID or INVALID.
        """
        payload_status = poll()
        engine_rpc.forkchoice_updated(
            forkchoice_state=head_state,
            payload_attributes=None,
            version=head_payload.forkchoice_updated_version,
        )
        return payload_status

    def redial(event: str) -> None:
        """
        Redial the client after it dropped the peer during `event`.

        A failed redial is logged, not raised: the client may refuse the
        new session for a moment (it has not reaped the old one, say),
        and the loop redials again at its next announcement, never
        sooner, since redialing faster has broken a client before.
        """
        logger.warning(
            f"{prefix}Peer dropped {event} (Disconnect reason "
            f"{mock_peer.disconnect_reason}); redialing"
        )
        try:
            mock_peer.reconnect(chain)
        except (OSError, RLPxError) as error:
            logger.warning(
                f"{prefix}Redial failed ({error}); retrying at the next "
                "announcement"
            )

    def ask(call: Callable[[], PayloadStatus]) -> PayloadStatus | None:
        """
        Return `call()`'s status, or `None` for the declared RPC refusal.

        Raise when the client refuses the head with another error code.
        """
        try:
            return call()
        except JSONRPCError as error:
            if head_payload.error_code is None:
                raise
            if error.code != head_payload.error_code:
                raise LoggedError(
                    f"{prefix}Client refused the head with the wrong error "
                    f"code: got {error.code}, expected "
                    f"{head_payload.error_code}"
                ) from error
            logger.info(
                f"{prefix}Client refused the invalid head at the RPC layer "
                f"with the expected error code {head_payload.error_code} "
                f"({error})"
            )
            return None

    with timing_data.time(f"{prefix}Announce sync target"):
        logger.info(
            f"{prefix}Announcing head block {chain.head.number} to "
            f"trigger a sync of {len(chain.blocks) - 1} ancestor "
            "block(s) over devp2p"
        )
        announce_status = ask(announce)
        if announce_status is None:
            return

    if expect_rejection:
        with timing_data.time(f"{prefix}Reject invalid chain"):
            deadline = time.monotonic() + sync_timeout
            next_announcement = time.monotonic() + announce_interval
            accepted_since: float | None = None

            def rejected(payload_status: PayloadStatus) -> bool:
                """
                Return whether `payload_status` rejects the head.

                A VALID answer starts (or continues) the acceptance
                hold and fails the test once it has held; anything
                else that is not a rejection resets the hold.
                """
                nonlocal accepted_since
                status = payload_status.status
                if status in REJECTED_STATUSES:
                    return True
                if status == PayloadStatusEnum.INVALID_BLOCK_HASH:
                    raise LoggedError(
                        f"{prefix}Client answered INVALID_BLOCK_HASH for "
                        f"the invalid head {expected_head}, whose payload "
                        "hashes to its blockHash (see REJECTED_STATUSES)"
                    )
                if status != PayloadStatusEnum.VALID:
                    accepted_since = None
                elif accepted_since is None:
                    # See `ACCEPTANCE_HOLD_TIME`.
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
                return False

            while True:
                # Once the ancestry has arrived over devp2p the client
                # can judge the head; until then it answers SYNCING (or
                # ACCEPTED if it merely stored the payload).
                payload_status = ask(poll)
                if payload_status is None:
                    return
                if rejected(payload_status):
                    break
                if time.monotonic() >= deadline:
                    break
                if time.monotonic() >= next_announcement:
                    if not mock_peer.alive:
                        # A client may drop a peer that served it a bad
                        # chain; a real peer would simply redial.
                        redial("mid-rejection")
                    logger.info(
                        f"{prefix}Re-announcing the invalid sync target"
                    )
                    payload_status = ask(announce)
                    if payload_status is None:
                        return
                    if rejected(payload_status):
                        break
                    next_announcement = time.monotonic() + announce_interval
                time.sleep(poll_interval)
            if payload_status.status not in REJECTED_STATUSES:
                raise LoggedError(
                    f"{prefix}Client never rejected the invalid head "
                    f"{expected_head} within {sync_timeout}s (last "
                    f"status: {payload_status.status}). Peer transcript: "
                    f"{mock_peer.statistics.transcript}"
                )
        statistics = mock_peer.statistics
        logger.info(
            f"{prefix}Client rejected the invalid head at block "
            f"{chain.head.number} with {payload_status.status} "
            f"(validationError: {payload_status.validation_error}) after "
            f"the peer served {statistics.headers_served} header(s) and "
            f"{statistics.bodies_served} body/bodies"
        )
        check_latest_valid_hash(path, chain, payload_status, prefix)
        if not path.announces_scaffolding:
            logger.info(
                f"{prefix}Not asserting wire coverage: this chain "
                "carries no framework sync target, so its own head was "
                "announced and the client may judge it without fetching "
                "an ancestor"
            )
            return
        # `any`, not `all`: a chain that may fail either way lets the
        # client take the header shortcut.
        header_judgeable = bool(
            path.invalidities & HEADER_JUDGEABLE_INVALIDITIES
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

    def raise_if_rejected(payload_status: PayloadStatus) -> None:
        """
        Fail at once when the client has refused the chain.

        An INVALID head means the client executed the ancestry and
        decided; waiting out the timeout would only lose its reason.
        """
        if payload_status.status in (
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
        # Watch for the block instead of repeating the forkchoice
        # update: each update restarts the client's sync cycle. The
        # announcement repeats on a slow cadence, as a consensus client
        # would each slot, for a client that ignored the first.
        raise_if_rejected(announce_status)
        deadline = time.monotonic() + sync_timeout
        next_announcement = time.monotonic() + announce_interval
        synced = False
        while True:
            if eth_rpc.get_block_by_hash(head_hash, full_txs=False):
                synced = True
                break
            if time.monotonic() >= deadline:
                break
            if time.monotonic() >= next_announcement:
                if not mock_peer.alive:
                    redial("mid-sync")
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
        if head_block["hash"] != str(expected_head):
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
        + (
            f", {statistics.bals_served} BAL(s) served "
            f"and {statistics.bals_withheld} withheld in "
            f"{statistics.bal_requests} request(s)"
            if statistics.bal_requests
            else ""
        )
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
    target_context_factory: TargetContextFactory,
    wirex_sync_timeout: float,
    wirex_poll_interval: float,
    wirex_announce_interval: float,
) -> None:
    """
    Make a client full sync, or reject, each of one test's sync targets.

    The first target runs on the `client` fixture, which the wirex client
    policy picks (see `wirex.client_policy`); each further target runs
    on its own isolated client from `target_context_factory`.
    """
    first = TargetContext(client, eth_rpc, engine_rpc, mock_peer)
    for index, case in enumerate(sync_target_cases):
        opened: AbstractContextManager[TargetContext] = (
            nullcontext(first) if index == 0 else target_context_factory(case)
        )
        with opened as context:
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
