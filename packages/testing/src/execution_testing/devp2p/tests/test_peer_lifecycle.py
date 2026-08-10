"""Tests for how the peer's connection starts, ends and is redialed."""

import socket
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, List, Tuple, cast

import ethereum_rlp as eth_rlp
import pytest
from ethereum_types.numeric import Uint

from ..chain import Chain
from ..peer import MockPeer
from ..protocol import BLOCK_HEADERS, ETH_PROTOCOLS, GET_BLOCK_HEADERS
from ..rlpx import RLPxSession


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


def _wait_until(condition: Callable[[], bool], timeout: float = 2.0) -> bool:
    """Return whether `condition` became true within `timeout`."""
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
        _start_on(peer, _BlockingSession(read_timeout=5.0))
        started = time.monotonic()
        peer.close()
        assert time.monotonic() - started < 1.0
        assert not peer.alive

    def test_session_close_wakes_a_blocked_reader(self) -> None:
        """Closing a real session wakes a thread waiting to read from it."""
        local, remote = socket.socketpair()
        session = RLPxSession(
            local,
            aes_secret=b"\x02" * 32,
            mac_secret=b"\x03" * 32,
            egress_seed=b"\x04" * 32,
            ingress_seed=b"\x05" * 32,
        )
        session.set_timeout(5.0)
        errors: List[BaseException] = []

        def read() -> None:
            try:
                session.read_message()
            except BaseException as error:  # noqa: BLE001
                errors.append(error)

        reader = threading.Thread(target=read)
        reader.start()
        time.sleep(0.05)
        started = time.monotonic()
        session.close()
        reader.join(5.0)
        remote.close()
        assert time.monotonic() - started < 1.0
        assert errors and not isinstance(errors[0], TimeoutError)


def _start_stuck(
    peer: MockPeer, monkeypatch: pytest.MonkeyPatch
) -> Tuple[_BlockingSession, threading.Thread]:
    """
    Start `peer` on a loop stuck in a write; return it and its thread.

    Joins give up at once, as the redial's join gives up on such a loop.
    """
    stuck = _BlockingSession(read_timeout=10.0, ignore_close=True)
    _start_on(peer, stuck)
    assert peer._thread is not None
    monkeypatch.setattr(
        threading.Thread, "join", lambda _self, *_args, **_kwargs: None
    )
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
        # Restore the real join so the fresh loop is joined, not left
        # logging after the test.
        monkeypatch.undo()
        peer.close()


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
        session = _AnsweringSession((GET_BLOCK_HEADERS, payload))
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
        session = _AnsweringSession((GET_BLOCK_HEADERS, request))
        peer = _serving_peer(session)
        # Service is recorded after the write, so wait for the record.
        assert _wait_until(lambda: peer.statistics.headers_served == 1)
        assert [code for code, _ in session.written] == [BLOCK_HEADERS]
        assert peer.alive
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

    def test_a_reset_starts_the_next_tests_transcript(self) -> None:
        """
        A test that begins with a redial starts from empty statistics,
        naming only the negotiated eth version.
        """
        peer = _peer()
        peer.statistics.record("the previous test's headers")
        peer.statistics.headers_served = 7
        peer.reset_statistics()
        assert peer.statistics.headers_served == 0
        assert peer.statistics.transcript == [
            f"eth/{max(ETH_PROTOCOLS)} negotiated"
        ]
