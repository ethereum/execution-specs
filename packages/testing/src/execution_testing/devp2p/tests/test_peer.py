"""Tests for what the peer serves and what it records as served."""

from dataclasses import dataclass, field
from itertools import takewhile
from typing import Any, Callable, Dict, List, Tuple, cast

import ethereum_rlp as eth_rlp
import pytest
from ethereum_types.numeric import Uint

from execution_testing.base_types import Hash

from ..chain import Block, Chain
from ..keccak import keccak256
from ..peer import (
    MAX_BODIES_PER_RESPONSE,
    MAX_HEADERS_PER_RESPONSE,
    SOFT_RESPONSE_LIMIT,
    UNAVAILABLE_BAL,
    MockPeer,
)
from ..protocol import (
    ETH_PROTOCOLS,
    BlockHeadersRequest,
    EthVersion,
    ForkSchedule,
    MessageCode,
)
from ..rlpx import RLPxSession

LARGE_BODY_SIZE = 8 * 1024 * 1024
"""A body the size EIP-7934 allows a block to reach."""


def _hash(index: int) -> Hash:
    """Return a distinct block hash for `index`."""
    return Hash(index.to_bytes(32, "big"))


@dataclass
class _StubHead:
    """The head fields the peer reads when a hash is unknown."""

    number: int = 1
    block_hash: bytes = b"\xaa" * 32


@dataclass
class _StubChain:
    """A current chain: its head, and the headers it holds by number."""

    head: _StubHead = field(default_factory=_StubHead)
    headers: Dict[int, bytes] = field(default_factory=dict)

    def header_rlp_by_number(self, number: int) -> bytes | None:
        """Return the header RLP held under `number`, if any."""
        return self.headers.get(number)


class _StubChains:
    """What a peer holds: bodies and BALs by hash, and a current chain."""

    def __init__(
        self,
        bodies: Dict[Hash, bytes] | None = None,
        headers: Dict[int, bytes] | None = None,
        bals: Dict[Hash, bytes | None] | None = None,
    ) -> None:
        """Hold the given items; a `None` BAL is a pre-Amsterdam block."""
        self._bodies = bodies or {}
        self._bals = bals or {}
        self.current = _StubChain(headers=headers or {})

    def install(self, chain: Any) -> None:
        """Accept a new chain without changing what is held."""
        del chain

    def body_rlp_by_hash(self, block_hash: Hash) -> bytes | None:
        """Return the body held under `block_hash`, if any."""
        return self._bodies.get(block_hash)

    def bal_rlp_by_hash(self, block_hash: Hash) -> bytes | None:
        """Return the BAL held under `block_hash`, if any."""
        return self._bals.get(block_hash)


def _peer(**overrides: Any) -> MockPeer:
    """Return a peer that is never dialed for real."""
    arguments: Dict[str, Any] = {
        "host": "127.0.0.1",
        "port": 30303,
        "remote_public_key": b"\x00" * 64,
        "private_key": b"\x01" * 32,
        "network_id": 1,
    }
    return MockPeer(**(arguments | overrides))


def _stub_peer(
    bodies: Dict[Hash, bytes] | None = None,
    headers: Dict[int, bytes] | None = None,
) -> MockPeer:
    """Return a peer holding stub `bodies` and current `headers`."""
    peer = _peer()
    peer._chains = cast(Any, _StubChains(bodies, headers))
    return peer


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


def _serve(bodies: Dict[Hash, bytes], hashes: List[Hash]) -> int:
    """
    Ask a peer holding `bodies` for `hashes`; return how many it sent.

    The response is sized rather than decoded: a pure Python RLP decode
    of megabytes would dominate the suite.
    """
    peer = _stub_peer(bodies)
    session = _RecordingSession()
    peer._serve_bodies(cast(RLPxSession, session), 1, hashes)

    ((code, payload),) = session.messages
    assert code == MessageCode.BLOCK_BODIES
    served = peer.statistics.bodies_served
    # The response ends at the first unknown hash, so the served bodies
    # are the first `served` hashes, and it carries nothing else.
    known = list(takewhile(lambda block_hash: block_hash in bodies, hashes))
    expected = sum(len(bodies[block_hash]) for block_hash in known[:served])
    assert expected <= len(payload) <= expected + 16
    assert peer.statistics.body_hashes_served == set(known[:served])
    return served


