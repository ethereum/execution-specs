"""
The RLPx transport: encrypted, authenticated framing over TCP.

This implements the initiator half of the handshake described in the
devp2p RLPx specification, and the frame codec that carries every
subsequent message. Only what a deterministic test peer needs is
present; there is no support for acting as the recipient of a dial.
"""

import logging
import os
import select
import socket
import threading
from typing import Tuple

import ethereum_rlp as eth_rlp
from cryptography.hazmat.primitives.ciphers import (
    Cipher,
    CipherContext,
    algorithms,
    modes,
)
from ethereum_types.numeric import Uint
from spec256k1 import PrivateKey

from .ecies import decrypt, encrypt
from .keccak import Keccak256, keccak256
from .secp256k1 import agree, public_key_bytes

logger = logging.getLogger(__name__)

AUTH_VERSION = 4
"""RLPx handshake version advertised in auth and ack messages."""

MAX_FRAME_SIZE = 1 << 24
"""Largest frame this peer will write, and the ceiling for the
decompressed payload size a compressed message may claim on read. A
frame header expresses its length in three bytes, so an outgoing frame
at or above this limit cannot be described at all."""

FRAME_READ_TIMEOUT = 30.0
"""
Socket timeout for the reads inside one frame.

A frame read, once begun, cannot be paused and resumed: the ingress
cipher and MAC have already advanced over the bytes consumed so far. A
remote that stalls mid-frame for this long has abandoned the
connection, and the session with it.
"""

_MAC_LENGTH = 16


class RLPxError(Exception):
    """Raised when the transport cannot maintain a valid session."""


def _xor(left: bytes, right: bytes) -> bytes:
    """Return the byte-wise exclusive-or of two equal length strings."""
    return bytes(a ^ b for a, b in zip(left, right, strict=True))


def _pad_to_block(data: bytes) -> bytes:
    """Zero pad `data` to a whole number of 16 byte blocks."""
    remainder = len(data) % 16
    return data if remainder == 0 else data + bytes(16 - remainder)


def _recv_exactly(connection: socket.socket, length: int) -> bytes:
    """Read exactly `length` bytes or raise `RLPxError` on a close."""
    buffer = b""
    while len(buffer) < length:
        chunk = connection.recv(length - len(buffer))
        if not chunk:
            raise RLPxError("connection closed by peer")
        buffer += chunk
    return buffer


class _Mac:
    """
    One direction of the RLPx frame MAC.

    The MAC is a running Keccak-256 state, seeded from the shared MAC
    secret and both handshake messages, that is advanced by every header
    and frame body. Each advance mixes in an AES-ECB encryption of the
    state's own current digest, which binds the MAC to the connection's
    key material rather than to the ciphertext alone.
    """

    def __init__(self, secret: bytes, seed: bytes) -> None:
        """Seed the MAC state with `seed` under the MAC `secret`."""
        self._secret = secret
        self._state = Keccak256(seed)

    def _encrypt_seed(self, seed: bytes) -> bytes:
        """Return `seed` encrypted with AES-ECB under the MAC secret."""
        cipher = Cipher(algorithms.AES(self._secret), modes.ECB()).encryptor()
        return cipher.update(seed) + cipher.finalize()

    def update_header(self, header_ciphertext: bytes) -> bytes:
        """Advance the MAC over a frame header and return its tag."""
        digest = self._state.digest()[:_MAC_LENGTH]
        self._state.update(_xor(self._encrypt_seed(digest), header_ciphertext))
        return self._state.digest()[:_MAC_LENGTH]

    def update_body(self, frame_ciphertext: bytes) -> bytes:
        """Advance the MAC over a frame body and return its tag."""
        self._state.update(frame_ciphertext)
        digest = self._state.digest()[:_MAC_LENGTH]
        self._state.update(_xor(self._encrypt_seed(digest), digest))
        return self._state.digest()[:_MAC_LENGTH]


