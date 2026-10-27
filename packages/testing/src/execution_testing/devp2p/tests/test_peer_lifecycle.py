"""Tests for how the peer's connection starts, ends and is redialed."""

import select
import socket
import threading
import time
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any, Callable, List, Tuple, cast

import ethereum_rlp as eth_rlp
import pytest
from ethereum_types.numeric import Uint

from execution_testing.base_types import Bytes, Hash

from .. import peer as peer_module
from .. import rlpx
from ..chain import Block, Chain
from ..peer import HANDSHAKE_TIMEOUT, MockPeer, PeerStatistics
from ..protocol import ETH_PROTOCOLS, MessageCode
from ..rlpx import RLPxError, RLPxSession

OUTLASTS_CLOSE = 20.0
"""
A read timeout longer than `MockPeer.close` waits to join the loop (5 s).

A loop or reader still alive after such a join is one the close did not
wake, so the lifecycle tests need no wall clock.
"""

WAKE_TIMEOUT = 5.0
"""How long a test waits for a thread it expects to wake at once."""


class _BlockingSession:
    """
    A session whose reads wait for data that never comes.

    Like a real socket, a read wakes when the session is closed, and
    otherwise times out after `read_timeout`. A session made with
    `ignore_close` models a loop stuck in a long write: closing does not
    wake it, only `release` does.
    """

    def __init__(
        self, read_timeout: float = 1.0, ignore_close: bool = False
    ) -> None:
        """Start open."""
        self.read_timeout = read_timeout
        self.ignore_close = ignore_close
        self.closed = threading.Event()
        self.released = threading.Event()

    def read_message(self) -> Tuple[int, bytes]:
        """Wait for a close (or release), else time out."""
        wake = self.released if self.ignore_close else self.closed
        if wake.wait(self.read_timeout):
            raise OSError("session closed")
        raise TimeoutError("no message within the read timeout")

    def release(self) -> None:
        """Wake a read that ignores closing."""
        self.released.set()

    def close(self) -> None:
        """Close the session, waking a read unless it ignores closing."""
        self.closed.set()


class _ScriptedSession(_BlockingSession):
    """A session that delivers one message, then blocks."""

    def __init__(self, message: Tuple[int, bytes]) -> None:
        """Hold `message` for the first read."""
        super().__init__()
        self.messages: List[Tuple[int, bytes]] = [message]

    def read_message(self) -> Tuple[int, bytes]:
        """Deliver the scripted message, then behave as blocking."""
        if self.messages:
            return self.messages.pop()
        return super().read_message()


def _peer() -> MockPeer:
    """Return a peer that is never dialed for real."""
    peer = MockPeer(
        host="127.0.0.1",
        port=30303,
        remote_public_key=b"\x00" * 64,
        private_key=b"\x01" * 32,
        network_id=1,
    )
    peer.protocol = ETH_PROTOCOLS[max(ETH_PROTOCOLS)]
    return peer


def _start_on(peer: MockPeer, session: _BlockingSession) -> None:
    """Start `peer`'s loop on `session`."""
    peer._session = cast(RLPxSession, session)
    peer.start()


def _dialing(peer: MockPeer, session: _BlockingSession) -> Callable[..., None]:
    """Return a `connect` stand-in that installs `session`."""

    def connect(chain: Any, timeout: float = 30.0) -> None:
        del chain, timeout
        peer._session = cast(RLPxSession, session)

    return connect


