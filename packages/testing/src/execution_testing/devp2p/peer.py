"""
The peer that dials the client under test and serves it fixture chains.

After the RLPx and eth handshakes the peer answers header and body
requests from whichever fixture chain is installed. It is deliberately
honest: it never withholds, reorders or corrupts a response, so a sync
failure is a finding about the client or the fixture, not the peer.

Every request and response is recorded in a transcript, which makes a
stalled sync diagnosable after the fact.
"""

import logging
import threading
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Set

from ethereum_rlp.exceptions import DecodingError

from execution_testing.base_types import Bytes, Hash

from .chain import Chain, ServedChains
from .protocol import (
    ETH_PROTOCOLS,
    GENESIS_FORK_ONLY,
    P2P_VERSION,
    BlockHeadersRequest,
    EthProtocol,
    EthVersion,
    ForkSchedule,
    MessageCode,
    ProtocolError,
    Status,
    decode_disconnect,
    decode_get_block_access_lists,
    decode_get_block_bodies,
    decode_get_block_headers,
    decode_hello,
    encode_block_range_update,
    encode_hello,
    encode_response,
    fork_id,
    highest_common_eth_version,
)
from .rlpx import RLPxError, RLPxSession, connect
from .secp256k1 import public_key_bytes

logger = logging.getLogger(__name__)

CLIENT_IDENTIFIER = "wirex-peer/v0"
"""Client identifier advertised in the base protocol handshake."""

MAX_HEADERS_PER_RESPONSE = 1024
"""Cap on headers served in one response, matching common client limits."""

MAX_BODIES_PER_RESPONSE = 256
"""Cap on bodies served in one response."""

SOFT_RESPONSE_LIMIT = 2 * 1024 * 1024
"""
Target ceiling on the serialized bytes of one response.

Clients cap the size of every message they read (geth drops a peer over
10 MiB) and two EIP-7934 blocks reach about 16 MiB, so a count of items
is no bound. A target, not a cap: a single body is always served.
"""

HANDSHAKE_TIMEOUT = 10.0
"""
Seconds each handshake step may take: the TCP dial, each read of the
RLPx ack, and the client's Hello.

A client answers these in milliseconds (geth gives a peer 5 s for its
whole handshake), so a silent client fails a dial in seconds rather than
holding a redial for the whole sync timeout.
"""

EMPTY_LIST_PAYLOAD = b"\xc0"

UNAVAILABLE_BAL = b"\x80"
"""The EIP-8159 entry for a BAL a peer does not hold: the RLP empty string."""


@dataclass
class PeerStatistics:
    """
    What a client asked for during one test, and what it was served.

    The `*_hashes_served` sets are the evidence behind the consumer's
    per-block wire coverage check, so a hash is recorded only after its
    response was written: a write that raises is not service.
    """

    header_requests: int = 0
    headers_served: int = 0
    header_hashes_served: Set[Hash] = field(default_factory=set)
    """Block hashes whose headers were served."""
    body_requests: int = 0
    bodies_served: int = 0
    body_hashes_served: Set[Hash] = field(default_factory=set)
    """Block hashes whose bodies were served."""
    bal_requests: int = 0
    bals_served: int = 0
    bals_withheld: int = 0
    """BALs held but answered as unavailable."""
    receipt_requests: int = 0
    """GetReceipts requests, each answered with none; nonzero is a finding."""
    transcript: List[str] = field(default_factory=list)

    def record(self, line: str) -> None:
        """Append `line` to the request transcript."""
        self.transcript.append(line)