class RLPxSession:
    """
    An established RLPx connection to a remote node.

    Construct with `connect`, which performs the encryption handshake and
    returns a session whose `read_message` and `write_message` speak in
    devp2p message codes and RLP encoded payloads.
    """

    _connection: socket.socket
    _egress_aes: CipherContext
    _ingress_aes: CipherContext

    def __init__(
        self,
        connection: socket.socket,
        aes_secret: bytes,
        mac_secret: bytes,
        egress_seed: bytes,
        ingress_seed: bytes,
    ) -> None:
        """Initialize the frame codec from the derived session secrets."""
        self._connection = connection
        zero_counter = bytes(16)
        self._egress_aes = Cipher(
            algorithms.AES(aes_secret), modes.CTR(zero_counter)
        ).encryptor()
        self._ingress_aes = Cipher(
            algorithms.AES(aes_secret), modes.CTR(zero_counter)
        ).decryptor()
        self._egress_mac = _Mac(mac_secret, egress_seed)
        self._ingress_mac = _Mac(mac_secret, ingress_seed)
        self._write_lock = threading.Lock()
        self._read_poll_timeout: float = FRAME_READ_TIMEOUT

    def _read_exactly(self, length: int) -> bytes:
        """
        Read exactly `length` bytes of an in-flight frame.

        A timeout here is fatal to the session rather than retryable:
        the ingress cipher and MAC have already advanced over the bytes
        consumed so far, so the read cannot be resumed later.
        """
        try:
            return _recv_exactly(self._connection, length)
        except TimeoutError:
            raise RLPxError(
                "connection stalled mid-frame; the stream cannot be resumed"
            ) from None

    def write_message(self, code: int, payload: bytes) -> None:
        """
        Write one devp2p message as a single RLPx frame.

        Serialized with a lock: the peer's serving thread and the test
        thread (chain announcements) both write to the session, and the
        egress cipher and MAC are stateful - an interleaved write would
        corrupt the running MAC and the frame stream.

        A frame too large to describe in the header's three byte length
        field is refused here. Without this the length would overflow
        inside a serving thread, far from the caller that assembled an
        oversized response.
        """
        frame = eth_rlp.encode(Uint(code)) + payload
        if len(frame) >= MAX_FRAME_SIZE:
            raise RLPxError(
                f"frame of {len(frame)} bytes exceeds the "
                f"{MAX_FRAME_SIZE - 1} bytes a frame header can express"
            )
        header = _pad_to_block(
            len(frame).to_bytes(3, "big") + eth_rlp.encode([Uint(0), Uint(0)])
        )

        with self._write_lock:
            header_ciphertext = self._egress_aes.update(header)
            header_mac = self._egress_mac.update_header(header_ciphertext)
            frame_ciphertext = self._egress_aes.update(_pad_to_block(frame))
            frame_mac = self._egress_mac.update_body(frame_ciphertext)

            self._connection.sendall(
                header_ciphertext + header_mac + frame_ciphertext + frame_mac
            )

    def read_message(self) -> Tuple[int, bytes]:
        """
        Read one devp2p message and return its code and payload.

        Waits up to the `set_timeout` interval for a frame to begin,
        raising `TimeoutError` while nothing has been consumed - the
        only point where a read may time out and leave the session
        usable, because resuming a partially read frame is impossible
        once the ingress cipher and MAC have advanced over its start.
        """
        ready, _, _ = select.select(
            [self._connection], [], [], self._read_poll_timeout
        )
        if not ready:
            raise TimeoutError("no message within the read timeout")
        header_ciphertext = self._read_exactly(16)
        header_mac = self._read_exactly(_MAC_LENGTH)
        if self._ingress_mac.update_header(header_ciphertext) != header_mac:
            raise RLPxError("frame header MAC mismatch")
        header = self._ingress_aes.update(header_ciphertext)

        frame_size = int.from_bytes(header[:3], "big")
        if frame_size == 0:
            raise RLPxError("zero-length frame")

        padded_size = (frame_size + 15) // 16 * 16
        frame_ciphertext = self._read_exactly(padded_size)
        frame_mac = self._read_exactly(_MAC_LENGTH)
        if self._ingress_mac.update_body(frame_ciphertext) != frame_mac:
            raise RLPxError("frame body MAC mismatch")
        frame = self._ingress_aes.update(frame_ciphertext)[:frame_size]

        # The message code is a single RLP encoded integer: either a
        # literal byte below 0x80, or 0x80 for a code of zero.
        code = 0 if frame[0] == 0x80 else frame[0]
        return code, frame[1:]

    def set_timeout(self, timeout: float) -> None:
        """
        Set how long `read_message` waits for a message to begin.

        The wait applies ahead of a frame, where timing out is
        harmless; the reads inside a frame run under the fixed
        `FRAME_READ_TIMEOUT`, because a partial frame cannot be
        resumed and abandoning one ends the session.
        """
        self._read_poll_timeout = timeout

    def close(self) -> None:
        """Close the underlying socket."""
        try:
            self._connection.close()
        except OSError:
            pass