BODY_RESPONSES = {
    "two-large-bodies-split": (
        {1: LARGE_BODY_SIZE, 2: LARGE_BODY_SIZE},
        [1, 2],
        1,
    ),
    "one-oversized-body-served": ({1: LARGE_BODY_SIZE}, [1], 1),
    "small-bodies-share-one-response": (
        dict.fromkeys(range(1, 33), 1),
        list(range(1, 33)),
        32,
    ),
    "item-cap": (
        dict.fromkeys(range(MAX_BODIES_PER_RESPONSE + 10), 1),
        list(range(MAX_BODIES_PER_RESPONSE + 10)),
        MAX_BODIES_PER_RESPONSE,
    ),
    "unknown-hash-ends-the-response": ({1: 2, 3: 2}, [1, 2, 3], 1),
}
"""Held body sizes by index, the indexes requested, and bodies served."""


class TestBodyResponseSize:
    """One response never carries more bytes than a client will read."""

    @pytest.mark.parametrize(
        "sizes,requested,served",
        BODY_RESPONSES.values(),
        ids=BODY_RESPONSES.keys(),
    )
    def test_a_response_stops_at_a_limit_or_an_unknown_hash(
        self, sizes: Dict[int, int], requested: List[int], served: int
    ) -> None:
        """
        A response stops at the byte or item limit, though one oversized
        body is still served rather than withheld, and at an unheld hash,
        as geth and reth stop: a body after it would sit at the unheld
        hash's position.
        """
        assert LARGE_BODY_SIZE > SOFT_RESPONSE_LIMIT
        bodies = {
            _hash(index): b"\x01" * size for index, size in sizes.items()
        }
        assert _serve(bodies, [_hash(index) for index in requested]) == served


def _headers_request(number: int, amount: int = 1) -> BlockHeadersRequest:
    """Return a forward request for `amount` headers from `number`."""
    return BlockHeadersRequest(
        request_id=7,
        origin_hash=None,
        origin_number=number,
        amount=amount,
        skip=0,
        reverse=False,
    )


@dataclass
class _StubHeader:
    """The header fields a `Chain` reads, hashed like a real header."""

    number: int
    rlp: bytes
    block_hash: bytes
    withdrawals_root: bytes | None = None


def _stub_header(number: int, tag: bytes) -> _StubHeader:
    """Return a header at `number`, distinguished by `tag`."""
    rlp = eth_rlp.encode([Uint(number), tag])
    return _StubHeader(number=number, rlp=rlp, block_hash=keccak256(rlp))


GENESIS = _stub_header(0, b"genesis")


def _chain(tags: List[bytes]) -> Chain:
    """
    Return a chain whose block `n` carries `tags[n - 1]`.

    Two chains built from equal leading tags share those blocks, hash
    for hash, as two tests of one group share a block prefix.
    """
    blocks = [
        Block(
            header=cast(Any, _stub_header(number, tag)),
            transactions=[],
            withdrawals=None,
        )
        for number, tag in enumerate(tags, start=1)
    ]
    return Chain(cast(Any, GENESIS), blocks)


def _hash_at(chain: Chain, number: int) -> bytes:
    """Return the hash of `chain`'s block at `number`, genesis included."""
    if number == 0:
        return bytes(chain.genesis.block_hash)
    return chain.blocks[number - 1].block_hash


def _serving(*chains: Chain) -> MockPeer:
    """Return a peer that served `chains` in order, the last current."""
    peer = _peer()
    for chain in chains:
        peer.set_chain(chain)
    return peer