def _wait_until(condition: Callable[[], bool], timeout: float = 10.0) -> bool:
    """
    Return whether `condition` became true within `timeout`.

    The timeout only bounds a failing test, so it is generous: a loaded
    runner may not schedule the peer's thread for a while.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.005)
    return condition()


class TestClose:
    """Closing ends the loop without waiting out its read timeout."""

    def test_close_wakes_the_loop_at_once(self) -> None:
        """A loop blocked on a read ends as soon as the peer closes."""
        peer = _peer()
        _start_on(peer, _BlockingSession(read_timeout=OUTLASTS_CLOSE))
        loop = peer._thread
        peer.close()
        # The read outlasts close's join, so a finished loop is one the
        # close woke rather than one that waited out its read.
        assert loop is not None and not loop.is_alive()
        assert not peer.alive

    def test_session_close_wakes_a_blocked_reader(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Closing a real session wakes a thread waiting to read from it."""
        local, remote = socket.socketpair()
        session = RLPxSession(
            local,
            aes_secret=b"\x02" * 32,
            mac_secret=b"\x03" * 32,
            egress_seed=b"\x04" * 32,
            ingress_seed=b"\x05" * 32,
        )
        session.set_timeout(OUTLASTS_CLOSE)
        errors: List[BaseException] = []
        waiting = threading.Event()

        def select_and_signal(*args: Any) -> Any:
            """Signal that the reader is about to wait, then wait."""
            waiting.set()
            return select.select(*args)

        monkeypatch.setattr(
            rlpx, "select", SimpleNamespace(select=select_and_signal)
        )

        def read() -> None:
            try:
                session.read_message()
            except BaseException as error:  # noqa: BLE001
                errors.append(error)

        reader = threading.Thread(target=read)
        reader.start()
        assert waiting.wait(WAKE_TIMEOUT)
        session.close()
        # The read outlasts this join, so a finished reader is one the
        # close woke rather than one that waited out its read.
        reader.join(WAKE_TIMEOUT)
        remote.close()
        assert not reader.is_alive()
        assert errors and not isinstance(errors[0], TimeoutError)


class _DisconnectingWhenReleased(_BlockingSession):
    """
    A stuck session whose loop, once released, reads a client Disconnect.

    It models a loop that outlived its close and then drains a
    Disconnect frame the client had already sent.
    """

    def __init__(self) -> None:
        """Start stuck, as `_start_stuck` needs."""
        super().__init__(read_timeout=10.0, ignore_close=True)

    def read_message(self) -> Tuple[int, bytes]:
        """Deliver a Disconnect with reason 4 once released."""
        if self.released.wait(self.read_timeout):
            return MessageCode.DISCONNECT, eth_rlp.encode([Uint(4)])
        raise TimeoutError("no message within the read timeout")


class _GatedSession(_BlockingSession):
    """A session that delivers a Ping once its gate opens, then blocks."""

    def __init__(self) -> None:
        """Start with the gate closed and nothing written."""
        super().__init__(read_timeout=0.01)
        self.gate = threading.Event()
        self.pinged = False
        self.written: List[int] = []

    def read_message(self) -> Tuple[int, bytes]:
        """Deliver one Ping after the gate opens."""
        if self.gate.is_set() and not self.pinged:
            self.pinged = True
            return MessageCode.PING, eth_rlp.encode([])
        return super().read_message()

    def write_message(self, code: int, payload: bytes) -> None:
        """Record the code of one message."""
        del payload
        self.written.append(code)


def _start_stuck(
    peer: MockPeer,
    monkeypatch: pytest.MonkeyPatch,
    stuck: _BlockingSession | None = None,
) -> Tuple[_BlockingSession, threading.Thread]:
    """
    Start `peer` on a loop stuck in a write; return it and its thread.

    Its join gives up at once, as the redial's join gives up on such a
    loop; only this thread's join is patched, so every other thread in
    the process still joins for real.
    """
    if stuck is None:
        stuck = _BlockingSession(read_timeout=10.0, ignore_close=True)
    _start_on(peer, stuck)
    assert peer._thread is not None
    monkeypatch.setattr(peer._thread, "join", lambda *_args, **_kwargs: None)
    return stuck, peer._thread