def _build_auth(
    private_key: bytes,
    ephemeral_private_key: bytes,
    nonce: bytes,
    remote_public_key: bytes,
) -> bytes:
    """Return the encrypted auth message for the handshake initiator."""
    static_shared_secret = agree(private_key, remote_public_key)
    signature = PrivateKey(ephemeral_private_key).sign_recoverable(
        _xor(static_shared_secret, nonce)
    )
    body = eth_rlp.encode(
        [
            signature,
            public_key_bytes(private_key),
            nonce,
            Uint(AUTH_VERSION),
        ]
    )
    # Random padding places the message in the EIP-8 encoding, which is
    # the only auth format current clients accept.
    body += os.urandom(100 + int.from_bytes(os.urandom(1), "big") % 100)

    encrypted_size = len(body) + 1 + 64 + 16 + 32
    prefix = encrypted_size.to_bytes(2, "big")
    return prefix + encrypt(remote_public_key, body, prefix)


def _first_rlp_item(data: bytes) -> bytes:
    """
    Return the leading RLP item of `data`, ignoring what follows it.

    Handshake messages carry random padding after their RLP body, so the
    body has to be delimited by its own length rather than by the end of
    the message.
    """
    prefix = data[0]
    if prefix < 0x80:
        return data[:1]
    if prefix <= 0xB7:
        return data[: 1 + prefix - 0x80]
    if prefix <= 0xBF:
        header = 1 + (prefix - 0xB7)
        length = int.from_bytes(data[1:header], "big")
        return data[: header + length]
    if prefix <= 0xF7:
        return data[: 1 + prefix - 0xC0]
    header = 1 + (prefix - 0xF7)
    length = int.from_bytes(data[1:header], "big")
    return data[: header + length]


def _parse_ack(private_key: bytes, message: bytes) -> Tuple[bytes, bytes]:
    """Return the remote ephemeral public key and nonce from an ack."""
    body = decrypt(private_key, message[2:], message[:2])
    fields = eth_rlp.decode(_first_rlp_item(body))
    if not isinstance(fields, list) or len(fields) < 2:
        raise RLPxError("malformed ack message")
    ephemeral_public_key, remote_nonce = fields[0], fields[1]
    if not isinstance(ephemeral_public_key, bytes) or not isinstance(
        remote_nonce, bytes
    ):
        raise RLPxError("malformed ack message fields")
    return ephemeral_public_key, remote_nonce


def connect(
    host: str,
    port: int,
    remote_public_key: bytes,
    private_key: bytes,
    timeout: float = 30.0,
) -> RLPxSession:
    """
    Dial `host`:`port` and complete the RLPx encryption handshake.

    `remote_public_key` is the 64 byte node identity taken from the
    remote's enode URL.
    """
    ephemeral_private_key = os.urandom(32)
    nonce = os.urandom(32)

    connection = socket.create_connection((host, port), timeout=timeout)
    connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    auth = _build_auth(
        private_key, ephemeral_private_key, nonce, remote_public_key
    )
    connection.sendall(auth)

    size_prefix = _recv_exactly(connection, 2)
    ack = size_prefix + _recv_exactly(
        connection, int.from_bytes(size_prefix, "big")
    )
    remote_ephemeral_public_key, remote_nonce = _parse_ack(private_key, ack)

    ephemeral_key = agree(ephemeral_private_key, remote_ephemeral_public_key)
    shared_secret = keccak256(ephemeral_key + keccak256(remote_nonce + nonce))
    aes_secret = keccak256(ephemeral_key + shared_secret)
    mac_secret = keccak256(ephemeral_key + aes_secret)

    logger.debug("RLPx handshake complete with %s:%d", host, port)
    connection.settimeout(FRAME_READ_TIMEOUT)
    return RLPxSession(
        connection,
        aes_secret,
        mac_secret,
        egress_seed=_xor(mac_secret, remote_nonce) + auth,
        ingress_seed=_xor(mac_secret, nonce) + ack,
    )