def _walk(
    peer: MockPeer,
    origin: int | bytes,
    amount: int,
    skip: int = 0,
    reverse: bool = False,
) -> List[bytes]:
    """
    Ask `peer` for headers from `origin` and return the served hashes.

    An `int` origin names a block by number, a `bytes` origin by hash.
    """
    session = _RecordingSession()
    request = BlockHeadersRequest(
        request_id=9,
        origin_hash=Hash(origin) if isinstance(origin, bytes) else None,
        origin_number=origin if isinstance(origin, int) else None,
        amount=amount,
        skip=skip,
        reverse=reverse,
    )
    peer._serve_headers(cast(RLPxSession, session), request)
    assert len(session.messages) == 1
    code, payload = session.messages[0]
    assert code == MessageCode.BLOCK_HEADERS
    request_id, headers = cast(
        Tuple[bytes, List[Any]], eth_rlp.decode(payload)
    )
    assert int.from_bytes(request_id, "big") == 9
    return [keccak256(eth_rlp.encode(header)) for header in headers]


class TestHeaderRequests:
    """Header requests walk the served chain as the eth protocol says."""

    @pytest.mark.parametrize(
        "length,origin,by_hash,amount,skip,reverse,expected",
        [
            pytest.param(10, 1, False, 4, 2, False, [1, 4, 7, 10], id="skip"),
            pytest.param(
                10, 10, False, 4, 2, True, [10, 7, 4, 1], id="reverse-skip"
            ),
            pytest.param(
                10,
                3,
                False,
                10,
                0,
                True,
                [3, 2, 1, 0],
                id="reverse-to-genesis",
            ),
            pytest.param(10, 9, False, 5, 0, False, [9, 10], id="past-head"),
            pytest.param(10, 11, False, 1, 0, False, [], id="beyond-head"),
            pytest.param(10, 1, False, 0, 0, False, [], id="amount-zero"),
            pytest.param(
                10, 10, True, 3, 0, True, [10, 9, 8], id="hash-head-reverse"
            ),
            pytest.param(
                10, 2, True, 3, 1, False, [2, 4, 6], id="hash-forward-skip"
            ),
            pytest.param(
                10, 0, True, 3, 0, False, [0, 1, 2], id="hash-genesis"
            ),
            # A hash on no served chain gets an empty, counted answer.
            pytest.param(10, None, True, 2, 0, False, [], id="unknown-hash"),
            pytest.param(
                MAX_HEADERS_PER_RESPONSE + 10,
                0,
                False,
                MAX_HEADERS_PER_RESPONSE + 11,
                0,
                False,
                list(range(MAX_HEADERS_PER_RESPONSE)),
                id="count-capped",
            ),
        ],
    )
    def test_header_requests(
        self,
        length: int,
        origin: int | None,
        by_hash: bool,
        amount: int,
        skip: int,
        reverse: bool,
        expected: List[int],
    ) -> None:
        """Exactly the requested blocks are served, in order, and recorded."""
        chain = _chain(
            [number.to_bytes(2, "big") for number in range(1, length + 1)]
        )
        peer = _serving(chain)
        start: int | bytes | None = origin
        if by_hash:
            start = b"\xee" * 32 if origin is None else _hash_at(chain, origin)
        assert start is not None
        served = _walk(peer, start, amount, skip, reverse)
        wanted = [_hash_at(chain, number) for number in expected]
        assert served == wanted
        assert peer.statistics.header_requests == 1
        assert peer.statistics.headers_served == len(wanted)
        assert peer.statistics.header_hashes_served == set(wanted)

    @pytest.mark.parametrize(
        "walked,origin,amount,reverse,expected",
        [
            # A client still syncing the previous test's chain names a
            # block only that chain holds, and is answered from it.
            pytest.param("older", 3, 4, True, [3, 2, 1, 0], id="older-head"),
            pytest.param(
                "current", 3, 4, True, [3, 2, 1, 0], id="current-head"
            ),
            # A forward walk from a block both chains share leads to the
            # current head, not the older one's.
            pytest.param(
                "current", 1, 3, False, [1, 2, 3], id="forward-from-shared"
            ),
        ],
    )
    def test_a_walk_follows_the_chain_of_its_origin(
        self,
        walked: str,
        origin: int,
        amount: int,
        reverse: bool,
        expected: List[int],
    ) -> None:
        """A walk across two served chains follows the right ancestry."""
        chains = {
            "older": _chain([b"1", b"2a", b"3a"]),
            "current": _chain([b"1", b"2b", b"3b"]),
        }
        assert _hash_at(chains["older"], 1) == _hash_at(chains["current"], 1)
        peer = _serving(chains["older"], chains["current"])
        chain = chains[walked]
        served = _walk(peer, _hash_at(chain, origin), amount, reverse=reverse)
        assert served == [_hash_at(chain, number) for number in expected]