class TestRedial:
    """Redialing replaces the session cleanly."""

    def test_a_failed_redial_reads_as_dead(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        A redial that raises leaves no loop claiming to be alive, even
        when the old loop is stuck and outlives the redial.
        """
        peer = _peer()
        stuck, straggler = _start_stuck(peer, monkeypatch)

        def refuse(chain: Any, timeout: float = 30.0) -> None:
            del chain, timeout
            raise ConnectionRefusedError("client refused")

        monkeypatch.setattr(peer, "connect", refuse)
        with pytest.raises(ConnectionRefusedError):
            peer.reconnect(cast(Any, None))
        assert straggler.is_alive()
        assert not peer.alive
        monkeypatch.undo()
        stuck.release()
        assert _wait_until(lambda: not straggler.is_alive())

    def test_a_straggling_loop_cannot_kill_the_next_session(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        A loop that outlives its session's close (stuck in a write)
        ends on its own later, and the redialed session stays alive.
        """
        peer = _peer()
        stuck, straggler = _start_stuck(peer, monkeypatch)
        fresh = _BlockingSession()
        monkeypatch.setattr(peer, "connect", _dialing(peer, fresh))
        peer.reconnect(cast(Any, None))
        stuck.release()
        assert _wait_until(lambda: not straggler.is_alive())
        assert peer.alive
        peer.close()

    def test_a_straggler_disconnect_stays_with_its_own_session(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        A Disconnect read by a loop that outlived its session is not
        reported for the redialed session, which keeps serving.
        """
        peer = _peer()
        stuck, straggler = _start_stuck(
            peer, monkeypatch, _DisconnectingWhenReleased()
        )
        fresh = _GatedSession()
        monkeypatch.setattr(peer, "connect", _dialing(peer, fresh))
        peer.reconnect(cast(Any, None))
        stuck.release()
        assert _wait_until(lambda: not straggler.is_alive())
        assert peer.disconnect_reason is None
        fresh.gate.set()
        assert _wait_until(lambda: fresh.written == [MessageCode.PONG])
        assert peer.alive
        peer.close()


class _SilentClientSession:
    """A session to a client that completes RLPx but never says Hello."""

    def __init__(self) -> None:
        """Start with the transport's own read timeout."""
        self.read_timeout = rlpx.FRAME_READ_TIMEOUT
        self.waited: List[float] = []
        self.closed = False

    def set_timeout(self, timeout: float) -> None:
        """Change how long a read waits."""
        self.read_timeout = timeout

    def write_message(self, code: int, payload: bytes) -> None:
        """Accept our Hello."""
        del code, payload

    def read_message(self) -> Tuple[int, bytes]:
        """Wait out the read timeout, recording it, as a silent client."""
        self.waited.append(self.read_timeout)
        raise TimeoutError("no message within the read timeout")

    def close(self) -> None:
        """Record the close."""
        self.closed = True


class TestHandshakeTimeout:
    """A silent client fails a dial within the handshake timeout."""

    def test_a_missing_hello_fails_within_the_handshake_timeout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The wait for Hello is bounded by the dial's timeout."""
        session = _SilentClientSession()
        monkeypatch.setattr(
            peer_module, "connect", lambda *_args, **_kwargs: session
        )
        peer = _peer()
        with pytest.raises(TimeoutError):
            peer.reconnect(Chain(cast(Any, _StubGenesis()), []))
        assert session.waited == [HANDSHAKE_TIMEOUT]
        assert HANDSHAKE_TIMEOUT < rlpx.FRAME_READ_TIMEOUT
        assert session.closed
        assert not peer.alive


class _MalformedHelloSession(_SilentClientSession):
    """A session to a client that answers our Hello with `payload`."""

    def __init__(self, code: int, payload: bytes) -> None:
        """Hold the one message the client sends."""
        super().__init__()
        self.message = (code, payload)

    def read_message(self) -> Tuple[int, bytes]:
        """Deliver the client's message."""
        return self.message


class TestMalformedHello:
    """
    A Hello (or Disconnect) that does not decode fails the dial with
    `RLPxError`, which the consumer's redial handling catches.
    """

    @pytest.mark.parametrize(
        "code, payload",
        [
            pytest.param(MessageCode.HELLO, b"\xff\x00", id="undecodable"),
            pytest.param(
                MessageCode.HELLO,
                eth_rlp.encode([Uint(5), b"client", []]) + b"\x00",
                id="trailing-bytes",
            ),
            pytest.param(
                MessageCode.HELLO,
                eth_rlp.encode([Uint(5), b"client", b"\x03\x02"]),
                id="capabilities-not-a-list",
            ),
            pytest.param(
                MessageCode.DISCONNECT,
                b"\xff\x00",
                id="undecodable-disconnect",
            ),
        ],
    )
    def test_the_dial_fails_with_an_rlpx_error(
        self, monkeypatch: pytest.MonkeyPatch, code: int, payload: bytes
    ) -> None:
        """The session is closed and the peer is left dead."""
        session = _MalformedHelloSession(code, payload)
        monkeypatch.setattr(
            peer_module, "connect", lambda *_args, **_kwargs: session
        )
        peer = _peer()
        with pytest.raises(RLPxError, match="malformed devp2p"):
            peer.reconnect(Chain(cast(Any, _StubGenesis()), []))
        assert session.closed
        assert not peer.alive


class _AnsweringSession(_ScriptedSession):
    """A scripted session that also keeps what the peer writes."""

    def __init__(self, message: Tuple[int, bytes]) -> None:
        """Hold `message` for the first read, with nothing written."""
        super().__init__(message)
        self.written: List[Tuple[int, bytes]] = []

    def write_message(self, code: int, payload: bytes) -> None:
        """Record one message."""
        self.written.append((code, payload))


@dataclass
class _StubGenesis:
    """The genesis fields a `Chain` reads."""

    number: int = 0
    rlp: bytes = b"\xc1\x80"
    block_hash: bytes = b"\x0a" * 32
    withdrawals_root: bytes | None = None


def _serving_peer(session: _AnsweringSession) -> MockPeer:
    """Return a peer serving a genesis-only chain, its loop on `session`."""
    peer = _peer()
    peer.set_chain(Chain(cast(Any, _StubGenesis()), []))
    _start_on(peer, session)
    return peer


class TestMalformedRequest:
    """
    A request the peer cannot read ends the loop cleanly and closes its
    session; a well-formed one is answered and the loop carries on.
    """

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param(b"\xff\x00", id="undecodable"),
            pytest.param(
                eth_rlp.encode([Uint(1), [Uint(1)]]), id="wrong-shape"
            ),
        ],
    )
    def test_the_loop_ends_without_a_crash(
        self, monkeypatch: pytest.MonkeyPatch, payload: bytes
    ) -> None:
        """No uncaught exception escapes, and no socket is left open."""
        crashes: List[threading.ExceptHookArgs] = []
        monkeypatch.setattr(threading, "excepthook", crashes.append)
        session = _AnsweringSession((MessageCode.GET_BLOCK_HEADERS, payload))
        peer = _serving_peer(session)
        assert _wait_until(lambda: not peer.alive)
        assert session.closed.is_set()
        assert session.written == []
        assert crashes == []
        peer.close()

    def test_a_well_formed_request_is_answered(self) -> None:
        """The same harness answers a valid request and stays alive."""
        request = eth_rlp.encode(
            [Uint(1), [Uint(0), Uint(1), Uint(0), Uint(0)]]
        )
        session = _AnsweringSession((MessageCode.GET_BLOCK_HEADERS, request))
        peer = _serving_peer(session)
        # Service is recorded after the write, so wait for the record.
        assert _wait_until(lambda: peer.statistics.headers_served == 1)
        assert [code for code, _ in session.written] == [
            MessageCode.BLOCK_HEADERS
        ]
        assert peer.alive
        peer.close()


