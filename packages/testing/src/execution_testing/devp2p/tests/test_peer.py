"""
Tests for how the peer bounds the responses it serves.

A response is bounded by serialized bytes, not only by a count of items.
Clients cap the size of every message they read - geth's `maxMessageSize`
is ten mebibytes, and exceeding it drops the peer rather than truncating
the message - so two multi-megabyte bodies have to travel as two
responses. EIP-7934 caps a block at eight mebibytes, which puts two of
them in one response over that cap, and blocks that large are exactly
what the `eip7934_block_rlp_limit` fixtures serve.
"""

import socket
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, cast

import ethereum_rlp as eth_rlp
import pytest
from ethereum_types.numeric import Uint

from ..keccak import keccak256
from ..peer import (
    BLOCK_BODIES,
    MAX_BODIES_PER_RESPONSE,
    SOFT_RESPONSE_LIMIT,
    UNAVAILABLE_ACCESS_LIST,
    MockPeer,
)
from ..protocol import (
    BLOCK_ACCESS_LISTS,
    ETH_PROTOCOLS,
    GET_BLOCK_ACCESS_LISTS,
    GET_RECEIPTS,
    BlockHeadersRequest,
)
from ..rlpx import MAX_FRAME_SIZE, RLPxError, RLPxSession

LARGE_BODY_SIZE = 8 * 1024 * 1024
"""A body the size EIP-7934 allows a block to reach."""


def _hash(index: int) -> bytes:
    """Return a distinct block hash for `index`."""
    return index.to_bytes(32, "big")


@dataclass
class _StubHead:
    """The head fields the peer reads when a hash is unknown."""

    number: int = 1
    block_hash: bytes = b"\xaa" * 32


@dataclass
class _StubChain:
    """A chain that only has to answer for its head."""

    head: _StubHead = field(default_factory=_StubHead)


class _StubChains:
    """The bodies a peer holds, keyed by block hash."""

    def __init__(self, bodies: Dict[bytes, bytes]) -> None:
        """Hold `bodies` and present a chain to report as current."""
        self._bodies = bodies
        self.current = _StubChain()

    def install(self, chain: Any) -> None:
        """Accept a new chain without changing the held bodies."""
        del chain

    def body_rlp_by_hash(self, block_hash: bytes) -> bytes | None:
        """Return the body held under `block_hash`, if any."""
        return self._bodies.get(block_hash)


class _RecordingSession:
    """A session that keeps what was written instead of sending it."""

    def __init__(self) -> None:
        """Start with nothing written."""
        self.messages: List[Tuple[int, bytes]] = []

    def write_message(self, code: int, payload: bytes) -> None:
        """Record one message."""
        self.messages.append((code, payload))


class _FailingSession:
    """A session whose socket dies on every write."""

    def write_message(self, code: int, payload: bytes) -> None:
        """Fail the way a closed socket fails `sendall`."""
        del code, payload
        raise OSError(32, "Broken pipe")


def _serve(bodies: Dict[bytes, bytes], hashes: List[bytes]) -> int:
    """
    Ask a peer holding `bodies` for `hashes`, and return how many it sent.

    The response is counted rather than decoded: these payloads reach
    megabytes, and a pure Python RLP decode of one takes long enough to
    dominate the suite.
    """
    peer = MockPeer(
        host="127.0.0.1",
        port=30303,
        remote_public_key=b"\x00" * 64,
        private_key=b"\x01" * 32,
        network_id=1,
    )
    peer._chains = cast(Any, _StubChains(bodies))
    session = _RecordingSession()
    peer._serve_bodies(cast(RLPxSession, session), 1, hashes)

    assert len(session.messages) == 1
    code, payload = session.messages[0]
    assert code == BLOCK_BODIES
    served = peer.statistics.bodies_served
    # The response carries every served body and nothing else of size.
    # Unknown hashes are skipped, so the served bodies are the first
    # `served` known hashes of the request.
    known = [block_hash for block_hash in hashes if block_hash in bodies]
    expected = sum(len(bodies[block_hash]) for block_hash in known[:served])
    assert expected <= len(payload) <= expected + 16
    # Exactly the served hashes are recorded - the per-block coverage
    # the consumer asserts - never an unknown or a bounded-out one.
    assert peer.statistics.body_hashes_served == set(known[:served])
    return served