class _HandoverSession(_RecordingSession):
    """A session during whose write the next test takes over the peer."""

    def __init__(self, handover: Callable[[], None]) -> None:
        """Run `handover` on the first write."""
        super().__init__()
        self.handover = handover

    def write_message(self, code: int, payload: bytes) -> None:
        """Start the next test, then record the message."""
        self.handover()
        super().write_message(code, payload)


HEADER = b"\x02" * 100
"""The header a stub peer holds at number 1."""


@dataclass(frozen=True)
class _Service:
    """
    One kind of served item, as the evidence tests hold and ask for it.

    The `str` fields name the statistics and peer attributes this kind
    is counted in, and `marker` the word its transcript line carries.
    """

    held: Callable[[], MockPeer]
    serve: Callable[[MockPeer, Any], None]
    evidence: bytes
    requests: str
    served: str
    hashes: str
    ever_served: str
    marker: str


SERVICES = {
    "header": _Service(
        held=lambda: _stub_peer(headers={1: HEADER}),
        serve=lambda peer, session: peer._serve_headers(
            session, _headers_request(1)
        ),
        evidence=keccak256(HEADER),
        requests="header_requests",
        served="headers_served",
        hashes="header_hashes_served",
        ever_served="header_hashes_ever_served",
        marker="headers",
    ),
    "body": _Service(
        held=lambda: _stub_peer(bodies={_hash(1): b"\x01"}),
        serve=lambda peer, session: peer._serve_bodies(session, 1, [_hash(1)]),
        evidence=_hash(1),
        requests="body_requests",
        served="bodies_served",
        hashes="body_hashes_served",
        ever_served="body_hashes_ever_served",
        marker="served",
    ),
}


@pytest.mark.parametrize("kind", SERVICES)
class TestServiceEvidence:
    """Served headers and bodies are each recorded by hash, apart."""

    def test_a_served_item_is_recorded_by_hash(self, kind: str) -> None:
        """
        The evidence is the hash of the exact item served, and it is no
        evidence of the other kind, per test or lifetime.
        """
        service = SERVICES[kind]
        other = SERVICES["body" if kind == "header" else "header"]
        peer = service.held()
        service.serve(peer, _RecordingSession())
        for attribute in (service.requests, service.served):
            assert getattr(peer.statistics, attribute) == 1
        assert getattr(peer.statistics, service.hashes) == {service.evidence}
        assert getattr(peer, service.ever_served) == {service.evidence}
        assert getattr(peer.statistics, other.served) == 0
        assert getattr(peer.statistics, other.hashes) == set()
        assert getattr(peer, other.ever_served) == set()

    def test_lifetime_service_survives_a_chain_switch(self, kind: str) -> None:
        """The lifetime record survives the statistics of a chain switch."""
        service = SERVICES[kind]
        peer = service.held()
        service.serve(peer, _RecordingSession())
        peer.set_chain(cast(Any, _StubChain()))
        assert getattr(peer.statistics, service.hashes) == set()
        assert getattr(peer, service.ever_served) == {service.evidence}

    def test_a_failed_write_records_nothing_as_served(self, kind: str) -> None:
        """A failed write records nothing as served, only the request."""
        service = SERVICES[kind]
        peer = service.held()
        with pytest.raises(OSError):
            service.serve(peer, _FailingSession())
        statistics = peer.statistics
        assert getattr(statistics, service.requests) == 1
        assert getattr(statistics, service.served) == 0
        assert getattr(statistics, service.hashes) == set()
        assert getattr(peer, service.ever_served) == set()
        assert not any(
            service.marker in line for line in statistics.transcript
        )

    def test_a_straggling_response_stays_with_its_test(
        self, kind: str
    ) -> None:
        """
        A response written while the next test takes over the peer is
        recorded for the test that asked for it.
        """
        service = SERVICES[kind]
        peer = service.held()
        asking = peer.statistics
        service.serve(
            peer,
            _HandoverSession(lambda: peer.set_chain(cast(Any, _StubChain()))),
        )
        assert peer.statistics is not asking
        assert getattr(asking, service.served) == 1
        assert getattr(asking, service.hashes) == {service.evidence}
        assert any(service.marker in line for line in asking.transcript)
        assert getattr(peer.statistics, service.served) == 0
        assert getattr(peer.statistics, service.hashes) == set()
        assert not any(
            service.marker in line for line in peer.statistics.transcript
        )
        assert getattr(peer, service.ever_served) == {service.evidence}


