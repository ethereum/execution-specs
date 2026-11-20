"""Tests for RLPx framing between two sessions sharing secrets."""

import socket
from typing import Iterator, Tuple, cast

import ethereum_rlp as eth_rlp
import pytest
from ethereum_types.numeric import Uint

from ..keccak import keccak256
from ..rlpx import MAX_FRAME_SIZE, RLPxError, RLPxSession, _recv_exactly

AES_SECRET = b"\x02" * 32
MAC_SECRET = b"\x03" * 32
INITIATOR_SEED = b"\x04" * 32
RECIPIENT_SEED = b"\x05" * 32


def _session(connection: socket.socket, initiator: bool) -> RLPxSession:
    """Return one end of a session under the shared test secrets."""
    egress, ingress = INITIATOR_SEED, RECIPIENT_SEED
    if not initiator:
        egress, ingress = ingress, egress
    return RLPxSession(
        connection,
        AES_SECRET,
        MAC_SECRET,
        egress_seed=egress,
        ingress_seed=ingress,
    )


@pytest.fixture
def sessions() -> Iterator[Tuple[RLPxSession, RLPxSession]]:
    """Yield two connected sessions whose seeds mirror each other."""
    left, right = socket.socketpair()
    # Tests write a whole message before reading it, and macOS socket
    # pairs buffer only 8 KiB, so a larger frame would block forever.
    for end in (left, right):
        end.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1 << 20)
    initiator = _session(left, initiator=True)
    recipient = _session(right, initiator=False)
    for session in (initiator, recipient):
        session.set_timeout(1.0)
    yield initiator, recipient
    initiator.close()
    recipient.close()


@pytest.fixture
def raw_link() -> Iterator[Tuple[socket.socket, RLPxSession]]:
    """Yield a raw socket and the recipient session reading from it."""
    left, right = socket.socketpair()
    recipient = _session(right, initiator=False)
    recipient.set_timeout(1.0)
    yield left, recipient
    left.close()
    recipient.close()


def _initiator_frame(code: int, payload: bytes) -> bytes:
    """Return the bytes the initiator writes for its first message."""
    left, right = socket.socketpair()
    writer = _session(left, initiator=True)
    writer.write_message(code, payload)
    raw = _recv_exactly(right, 64)
    writer.close()
    right.close()
    return raw


def _flip(data: bytes, index: int) -> bytes:
    """Return `data` with one bit of the byte at `index` flipped."""
    flipped = bytearray(data)
    flipped[index] ^= 1
    return bytes(flipped)


class TestFraming:
    """Messages cross intact, in order, in both directions."""

    def test_messages_round_trip(
        self, sessions: Tuple[RLPxSession, RLPxSession]
    ) -> None:
        """Each message arrives with its code and payload."""
        initiator, recipient = sessions
        messages = [(0x00, b"\xc0"), (0x13, b"x" * 1000), (0x7F, b"")]
        for code, payload in messages:
            initiator.write_message(code, payload)
        assert [recipient.read_message() for _ in messages] == messages
        recipient.write_message(0x10, b"reply")
        assert initiator.read_message() == (0x10, b"reply")

    def test_snappy_payloads_round_trip(
        self, sessions: Tuple[RLPxSession, RLPxSession]
    ) -> None:
        """Compressed sessions carry the same payloads."""
        initiator, recipient = sessions
        initiator.enable_snappy()
        recipient.enable_snappy()
        initiator.write_message(0x12, b"body" * 10_000)
        assert recipient.read_message() == (0x12, b"body" * 10_000)

    def test_a_snappy_bomb_claim_is_refused_before_decompressing(
        self, sessions: Tuple[RLPxSession, RLPxSession]
    ) -> None:
        """A payload claiming more than a frame may hold is refused."""
        initiator, recipient = sessions
        recipient.enable_snappy()
        # A bare preamble claiming 32 MiB, sent uncompressed so it
        # arrives as is.
        initiator.write_message(0x10, bytes([0x80, 0x80, 0x80, 0x10]))
        with pytest.raises(RLPxError, match="over the frame limit"):
            recipient.read_message()

    def test_a_code_beyond_one_byte_is_refused(
        self, sessions: Tuple[RLPxSession, RLPxSession]
    ) -> None:
        """A code needing a longer RLP integer is refused, not misread."""
        initiator, recipient = sessions
        initiator.write_message(0x81, b"")
        with pytest.raises(RLPxError, match="message code prefix"):
            recipient.read_message()

    def test_a_tampered_header_mac_is_refused(
        self, raw_link: Tuple[socket.socket, RLPxSession]
    ) -> None:
        """A frame whose header MAC fails raises on the header check."""
        link, recipient = raw_link
        # Bytes 16-31 of a frame are the header MAC.
        link.sendall(_flip(_initiator_frame(0x10, b"x"), 16))
        with pytest.raises(RLPxError, match="header MAC mismatch"):
            recipient.read_message()

    def test_a_tampered_body_mac_is_refused(
        self, raw_link: Tuple[socket.socket, RLPxSession]
    ) -> None:
        """A frame whose body MAC fails raises on the body check."""
        link, recipient = raw_link
        # The last 16 bytes of a frame are the body MAC.
        link.sendall(_flip(_initiator_frame(0x10, b"x"), -1))
        with pytest.raises(RLPxError, match="body MAC mismatch"):
            recipient.read_message()


# Source: go-ethereum p2p/rlpx/rlpx_test.go, TestFrameReadWrite
# https://github.com/ethereum/go-ethereum/blob/master/p2p/rlpx/rlpx_test.go
GETH_HEADER_CIPHERTEXT = bytes.fromhex("00828ddae471818bb0bfa6b551d1cb42")
"""The golden frame's header ciphertext."""

GETH_FRAME_CIPHERTEXT = bytes.fromhex("ba628a4ba590cb43f7848f41c4382885")
"""The golden frame's body ciphertext."""


class TestFrameLayout:
    """The frame layout matches another implementation byte for byte."""

    def test_the_frame_ciphertext_matches_geth(self) -> None:
        """
        Code 8 with `rlp([1, 2, 3, 4])` under AES secret `keccak256("")`.

        Pins the header (length, header-data, padding) and the body
        ciphertext. The golden MACs come from a fake hash in geth's test
        and are not compared.
        """
        left, right = socket.socketpair()
        secret = keccak256(b"")
        session = RLPxSession(
            left, secret, secret, egress_seed=b"", ingress_seed=b""
        )
        payload = eth_rlp.encode([Uint(1), Uint(2), Uint(3), Uint(4)])
        session.write_message(8, payload)
        raw = _recv_exactly(right, 64)
        session.close()
        right.close()
        assert raw[:16] == GETH_HEADER_CIPHERTEXT
        assert raw[32:48] == GETH_FRAME_CIPHERTEXT


class _RefusingSocket:
    """A socket that fails the test if it is ever written to."""

    def sendall(self, data: bytes) -> None:
        """Reject a write the size guard should have stopped."""
        del data
        raise AssertionError("oversized frame reached the socket")


class TestFrameSizeGuard:
    """A frame too large to describe is refused, not silently mangled."""

    def test_oversized_frame_is_refused(self) -> None:
        """A frame at the three byte length ceiling raises before a write."""
        session = _session(
            cast(socket.socket, _RefusingSocket()), initiator=True
        )
        # One byte for the message code brings the frame to the ceiling.
        with pytest.raises(RLPxError, match="frame of"):
            session.write_message(0x10, b"\x00" * (MAX_FRAME_SIZE - 1))