class TestDisconnect:
    """A Disconnect from the client ends the loop, with or without a reason."""

    @pytest.mark.parametrize(
        "payload, reason",
        [
            pytest.param(eth_rlp.encode([Uint(4)]), 4, id="with-reason"),
            pytest.param(eth_rlp.encode([]), None, id="without-reason"),
        ],
    )
    def test_the_loop_ends_and_keeps_the_reason(
        self, payload: bytes, reason: int | None
    ) -> None:
        """The reason is recorded, `None` when the message has none."""
        session = _ScriptedSession((MessageCode.DISCONNECT, payload))
        peer = _peer()
        _start_on(peer, session)
        assert _wait_until(lambda: not peer.alive)
        assert session.closed.is_set()
        assert peer.disconnect_reason == reason
        peer.close()


class TestStatisticsAcrossRedials:
    """Which test a redial's traffic is attributed to."""

    def test_a_redial_mid_test_keeps_the_transcript(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A redial does not erase what the test has seen so far."""
        peer = _peer()
        _start_on(peer, _BlockingSession())
        peer.statistics.record("headers before the drop")
        monkeypatch.setattr(
            peer, "connect", _dialing(peer, _BlockingSession())
        )
        peer.reconnect(cast(Any, None))
        assert "headers before the drop" in peer.statistics.transcript
        peer.close()

    def test_a_reset_starts_the_next_test_from_empty_statistics(
        self,
    ) -> None:
        """
        A reset leaves no field of the previous test's statistics, only
        the negotiated eth version, and keeps the lifetime evidence.
        """
        peer = _peer()
        previous = peer.statistics
        previous.record("the previous test's headers")
        previous.header_requests = 1
        previous.headers_served = 7
        previous.header_hashes_served.add(Hash(b"\x01" * 32))
        previous.body_requests = 2
        previous.bodies_served = 3
        previous.body_hashes_served.add(Hash(b"\x02" * 32))
        previous.bal_requests = 4
        previous.bals_served = 5
        previous.bals_withheld = 6
        previous.receipt_requests = 7
        peer.header_hashes_ever_served.add(Hash(b"\x01" * 32))
        peer.body_hashes_ever_served.add(Hash(b"\x02" * 32))

        peer.reset_statistics()

        assert peer.statistics == PeerStatistics(
            transcript=[f"eth/{max(ETH_PROTOCOLS)} negotiated"]
        )
        assert peer.header_hashes_ever_served == {b"\x01" * 32}
        assert peer.body_hashes_ever_served == {b"\x02" * 32}


@dataclass
class _LoopbackHeader:
    """The header fields the Status message and the peer's indexes read."""

    number: int
    block_hash: Hash
    timestamp: int


def _loopback_chain() -> Chain:
    """Return genesis `0x11..` and two blocks, the first with one tx."""
    genesis = _LoopbackHeader(0, Hash(b"\x11" * 32), 0)
    blocks = [
        Block(
            header=cast(Any, _LoopbackHeader(1, Hash(b"\x01" * 32), 12)),
            transactions=[Bytes(b"\x01\x02")],
            withdrawals=None,
        ),
        Block(
            header=cast(Any, _LoopbackHeader(2, Hash(b"\x02" * 32), 24)),
            transactions=[],
            withdrawals=None,
        ),
    ]
    return Chain(cast(Any, genesis), blocks)


class TestLoopbackDial:
    """
    A dial over a real socket, read as a client reads it.

    Every other protocol test speaks to the library with the library, so
    a message code moved on both ends would still pass. The codes and
    layouts here are literal values from devp2p's `rlpx.md` and
    `caps/eth.md`.
    """

    @pytest.mark.parametrize("p2p_version", [4, 5])
    def test_a_dial_speaks_the_spec_codes(
        self, monkeypatch: pytest.MonkeyPatch, p2p_version: int
    ) -> None:
        """
        Hello is 0x00, then Status 0x10, BlockRangeUpdate 0x21 and
        BlockBodies 0x16 for GetBlockBodies 0x15, Snappy compressed from
        p2p version 5 on.
        """
        local, remote = socket.socketpair()
        for end in (local, remote):
            end.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)
        secrets = (b"\x02" * 32, b"\x03" * 32)
        peer_end = RLPxSession(
            local, *secrets, egress_seed=b"\x04", ingress_seed=b"\x05"
        )
        client = RLPxSession(
            remote, *secrets, egress_seed=b"\x05", ingress_seed=b"\x04"
        )
        client.set_timeout(WAKE_TIMEOUT)
        monkeypatch.setattr(
            peer_module, "connect", lambda *_args, **_kwargs: peer_end
        )
        # The client's Hello waits in the socket until the peer reads it.
        client.write_message(
            0x00,
            eth_rlp.encode(
                [
                    Uint(p2p_version),
                    b"client",
                    [[b"eth", Uint(69)]],
                    Uint(0),
                    b"\x09" * 64,
                ]
            ),
        )
        chain = _loopback_chain()
        peer = _peer()
        try:
            peer.connect(chain)
            code, _ = client.read_message()
            assert code == 0x00
            if p2p_version >= 5:
                client.enable_snappy()
            code, status = client.read_message()
            assert code == 0x10
            # eth/69, the one version both sides share, then the network,
            # genesis, fork id (pinned elsewhere) and the block range.
            fields = cast(list[Any], eth_rlp.decode(status))
            assert len(fields) == 7
            assert fields[:3] == [b"\x45", b"\x01", b"\x11" * 32]
            assert fields[4:] == [b"", b"\x02", b"\x02" * 32]
            peer.start()
            peer.set_chain(chain)
            code, update = client.read_message()
            assert code == 0x21
            assert eth_rlp.decode(update) == [b"", b"\x02", b"\x02" * 32]
            client.write_message(
                0x15, eth_rlp.encode([Uint(7), [b"\x01" * 32]])
            )
            code, bodies = client.read_message()
            assert code == 0x16
            assert eth_rlp.decode(bodies) == [b"\x07", [[[b"\x01\x02"], []]]]
        finally:
            peer.close()
            client.close()