class TestBodyResponseSize:
    """One response never carries more bytes than a client will read."""

    def test_two_large_bodies_are_split(self) -> None:
        """Two eight mebibyte bodies do not share one response."""
        bodies = {
            _hash(1): b"\x00" * LARGE_BODY_SIZE,
            _hash(2): b"\x00" * LARGE_BODY_SIZE,
        }
        assert _serve(bodies, [_hash(1), _hash(2)]) == 1

    def test_one_oversized_body_is_still_served(self) -> None:
        """A body larger than the limit is served rather than withheld."""
        body = b"\x00" * LARGE_BODY_SIZE
        assert len(body) > SOFT_RESPONSE_LIMIT
        assert _serve({_hash(1): body}, [_hash(1)]) == 1

    def test_small_bodies_share_one_response(self) -> None:
        """Bodies that fit are still batched, as they always were."""
        bodies = {_hash(index): bytes([index]) for index in range(1, 33)}
        assert _serve(bodies, sorted(bodies)) == 32

    def test_unknown_hash_is_skipped(self) -> None:
        """An unheld hash is skipped; held bodies after it still serve."""
        bodies = {_hash(1): b"\x01", _hash(3): b"\x03"}
        assert _serve(bodies, [_hash(1), _hash(2), _hash(3)]) == 2

    def test_item_cap_still_applies(self) -> None:
        """The count cap bounds a request for many tiny bodies."""
        wanted = MAX_BODIES_PER_RESPONSE + 10
        bodies = {_hash(index): b"\x01" for index in range(wanted)}
        hashes = [_hash(index) for index in range(wanted)]
        assert _serve(bodies, hashes) == MAX_BODIES_PER_RESPONSE

    def test_lifetime_service_survives_a_chain_switch(self) -> None:
        """
        `body_hashes_ever_served` accumulates across `set_chain`.

        The per-test statistics reset with every chain switch, but the
        reused client keeps every block it imported, so the evidence
        that a body once traveled the wire must outlive the test that
        made it travel: a later test declaring a byte-identical chain
        syncs nothing, and its coverage check reads this set.
        """
        peer = MockPeer(
            host="127.0.0.1",
            port=30303,
            remote_public_key=b"\x00" * 64,
            private_key=b"\x01" * 32,
            network_id=1,
        )
        peer._chains = cast(Any, _StubChains({_hash(1): b"\x01"}))
        peer._serve_bodies(
            cast(RLPxSession, _RecordingSession()), 1, [_hash(1)]
        )
        assert peer.statistics.body_hashes_served == {_hash(1)}

        peer.set_chain(cast(Any, _StubChain()))
        assert peer.statistics.body_hashes_served == set()
        assert peer.body_hashes_ever_served == {_hash(1)}

    def test_failed_write_records_nothing_as_served(self) -> None:
        """
        A response whose socket write raises is not service.

        `body_hashes_served` is the evidence behind the consumer's
        per-block wire-coverage assertion, so a body that never left
        the peer must not appear in it - and the transcript must not
        claim it was served. The request itself is still counted: it
        arrived, whatever became of the answer.
        """
        peer = MockPeer(
            host="127.0.0.1",
            port=30303,
            remote_public_key=b"\x00" * 64,
            private_key=b"\x01" * 32,
            network_id=1,
        )
        peer._chains = cast(Any, _StubChains({_hash(1): b"\x01"}))
        with pytest.raises(OSError):
            peer._serve_bodies(
                cast(RLPxSession, _FailingSession()), 1, [_hash(1)]
            )
        assert peer.statistics.body_requests == 1
        assert peer.statistics.bodies_served == 0
        assert peer.statistics.body_hashes_served == set()
        assert peer.body_hashes_ever_served == set()
        assert not any("served" in line for line in peer.statistics.transcript)


