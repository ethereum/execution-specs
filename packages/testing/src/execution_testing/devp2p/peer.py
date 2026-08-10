"""
The deterministic peer that serves fixture chains over devp2p.

The peer dials the client under test, completes the RLPx and eth
handshakes, and then answers header and body requests from whichever
fixture chain is currently installed. It is deliberately honest: it never
withholds, reorders or corrupts a response, so a sync failure is a
finding about the client or the fixture rather than about the peer.

Every request and response is recorded in a transcript, which is what
makes a stalled sync diagnosable after the fact.
"""

import logging
import threading
from dataclasses import dataclass, field
from typing import List, Optional, Set

from .chain import Chain, ServedChains
from .protocol import (
    BLOCK_BODIES,
    BLOCK_HEADERS,
    BLOCK_RANGE_UPDATE,
    DISCONNECT,
    GET_BLOCK_BODIES,
    GET_BLOCK_HEADERS,
    GET_RECEIPTS,
    HELLO,
    MESSAGE_NAMES,
    P2P_VERSION,
    PING,
    PONG,
    STATUS,
    BlockHeadersRequest,
    ProtocolError,
    Status,
    decode_disconnect,
    decode_get_block_bodies,
    decode_get_block_headers,
    decode_hello,
    encode_block_range_update,
    encode_hello,
    encode_response,
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

A count of items is no bound at all when one item may be megabytes, and
a client caps the size of every message it reads: geth refuses anything
over ten mebibytes and drops the peer rather than truncating it. Two
EIP-7934 blocks are roughly sixteen, so stop filling a response once it
reaches this many bytes and let the client ask for the rest. The value
is the one clients themselves stop at, and it is a target rather than a
cap: a single body is always served, however large it is alone.
"""

EMPTY_LIST_PAYLOAD = b"\xc0"


@dataclass
class PeerStatistics:
    """Counts of what a client asked for during one test."""

    header_requests: int = 0
    headers_served: int = 0
    body_requests: int = 0
    bodies_served: int = 0
    body_hashes_served: Set[bytes] = field(default_factory=set)
    """
    The block hashes whose bodies were served, not only their count.

    A count cannot tell the consumer *which* bodies traveled the wire,
    and its wire-coverage claim is per block: every block with a
    non-derivable body must have been downloaded from this peer, not
    just some block.
    """
    receipt_requests: int = 0
    unknown_requests: int = 0
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
    ) -> None:
        """Record where to dial and under which network identity."""
        self.host = host
        self.port = port
        self.remote_public_key = remote_public_key
        self.private_key = private_key
        self.network_id = network_id

        self._session: Optional[RLPxSession] = None
        self._chains = ServedChains()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.statistics = PeerStatistics()
        self.body_hashes_ever_served: Set[bytes] = set()
        """
        Every block hash whose body this peer served the client, across
        the peer's whole lifetime.

        `statistics.body_hashes_served` is reset for each test so its
        transcript stays attributable, but the client it describes is
        reused across a whole group of tests and keeps every block it
        ever imported. Two tests of one group may declare byte-identical
        chains, and the client re-syncs nothing for the second one - its
        blocks already traveled the wire during the first. This set is
        the evidence that they did: the consumer's wire-coverage check
        consults it, so a body is required to cross the wire once per
        client, not once per test.
        """
        self.remote_name = ""
        self.disconnect_reason: Optional[int] = None

    def connect(self, chain: Chain, timeout: float = 30.0) -> None:
        """
        Dial the client and complete both handshakes.

        `chain` is the chain advertised in the eth Status message and the
        one served until `set_chain` replaces it.
        """
        self._chains.install(chain)
        session = connect(
            self.host,
            self.port,
            self.remote_public_key,
            self.private_key,
            timeout=timeout,
        )
        self._session = session

        session.write_message(
            HELLO,
            encode_hello(
                CLIENT_IDENTIFIER, public_key_bytes(self.private_key)
            ),
        )
        code, payload = session.read_message()
        if code == DISCONNECT:
            raise RLPxError(
                f"client refused the connection: reason "
                f"{decode_disconnect(payload)}"
            )
        if code != HELLO:
            raise RLPxError(f"expected Hello, got message {code}")
        remote_version, self.remote_name, capabilities = decode_hello(payload)
        logger.info(
            "Connected to %s (p2p version %d) advertising %s",
            self.remote_name,
            remote_version,
            capabilities,
        )
        if min(remote_version, P2P_VERSION) >= 5:
            # Every message after Hello is Snappy compressed once both
            # sides have advertised base protocol version 5 or higher.
            session.enable_snappy()

        session.write_message(STATUS, self._status(chain).encode())
        session.set_timeout(1.0)

    def _status(self, chain: Chain) -> Status:
        """Return the Status message describing `chain`."""
        return Status(
            network_id=self.network_id,
            genesis_hash=bytes(chain.genesis.block_hash),
            fork_activations=[],
            earliest_block=0,
            latest_block=chain.head.number,
            latest_block_hash=chain.head.block_hash,
        )

    def start(self) -> None:
        """Start the background message loop."""
        self._thread = threading.Thread(
            target=self._run, name="wirex-peer", daemon=True
        )
        self._thread.start()

    def set_chain(self, chain: Chain) -> None:
        """
        Serve `chain` from now on and announce its range.

        Installing a new chain is how one client is reused across the
        tests of a pre-allocation group: each test is an independent
        chain from the same genesis.
        """
        with self._lock:
            self._chains.install(chain)
            self.statistics = PeerStatistics()
            session = self._session
        if session is not None:
            session.write_message(
                BLOCK_RANGE_UPDATE,
                encode_block_range_update(
                    0, chain.head.number, chain.head.block_hash
                ),
            )

    def _run(self) -> None:
        """Read and answer messages until stopped or disconnected."""
        session = self._session
        assert session is not None
        while not self._stop.is_set():
            try:
                code, payload = session.read_message()
            except (TimeoutError, OSError):
                continue
            except RLPxError as error:
                logger.info("Peer connection ended: %s", error)
                return

            try:
                self._handle(session, code, payload)
            except OSError as error:
                # The client closed the socket while the answer was
                # being written. End the loop cleanly rather than
                # leaving a traceback in a thread nobody joins.
                logger.info(
                    "Peer connection ended while answering message %d: %s",
                    code,
                    error,
                )
                return
            except (ProtocolError, RLPxError) as error:
                logger.warning("Failed to answer message %d: %s", code, error)
                return

    def _handle(self, session: RLPxSession, code: int, payload: bytes) -> None:
        """Answer one message from the client."""
        if code == PING:
            session.write_message(PONG, EMPTY_LIST_PAYLOAD)
        elif code == GET_BLOCK_HEADERS:
            self._serve_headers(session, decode_get_block_headers(payload))
        elif code == GET_BLOCK_BODIES:
            self._serve_bodies(session, *decode_get_block_bodies(payload))
        elif code == GET_RECEIPTS:
            # A full syncing client derives receipts by executing the
            # block, so a request here means the client chose a path this
            # peer cannot serve. Leave it unanswered and make it visible.
            with self._lock:
                self.statistics.receipt_requests += 1
                self.statistics.record("GetReceipts (unanswered)")
            logger.warning("Client requested receipts; not served")
        elif code == DISCONNECT:
            self.disconnect_reason = decode_disconnect(payload)
            logger.info(
                "Client disconnected: reason %d", self.disconnect_reason
            )
        elif code in (STATUS, HELLO, PONG):
            pass
        else:
            with self._lock:
                self.statistics.unknown_requests += 1
            logger.debug(
                "Ignoring %s", MESSAGE_NAMES.get(code, f"message {code}")
            )

    def _serve_headers(
        self, session: RLPxSession, request: BlockHeadersRequest
    ) -> None:
        """Answer a GetBlockHeaders request from the current chain."""
        with self._lock:
            # The test's statistics object is captured under the lock:
            # `set_chain` swaps in a fresh one when the next test
            # starts, and a straggler request from the previous test
            # must land in the previous test's statistics, not poison
            # the next test's transcript (or satisfy its wire-coverage
            # check with another chain's bodies).
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

        # Written before recording, for the same reason as in
        # `_serve_bodies`: a failed send must not read as service.
        session.write_message(
            BLOCK_HEADERS, encode_response(request.request_id, headers)
        )

        with self._lock:
            statistics.headers_served += len(headers)
            statistics.record(
                f"{request.describe()} -> {len(headers)} headers"
            )

    def _serve_bodies(
        self, session: RLPxSession, request_id: int, hashes: List[bytes]
    ) -> None:
        """
        Answer a GetBlockBodies request from the served chains.

        A hash this peer does not hold is skipped, as the eth wire
        protocol allows and real peers do; every held body in the
        request is still served, up to the response bounds. Ending
        the response at the first unknown hash instead would withhold
        held bodies whenever a client mixes hashes from an abandoned
        chain into a request, and starve its sync.
        """
        with self._lock:
            # Captured for the same straggler-attribution reason as in
            # `_serve_headers`.
            statistics = self.statistics
            statistics.body_requests += 1
            chain = self._chains.current

        bodies: List[bytes] = []
        served_hashes: List[bytes] = []
        unknown: List[bytes] = []
        served_bytes = 0
        for block_hash in hashes[:MAX_BODIES_PER_RESPONSE]:
            if served_bytes >= SOFT_RESPONSE_LIMIT:
                break
            body = self._chains.body_rlp_by_hash(block_hash)
            if body is None:
                unknown.append(block_hash)
                continue
            bodies.append(body)
            served_hashes.append(block_hash)
            served_bytes += len(body)

        # The response is written before anything is recorded as served:
        # `body_hashes_served` is the evidence behind the consumer's
        # per-block wire-coverage assertion, and a `write_message` that
        # raises mid-send must not leave statistics claiming the bodies
        # reached the client.
        session.write_message(
            BLOCK_BODIES, encode_response(request_id, bodies)
        )

        with self._lock:
            statistics.bodies_served += len(bodies)
            statistics.body_hashes_served.update(served_hashes)
            self.body_hashes_ever_served.update(served_hashes)
            detail = (
                ""
                if not unknown
                else f", {len(unknown)} unknown, first "
                f"0x{unknown[0].hex()[:16]} (chain head "
                f"#{chain.head.number} 0x{chain.head.block_hash.hex()[:16]})"
            )
            statistics.record(
                f"bodies for {len(hashes)} hashes -> "
                f"{len(bodies)} served ({served_bytes} bytes){detail}"
            )

    def close(self) -> None:
        """Stop the message loop and close the connection."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        if self._session is not None:
            self._session.close()