class TestChainSwitchDuringALookup:
    """A chain switch on the test thread cannot hide a held block."""

    def test_a_switch_between_reads_still_serves_a_held_body(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        The next test installs its chain in the middle of a body lookup
        on the serving thread; the body the old chain holds is served.
        """
        old = _chain([b"\x01", b"\x02"])
        new = _chain([b"\x03"])
        peer = _serving(old)
        held = Hash(_hash_at(old, 2))
        real_number_of = old.number_of

        def number_of_then_switch(block_hash: Hash) -> int | None:
            """Answer, then let the next test take over the peer."""
            number = real_number_of(block_hash)
            if peer._chains.current is old:
                peer.set_chain(new)
            return number

        monkeypatch.setattr(old, "number_of", number_of_then_switch)
        asking = peer.statistics
        peer._serve_bodies(cast(RLPxSession, _RecordingSession()), 1, [held])

        assert peer._chains.current is new
        assert asking.body_hashes_served == {held}


@dataclass
class _TimedHeader:
    """The header fields the Status message reads."""

    number: int
    block_hash: Hash
    timestamp: int


def _status_chain(head_timestamp: int) -> Chain:
    """Return genesis `0x11..` (t=0) and head #5 `0x22..` at a time."""
    genesis = _TimedHeader(0, Hash(b"\x11" * 32), 0)
    head = _TimedHeader(5, Hash(b"\x22" * 32), head_timestamp)
    block = Block(header=cast(Any, head), transactions=[], withdrawals=None)
    return Chain(cast(Any, genesis), [block])


def _eth69_status(peer: MockPeer, head_timestamp: int) -> str:
    """Return the eth/69 Status `peer` sends for `_status_chain`, as hex."""
    status = peer._status(_status_chain(head_timestamp))
    return ETH_PROTOCOLS[EthVersion.ETH_69].encode_status(status).hex()


GENESIS_11 = "a0" + "11" * 32
HEAD_22 = "a0" + "22" * 32


class TestStatusForkId:
    """The Status fork identifier follows the client's fork schedule."""

    def test_a_single_fork_network_is_unchanged(self) -> None:
        """
        A network running one fork from genesis sends the bytes it
        always has: the genesis checksum and no next fork.
        """
        expected = f"f84d4501{GENESIS_11}c684bc4920d8808005{HEAD_22}"
        assert _eth69_status(_peer(), head_timestamp=30000) == expected

    @pytest.mark.parametrize(
        "head_timestamp, expected",
        [
            pytest.param(
                14999,
                f"f84f4501{GENESIS_11}c884bc4920d8823a988005{HEAD_22}",
                id="before-the-fork",
            ),
            pytest.param(
                15000,
                f"f84d4501{GENESIS_11}c684597af0e2808005{HEAD_22}",
                id="past-the-fork",
            ),
        ],
    )
    def test_a_transition_network_names_its_fork(
        self, head_timestamp: int, expected: str
    ) -> None:
        """
        A fork at t=15000 is announced as the next fork before the
        served head reaches it, and folded into the hash after.
        """
        peer = _peer(fork_schedule=ForkSchedule(timestamps=(15000,)))
        assert _eth69_status(peer, head_timestamp) == expected


def _bal_peer(bals: Dict[Hash, bytes | None], serve: bool) -> MockPeer:
    """Return an eth/71 peer holding `bals`."""
    peer = _peer(serve_bals=serve)
    peer.protocol = ETH_PROTOCOLS[EthVersion.ETH_71]
    peer._chains = cast(Any, _StubChains(bals=bals))
    return peer


def _request_bals(
    peer: MockPeer, hashes: List[bytes]
) -> Tuple[int, List[bytes]]:
    """Ask `peer` for the BALs of `hashes`; return the id and entries."""
    session = _RecordingSession()
    payload = eth_rlp.encode([Uint(5), hashes])
    peer._handle(
        cast(RLPxSession, session), MessageCode.GET_BLOCK_ACCESS_LISTS, payload
    )
    ((code, response),) = session.messages
    assert code == MessageCode.BLOCK_ACCESS_LISTS
    request_id, entries = cast(
        Tuple[bytes, List[Any]], eth_rlp.decode(response)
    )
    return (
        int.from_bytes(request_id, "big"),
        [eth_rlp.encode(entry) for entry in entries],
    )


class TestBalService:
    """BALs are withheld by default and served on request."""

    BAL = eth_rlp.encode([[b"\x11" * 20, [], [], [], [], []]])

    def test_withheld_by_default(self) -> None:
        """Every entry is unavailable; held BALs count as withheld."""
        peer = _bal_peer({_hash(1): self.BAL, _hash(2): None}, serve=False)
        assert _request_bals(peer, [_hash(1), _hash(2)]) == (
            5,
            [UNAVAILABLE_BAL, UNAVAILABLE_BAL],
        )
        assert peer.statistics.bal_requests == 1
        assert peer.statistics.bals_served == 0
        assert peer.statistics.bals_withheld == 1
        assert peer.statistics.receipt_requests == 0

    def test_served_entries_are_positional(self) -> None:
        """One entry per hash, in order: the unwrapped BAL, else empty."""
        peer = _bal_peer({_hash(1): self.BAL, _hash(2): None}, serve=True)
        assert _request_bals(peer, [_hash(1), _hash(2), _hash(3)]) == (
            5,
            [self.BAL, UNAVAILABLE_BAL, UNAVAILABLE_BAL],
        )
        assert peer.statistics.bal_requests == 1
        assert peer.statistics.bals_served == 1
        assert peer.statistics.bals_withheld == 0
        assert peer.statistics.receipt_requests == 0

    @pytest.mark.parametrize("version", sorted(ETH_PROTOCOLS))
    def test_receipts_are_answered_as_none_held_when_serving(
        self, version: EthVersion
    ) -> None:
        """No version serves receipts, even with BALs served."""
        peer = _bal_peer({}, serve=True)
        peer.protocol = ETH_PROTOCOLS[version]
        session = _RecordingSession()
        offset = [] if version == 69 else [Uint(0)]
        payload = eth_rlp.encode([Uint(5), *offset, [_hash(1)]])
        peer._handle(
            cast(RLPxSession, session), MessageCode.GET_RECEIPTS, payload
        )
        assert session.messages == [
            (
                MessageCode.RECEIPTS,
                ETH_PROTOCOLS[version].encode_no_receipts(5),
            )
        ]
        assert peer.statistics.receipt_requests == 1
        assert "receipts for 1 hashes" in peer.statistics.transcript[-1]
