"""
The RLPx transport: encrypted, authenticated framing over TCP.

This implements the initiator half of the handshake described in the
devp2p RLPx specification, and the frame codec that carries every
subsequent message. There is no support for acting as the recipient of
a dial.
"""

import contextlib
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
from ethereum_rlp.rlp import decode_item_length
from ethereum_types.numeric import Uint
from spec256k1 import PrivateKey

from .ecies import OVERHEAD, PUBLIC_KEY_LENGTH, decrypt, encrypt
from .keccak import Keccak256, keccak256
from .secp256k1 import agree, public_key_bytes
from .snappy import SnappyError, compress, decompress, decompressed_length

logger = logging.getLogger(__name__)

AUTH_VERSION = 4
"""RLPx handshake version advertised in auth and ack messages."""

NONCE_LENGTH = 32
"""Bytes of the random nonce each side sends in its handshake message."""

MAX_FRAME_SIZE = 1 << 24
"""
Largest frame this peer writes, and the most a compressed message may
claim to decompress to. A frame header holds its length in three bytes.
"""

FRAME_READ_TIMEOUT = 30.0
"""Socket timeout for the reads inside one frame (see `read_message`)."""

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
        self._snappy = False
        self._write_lock = threading.Lock()
        self._read_poll_timeout: float = FRAME_READ_TIMEOUT

    def enable_snappy(self) -> None:
        """Compress every later payload (see `P2P_VERSION`)."""
        self._snappy = True

    def _read_exactly(self, length: int) -> bytes:
        """
        Read exactly `length` bytes of an in-flight frame.

        A stall here ends the session (see `read_message`).
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

        The peer's serving thread and the test thread both write, and the
        egress cipher and MAC are stateful, so writes take a lock. A frame
        over `MAX_FRAME_SIZE` is refused here, near the caller that built
        it, rather than overflowing the length field.
        """
        if self._snappy:
            payload = compress(payload)
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

        Raise `TimeoutError` if no frame begins within the `set_timeout`
        interval; the session stays usable. Once a frame begins, its reads
        run under `FRAME_READ_TIMEOUT` and a stall is fatal: the ingress
        cipher and MAC have already advanced over its start, so a partial
        frame cannot be resumed.
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
        # literal byte below 0x80, or 0x80 for a code of zero. Every
        # devp2p message code fits that; a longer integer would be
        # misread as a code followed by payload.
        if frame[0] > 0x80:
            raise RLPxError(f"message code prefix {frame[0]:#x} unsupported")
        code = 0 if frame[0] == 0x80 else frame[0]
        payload = frame[1:]
        if self._snappy:
            try:
                if decompressed_length(payload) > MAX_FRAME_SIZE:
                    raise RLPxError(
                        "compressed message claims a decompressed size "
                        "over the frame limit"
                    )
                payload = decompress(payload)
            except SnappyError as error:
                raise RLPxError(
                    f"invalid snappy payload in message {code}: {error}"
                ) from None
        return code, payload

    def set_timeout(self, timeout: float) -> None:
        """Set how long `read_message` waits for a frame to begin."""
        self._read_poll_timeout = timeout

    def close(self) -> None:
        """
        Shut down and close the underlying socket.

        Shutting down first wakes a thread blocked on this session at
        once; a bare close leaves it waiting out its timeout.
        """
        with contextlib.suppress(OSError):
            self._connection.shutdown(socket.SHUT_RDWR)
        with contextlib.suppress(OSError):
            self._connection.close()


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

    encrypted_size = len(body) + OVERHEAD
    prefix = encrypted_size.to_bytes(2, "big")
    return prefix + encrypt(remote_public_key, body, prefix)


def _parse_ack(private_key: bytes, message: bytes) -> Tuple[bytes, bytes]:
    """Return the remote ephemeral public key and nonce from an ack."""
    body = decrypt(private_key, message[2:], message[:2])
    # The EIP-8 body is followed by random padding.
    fields = eth_rlp.decode(body[: decode_item_length(body)])
    if not isinstance(fields, list) or len(fields) < 2:
        raise RLPxError("malformed ack message")
    ephemeral_public_key, remote_nonce = fields[0], fields[1]
    if not isinstance(ephemeral_public_key, bytes) or not isinstance(
        remote_nonce, bytes
    ):
        raise RLPxError("malformed ack message fields")
    if (
        len(ephemeral_public_key) != PUBLIC_KEY_LENGTH
        or len(remote_nonce) != NONCE_LENGTH
    ):
        raise RLPxError(
            f"malformed ack: a {len(ephemeral_public_key)} byte key and a "
            f"{len(remote_nonce)} byte nonce, expected {PUBLIC_KEY_LENGTH} "
            f"and {NONCE_LENGTH}"
        )
    return ephemeral_public_key, remote_nonce


def _derive_secrets(
    ephemeral_key: bytes,
    nonce: bytes,
    remote_nonce: bytes,
    auth: bytes,
    ack: bytes,
) -> Tuple[bytes, bytes, bytes, bytes]:
    """
    Return the initiator's session secrets and MAC seeds.

    `ephemeral_key` is the agreement of both ephemeral keys, and `auth`
    and `ack` are the handshake messages as sent, size prefix included.
    The result is the AES secret, the MAC secret, the egress MAC seed
    and the ingress MAC seed.
    """
    shared_secret = keccak256(ephemeral_key + keccak256(remote_nonce + nonce))
    aes_secret = keccak256(ephemeral_key + shared_secret)
    mac_secret = keccak256(ephemeral_key + aes_secret)
    return (
        aes_secret,
        mac_secret,
        _xor(mac_secret, remote_nonce) + auth,
        _xor(mac_secret, nonce) + ack,
    )


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
    nonce = os.urandom(NONCE_LENGTH)

    connection = socket.create_connection((host, port), timeout=timeout)
    try:
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        auth = _build_auth(
            private_key, ephemeral_private_key, nonce, remote_public_key
        )
        connection.sendall(auth)

        size_prefix = _recv_exactly(connection, 2)
        ack = size_prefix + _recv_exactly(
            connection, int.from_bytes(size_prefix, "big")
        )
        remote_ephemeral_public_key, remote_nonce = _parse_ack(
            private_key, ack
        )
        ephemeral_key = agree(
            ephemeral_private_key, remote_ephemeral_public_key
        )
        aes_secret, mac_secret, egress_seed, ingress_seed = _derive_secrets(
            ephemeral_key, nonce, remote_nonce, auth, ack
        )
        connection.settimeout(FRAME_READ_TIMEOUT)
    except (OSError, RLPxError):
        connection.close()
        raise
    except Exception as error:
        # An ack that fails decryption, decodes to the wrong shape or
        # carries a key off the curve is a malformed handshake, which
        # callers handle as such rather than as an unrelated crash.
        connection.close()
        raise RLPxError(f"malformed handshake: {error!r}") from error

    logger.debug("RLPx handshake complete with %s:%d", host, port)
    return RLPxSession(
        connection,
        aes_secret,
        mac_secret,
        egress_seed=egress_seed,
        ingress_seed=ingress_seed,
    )