class MockPeer:
    """
    A single connection to the client under test.

    The peer runs its message loop on a background thread so that the
    test body can drive the Engine API while the client is downloading
    the chain.
    """

    def __init__(
        self,
        host: str,
        port: int,
        remote_public_key: bytes,
        private_key: bytes,
        network_id: int,
        eth_versions: Sequence[EthVersion] | None = None,
        serve_bals: bool = False,
        fork_schedule: ForkSchedule = GENESIS_FORK_ONLY,
    ) -> None:
        """
        Record where to dial and under which network identity.

        `eth_versions` defaults to every implemented version; a single
        version makes a client that lacks it fail the handshake.

        `serve_bals` answers GetBlockAccessLists with the BALs, which a
        client may use to execute a block's transactions in parallel; by
        default every entry is answered as unavailable.

        `fork_schedule` is when the network the client runs forks after
        genesis; the Status fork identifier is computed from it, so a
        client past a fork accepts the peer (EIP-2124).
        """
        self.host = host
        self.port = port
        self.remote_public_key = remote_public_key
        self.private_key = private_key
        self.network_id = network_id
        self.serve_bals = serve_bals
        self.fork_schedule = fork_schedule
        if eth_versions is None:
            eth_versions = tuple(ETH_PROTOCOLS)
        unknown = set(eth_versions).difference(ETH_PROTOCOLS)
        if unknown:
            raise ValueError(
                f"unimplemented eth version(s) {sorted(unknown)}; "
                f"implemented: {sorted(map(int, ETH_PROTOCOLS))}"
            )
        self.eth_versions = tuple(sorted(EthVersion(v) for v in eth_versions))
        self.protocol: Optional[EthProtocol] = None

        self._session: Optional[RLPxSession] = None
        self._chains = ServedChains()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._dead = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.statistics = PeerStatistics()
        self.body_hashes_ever_served: Set[Hash] = set()
        """
        Every body hash served over the peer's lifetime.

        The client is reused across a group and keeps every block it
        imported, so a later test declaring the same chain syncs
        nothing: a block has to cross the wire once per client, not
        once per test.
        """
        self.header_hashes_ever_served: Set[Hash] = set()
        """Every header hash served over the peer's lifetime (as above)."""
        self.remote_name = ""
        self.disconnect_reason: Optional[int] = None

    @property
    def alive(self) -> bool:
        """Whether the connection's message loop is still running."""
        return self._thread is not None and not self._dead.is_set()

    def connect(
        self, chain: Chain, timeout: float = HANDSHAKE_TIMEOUT
    ) -> None:
        """
        Dial the client and complete both handshakes.

        `chain` is the chain advertised in the eth Status message and the
        one served until `set_chain` replaces it. `timeout` bounds each
        handshake step, the client's Hello included.
        """
        with self._lock:
            # A straggling loop from the previous session may still be
            # reading the served chains.
            self._chains.install(chain)
        session = connect(
            self.host,
            self.port,
            self.remote_public_key,
            self.private_key,
            timeout=timeout,
        )
        self._session = session
        try:
            self._complete_protocol_handshakes(session, chain, timeout)
        except Exception:
            # A session that fails its devp2p handshakes is closed at
            # once rather than left open until the next redial.
            session.close()
            raise

    def _complete_protocol_handshakes(
        self, session: RLPxSession, chain: Chain, timeout: float
    ) -> None:
        """
        Complete the base protocol Hello and the eth Status exchange.

        A Hello (or Disconnect) that does not decode raises `RLPxError`,
        as a malformed RLPx handshake does, so a caller handles it like
        any other refused dial.
        """
        try:
            self._exchange_hello_and_status(session, chain, timeout)
        except (ProtocolError, DecodingError) as error:
            raise RLPxError(
                f"malformed devp2p handshake: {error!r}"
            ) from error

    def _exchange_hello_and_status(
        self, session: RLPxSession, chain: Chain, timeout: float
    ) -> None:
        """Send Hello, read the client's Hello, then send Status."""
        session.set_timeout(timeout)
        session.write_message(
            MessageCode.HELLO,
            encode_hello(
                CLIENT_IDENTIFIER,
                public_key_bytes(self.private_key),
                self.eth_versions,
            ),
        )
        code, payload = session.read_message()
        if code == MessageCode.DISCONNECT:
            raise RLPxError(
                f"client refused the connection: reason "
                f"{decode_disconnect(payload)}"
            )
        if code != MessageCode.HELLO:
            raise RLPxError(f"expected Hello, got message {code}")
        remote_version, self.remote_name, capabilities = decode_hello(payload)
        logger.info(
            "Connected to %s (p2p version %d) advertising %s",
            self.remote_name,
            remote_version,
            capabilities,
        )
        negotiated = highest_common_eth_version(
            self.eth_versions, capabilities
        )
        if negotiated is None:
            raise RLPxError(
                f"no common eth version: this peer advertises "
                f"{list(map(int, self.eth_versions))}, "
                f"{self.remote_name or 'client'} "
                f"advertises {capabilities}"
            )
        self.protocol = ETH_PROTOCOLS[negotiated]
        logger.info("Negotiated eth/%d", negotiated)
        with self._lock:
            self.statistics.record(f"eth/{negotiated} negotiated")
        if min(remote_version, P2P_VERSION) >= 5:
            session.enable_snappy()

        session.write_message(
            MessageCode.STATUS,
            self.protocol.encode_status(self._status(chain)),
        )
        session.set_timeout(1.0)

    def _status(self, chain: Chain) -> Status:
        """
        Return the Status message describing `chain`.

        The fork identifier is the one of `chain`'s head, so each
        redial describes the chain served at that moment.
        """
        return Status(
            network_id=self.network_id,
            genesis_hash=chain.genesis.block_hash,
            fork_id=fork_id(
                chain.genesis.block_hash,
                self.fork_schedule,
                genesis_timestamp=int(chain.genesis.timestamp),
                head_number=chain.head.number,
                head_timestamp=int(chain.head.header.timestamp),
            ),
            earliest_block=0,
            latest_block=chain.head.number,
            latest_block_hash=chain.head.block_hash,
        )

    def start(self) -> None:
        """
        Start the background message loop.

        Every loop gets its own stop and dead events: a loop that
        outlived its session's close (stuck in a long write, say) must
        never mark the next session dead, nor see its stop cleared.
        """
        self._stop = threading.Event()
        self._dead = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            args=(self._session, self._stop, self._dead),
            name="wirex-peer",
            daemon=True,
        )
        self._thread.start()

    def set_chain(self, chain: Chain) -> None:
        """Serve `chain` from now on and announce its range."""
        with self._lock:
            self._chains.install(chain)
            self.statistics = self._fresh_statistics()
            session = self._session
        if session is not None:
            session.write_message(
                MessageCode.BLOCK_RANGE_UPDATE,
                encode_block_range_update(
                    0, chain.head.number, chain.head.block_hash
                ),
            )

    def served_chain_holding(self, block_hash: Hash) -> Optional[Chain]:
        """
        Return a chain this peer served that holds `block_hash`, if any.

        Chains that share a block share its whole ancestry, so whichever
        one is returned describes the block's ancestors exactly.
        """
        with self._lock:
            return self._chains.chain_for_hash(block_hash)

    def reset_statistics(self) -> None:
        """
        Start fresh statistics for the next test.

        `set_chain` does this itself; `reconnect` does not, so a redial
        mid-test keeps the test's transcript.
        """
        with self._lock:
            self.statistics = self._fresh_statistics()

    def _fresh_statistics(self) -> PeerStatistics:
        """Return empty statistics naming the negotiated eth version."""
        statistics = PeerStatistics()
        if self.protocol is not None:
            statistics.record(f"eth/{self.protocol.version} negotiated")
        return statistics

    def reconnect(
        self, chain: Chain, timeout: float = HANDSHAKE_TIMEOUT
    ) -> None:
        """
        Dial the client again after it dropped the previous session.

        A client is free to hang up on a peer at any time (nethermind
        does, with `Disconnect(0x00)`). Served chains stay installed
        (see `ServedChains`). A failed redial raises and leaves the peer
        reading as dead, so the caller may simply try again.
        """
        self.close()
        self._thread = None
        self.disconnect_reason = None
        self.connect(chain, timeout=timeout)
        self.start()

    def _run(
        self,
        session: Optional[RLPxSession],
        stop: threading.Event,
        dead: threading.Event,
    ) -> None:
        """Read and answer messages until stopped or disconnected."""
        assert session is not None
        # Every exit ends the loop rather than raising: the owner sees a
        # dead session through `alive` and redials, no traceback is left
        # in a thread nobody joins, and no socket is left open.
        try:
            while not stop.is_set():
                try:
                    code, payload = session.read_message()
                except TimeoutError:
                    continue
                except (OSError, RLPxError, ValueError) as error:
                    # `ValueError` is a socket closed under the loop.
                    logger.info("Peer connection ended: %s", error)
                    return

                try:
                    self._handle(session, code, payload)
                except OSError as error:
                    # The client closed the socket mid-answer.
                    logger.info(
                        "Peer connection ended while answering message %d: %s",
                        code,
                        error,
                    )
                    return
                except (ProtocolError, RLPxError) as error:
                    logger.warning(
                        "Failed to answer message %d: %s", code, error
                    )
                    return
                except Exception:
                    # A request the decoders could not make sense of.
                    logger.exception("Failed to answer message %d", code)
                    return
                if code == MessageCode.DISCONNECT:
                    return
        finally:
            session.close()
            dead.set()

    def _handle(self, session: RLPxSession, code: int, payload: bytes) -> None:
        """Answer one message from the client."""
        protocol = self.protocol
        assert protocol is not None, "message received before negotiation"
        if code == MessageCode.PING:
            session.write_message(MessageCode.PONG, EMPTY_LIST_PAYLOAD)
        elif code == MessageCode.GET_BLOCK_HEADERS:
            self._serve_headers(session, decode_get_block_headers(payload))
        elif code == MessageCode.GET_BLOCK_BODIES:
            self._serve_bodies(session, *decode_get_block_bodies(payload))
        elif code == MessageCode.GET_BLOCK_ACCESS_LISTS and protocol.has_bals:
            self._answer_bals(session, *decode_get_block_access_lists(payload))
        elif code == MessageCode.GET_RECEIPTS:
            # A full syncing client derives receipts by executing the
            # block; serving them would let a failing test pass with no
            # coverage. Answer that none are held, rather than leave the
            # request to time out, and make it visible.
            request = protocol.decode_get_receipts(payload)
            session.write_message(
                MessageCode.RECEIPTS,
                protocol.encode_no_receipts(request.request_id),
            )
            with self._lock:
                self.statistics.receipt_requests += 1
                self.statistics.record(f"{request.describe()} (none held)")
            logger.warning("Client requested GetReceipts; answered none held")
        elif code == MessageCode.DISCONNECT:
            reason = decode_disconnect(payload)
            logger.info("Client disconnected: reason %s", reason)
            # Only the current session's loop speaks for the peer: a
            # loop that outlived its session (see `start`) must not
            # report its reason for the redialed one.
            if session is self._session:
                self.disconnect_reason = reason
        else:
            logger.debug("Ignoring message %d", code)

    def _serve_headers(
        self, session: RLPxSession, request: BlockHeadersRequest
    ) -> None:
        """Answer a GetBlockHeaders request from the current chain."""
        with self._lock:
            # Captured under the lock: a straggler from the previous
            # test must land in that test's statistics, not this one's.
            statistics = self.statistics
            statistics.header_requests += 1
            if request.origin_hash is None:
                chain = self._chains.current
                start = request.origin_number
            else:
                origin_chain = self._chains.chain_for_hash(request.origin_hash)
                chain = (
                    self._chains.current
                    if origin_chain is None
                    else origin_chain
                )
                start = chain.number_of(request.origin_hash)

        headers: List[bytes] = []
        if start is not None:
            step = request.skip + 1
            number = start
            while len(headers) < min(request.amount, MAX_HEADERS_PER_RESPONSE):
                header = chain.header_rlp_by_number(number)
                if header is None:
                    break
                headers.append(header)
                number = number - step if request.reverse else number + step
                if number < 0:
                    break

        session.write_message(
            MessageCode.BLOCK_HEADERS,
            encode_response(request.request_id, headers),
        )

        # A block's hash is the keccak of its header, so the recorded
        # evidence is computed from the exact bytes that traveled.
        served_hashes = [Bytes(header).keccak256() for header in headers]

        with self._lock:
            statistics.headers_served += len(headers)
            statistics.header_hashes_served.update(served_hashes)
            self.header_hashes_ever_served.update(served_hashes)
            statistics.record(
                f"{request.describe()} -> {len(headers)} headers"
            )

    def _serve_bodies(
        self, session: RLPxSession, request_id: int, hashes: List[Hash]
    ) -> None:
        """
        Answer a GetBlockBodies request from the served chains.

        The response ends at the first hash this peer does not hold, as
        geth and reth end theirs: a client matches bodies to its request
        by position, so skipping a hash would shift every later body
        onto the wrong header and make the whole response invalid. Every
        chain served by this peer stays held (see `ServedChains`), even
        across redials, so an unknown hash is one this peer never had.
        """
        with self._lock:
            statistics = self.statistics
            statistics.body_requests += 1
            chain = self._chains.current

        bodies: List[bytes] = []
        served_hashes: List[Hash] = []
        unknown: Hash | None = None
        served_bytes = 0
        for block_hash in hashes[:MAX_BODIES_PER_RESPONSE]:
            if served_bytes >= SOFT_RESPONSE_LIMIT:
                break
            body = self._chains.body_rlp_by_hash(block_hash)
            if body is None:
                unknown = block_hash
                break
            bodies.append(body)
            served_hashes.append(block_hash)
            served_bytes += len(body)

        # Recorded only after the write succeeds (see `PeerStatistics`).
        session.write_message(
            MessageCode.BLOCK_BODIES, encode_response(request_id, bodies)
        )

        with self._lock:
            statistics.bodies_served += len(bodies)
            statistics.body_hashes_served.update(served_hashes)
            self.body_hashes_ever_served.update(served_hashes)
            detail = (
                ""
                if unknown is None
                else f", stopped at unknown {unknown.hex()[:18]} (chain "
                f"head #{chain.head.number} "
                f"{chain.head.block_hash.hex()[:18]})"
            )
            statistics.record(
                f"bodies for {len(hashes)} hashes -> "
                f"{len(bodies)} served ({served_bytes} bytes){detail}"
            )

    def _answer_bals(
        self, session: RLPxSession, request_id: int, hashes: List[Hash]
    ) -> None:
        """
        Answer a GetBlockAccessLists request from the served chains.

        Entries are positional (EIP-8159): one per requested hash, the
        RLP empty string for a BAL not held or withheld. Silence is not
        an option, as clients penalize a peer that leaves these
        requests unanswered. The response stops at the soft byte limit,
        like bodies.
        """
        with self._lock:
            statistics = self.statistics
            statistics.bal_requests += 1

        entries: List[bytes] = []
        served = 0
        withheld = 0
        served_bytes = 0
        for block_hash in hashes[:MAX_BODIES_PER_RESPONSE]:
            if served_bytes >= SOFT_RESPONSE_LIMIT:
                break
            bal = self._chains.bal_rlp_by_hash(block_hash)
            if bal is None:
                entries.append(UNAVAILABLE_BAL)
                continue
            if not self.serve_bals:
                entries.append(UNAVAILABLE_BAL)
                withheld += 1
                continue
            entries.append(bal)
            served += 1
            served_bytes += len(bal)

        session.write_message(
            MessageCode.BLOCK_ACCESS_LISTS,
            encode_response(request_id, entries),
        )

        with self._lock:
            statistics.bals_served += served
            statistics.bals_withheld += withheld
            statistics.record(
                f"BALs for {len(hashes)} hashes -> {served} "
                f"served ({served_bytes} bytes), {withheld} withheld"
            )

    def close(self) -> None:
        """Stop the message loop and close the connection."""
        self._stop.set()
        # Closing first wakes a loop blocked on the socket at once;
        # joining first would wait out its read timeout.
        if self._session is not None:
            self._session.close()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