@dataclass
class _StubHeaderChain:
    """A chain that answers header requests by number."""

    headers: Dict[int, bytes]

    def header_rlp_by_number(self, number: int) -> bytes | None:
        """Return the header RLP held under `number`, if any."""
        return self.headers.get(number)


def _headers_request(number: int) -> BlockHeadersRequest:
    """Return a request for the single header at `number`."""
    return BlockHeadersRequest(
        request_id=7,
        origin_hash=None,
        origin_number=number,
        amount=1,
        skip=0,
        reverse=False,
    )


def _peer_with_headers(headers: Dict[int, bytes]) -> MockPeer:
    """Return a peer whose current chain serves exactly `headers`."""
    peer = MockPeer(
        host="127.0.0.1",
        port=30303,
        remote_public_key=b"\x00" * 64,
        private_key=b"\x01" * 32,
        network_id=1,
    )
    chains = _StubChains({})
    chains.current = cast(Any, _StubHeaderChain(headers))
    peer._chains = cast(Any, chains)
    return peer


class TestHeaderServiceEvidence:
    """Served headers are recorded per block hash, like bodies."""

    def test_served_headers_are_recorded_by_hash(self) -> None:
        """The evidence is the keccak of the exact bytes served."""
        header = b"\x02" * 100
        peer = _peer_with_headers({1: header})
        peer._serve_headers(
            cast(RLPxSession, _RecordingSession()), _headers_request(1)
        )
        assert peer.statistics.headers_served == 1
        assert peer.statistics.header_hashes_served == {keccak256(header)}
        assert peer.header_hashes_ever_served == {keccak256(header)}

    def test_lifetime_service_survives_a_chain_switch(self) -> None:
        """
        `header_hashes_ever_served` accumulates across `set_chain`,
        exactly as the body evidence does and for the same reason: a
        header is required to cross the wire once per client, not once
        per test.
        """
        header = b"\x03" * 100
        peer = _peer_with_headers({1: header})
        peer._serve_headers(
            cast(RLPxSession, _RecordingSession()), _headers_request(1)
        )
        assert peer.statistics.header_hashes_served == {keccak256(header)}

        peer.set_chain(cast(Any, _StubChain()))
        assert peer.statistics.header_hashes_served == set()
        assert peer.header_hashes_ever_served == {keccak256(header)}

    def test_failed_write_records_nothing_as_served(self) -> None:
        """
        A header response whose socket write raises is not service.

        The evidence feeds the consumer's per-block wire-coverage
        assertion, so a header that never left the peer must not
        appear in it. The request itself is still counted: it arrived,
        whatever became of the answer.
        """
        peer = _peer_with_headers({1: b"\x04" * 100})
        with pytest.raises(OSError):
            peer._serve_headers(
                cast(RLPxSession, _FailingSession()), _headers_request(1)
            )
        assert peer.statistics.header_requests == 1
        assert peer.statistics.headers_served == 0
        assert peer.statistics.header_hashes_served == set()
        assert peer.header_hashes_ever_served == set()


class TestFrameSizeGuard:
    """A frame too large to describe is refused, not silently mangled."""

    def test_oversized_frame_is_refused(self) -> None:
        """A frame at the three byte length ceiling raises."""

        class _RefusingSocket:
            """A socket that fails the test if it is ever written to."""

            def sendall(self, data: bytes) -> None:
                """Reject a write the size guard should have stopped."""
                del data
                raise AssertionError("oversized frame reached the socket")

        session = RLPxSession(
            cast(socket.socket, _RefusingSocket()),
            aes_secret=b"\x02" * 32,
            mac_secret=b"\x03" * 32,
            egress_seed=b"\x04" * 32,
            ingress_seed=b"\x05" * 32,
        )
        # One byte for the message code brings the frame to the ceiling.
        with pytest.raises(RLPxError, match="frame of"):
            session.write_message(0x10, b"\x00" * (MAX_FRAME_SIZE - 1))


class _StubAccessListChains:
    """The access lists a peer holds, keyed by block hash."""

    def __init__(self, access_lists: Dict[bytes, bytes | None]) -> None:
        """Hold `access_lists`; a `None` value is a pre-Amsterdam block."""
        self._access_lists = access_lists

    def access_list_rlp_by_hash(self, block_hash: bytes) -> bytes | None:
        """Return the access list held under `block_hash`, if any."""
        return self._access_lists.get(block_hash)


def _access_list_peer(
    access_lists: Dict[bytes, bytes | None], serve: bool
) -> MockPeer:
    """Return an eth/71 peer holding `access_lists`."""
    peer = MockPeer(
        host="127.0.0.1",
        port=30303,
        remote_public_key=b"\x00" * 64,
        private_key=b"\x01" * 32,
        network_id=1,
        serve_access_lists=serve,
    )
    peer.protocol = ETH_PROTOCOLS[71]
    peer._chains = cast(Any, _StubAccessListChains(access_lists))
    return peer


def _request_access_lists(peer: MockPeer, hashes: List[bytes]) -> Any:
    """Send `peer` a GetBlockAccessLists request and return its answer."""
    session = _RecordingSession()
    payload = eth_rlp.encode([Uint(5), hashes])
    peer._handle(cast(RLPxSession, session), GET_BLOCK_ACCESS_LISTS, payload)
    return session.messages


class TestAccessListService:
    """Access lists are withheld by default and served on request."""

    ACCESS_LIST = eth_rlp.encode([[b"\x11" * 20, [], [], [], [], []]])

    def test_withheld_by_default(self) -> None:
        """The default peer leaves the request unanswered and counts it."""
        peer = _access_list_peer({_hash(1): self.ACCESS_LIST}, serve=False)
        assert _request_access_lists(peer, [_hash(1)]) == []
        assert peer.statistics.unanswered_requests == {
            "GetBlockAccessLists": 1
        }
        assert peer.statistics.access_lists_served == 0

    def test_served_entries_are_positional(self) -> None:
        """
        One entry per requested hash, in order: the access list itself,
        not wrapped in a byte string, and the RLP empty string for a
        block without one (unknown, or from before Amsterdam).
        """
        peer = _access_list_peer(
            {_hash(1): self.ACCESS_LIST, _hash(2): None}, serve=True
        )
        messages = _request_access_lists(peer, [_hash(1), _hash(2), _hash(3)])
        assert len(messages) == 1
        code, payload = messages[0]
        assert code == BLOCK_ACCESS_LISTS
        request_id, entries = cast(
            Tuple[bytes, List[Any]], eth_rlp.decode(payload)
        )
        assert int.from_bytes(request_id, "big") == 5
        assert [eth_rlp.encode(entry) for entry in entries] == [
            self.ACCESS_LIST,
            UNAVAILABLE_ACCESS_LIST,
            UNAVAILABLE_ACCESS_LIST,
        ]
        assert peer.statistics.access_list_requests == 1
        assert peer.statistics.access_lists_served == 1
        assert peer.statistics.unanswered_requests == {}

    def test_receipts_stay_unanswered_when_serving(self) -> None:
        """Serving access lists never extends to receipts."""
        peer = _access_list_peer({}, serve=True)
        session = _RecordingSession()
        payload = eth_rlp.encode([Uint(5), Uint(0), [_hash(1)]])
        peer._handle(cast(RLPxSession, session), GET_RECEIPTS, payload)
        assert session.messages == []
        assert peer.statistics.receipt_requests == 1
