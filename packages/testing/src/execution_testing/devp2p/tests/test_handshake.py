"""
Tests for the RLPx handshake against the EIP-8 test vectors.

Every expected value comes from EIP-8 (see `handshake_vectors`), so a
bug shared by both halves of this codec still fails here.
"""

import socket
import threading
import types
from typing import Callable, Iterator, List

import ethereum_rlp as eth_rlp
import pytest
from ethereum_rlp.rlp import decode_item_length
from ethereum_types.numeric import Uint
from spec256k1 import PublicKey

from .. import rlpx
from ..ecies import OVERHEAD, decrypt, encrypt
from ..keccak import Keccak256
from ..rlpx import (
    RLPxError,
    RLPxSession,
    _build_auth,
    _derive_secrets,
    _parse_ack,
    _recv_exactly,
    _xor,
)
from ..secp256k1 import agree, public_key_bytes
from .handshake_vectors import (
    ACK_VERSION_4,
    ACK_VERSION_57,
    AES_SECRET,
    AUTH_VERSION_4,
    AUTH_VERSION_56,
    EPHEMERAL_KEY_A,
    EPHEMERAL_KEY_B,
    INGRESS_MAC_FOO,
    MAC_SECRET,
    NONCE_A,
    NONCE_B,
    STATIC_KEY_A,
    STATIC_KEY_B,
)


def _decode_auth(auth: bytes) -> List[bytes]:
    """Return the auth body fields as node B decrypts them."""
    body = decrypt(STATIC_KEY_B, auth[2:], auth[:2])
    fields = eth_rlp.decode(body[: decode_item_length(body)])
    assert isinstance(fields, list)
    return [bytes(field) for field in fields[:4]]


def _ack(fields: List[bytes]) -> bytes:
    """Return an EIP-8 ack from node B to node A carrying `fields`."""
    body = eth_rlp.encode([*fields, Uint(4)]) + bytes(100)
    prefix = (len(body) + OVERHEAD).to_bytes(2, "big")
    return prefix + encrypt(public_key_bytes(STATIC_KEY_A), body, prefix)


SHORT_ACK_FIELDS = {
    "short-key": [public_key_bytes(EPHEMERAL_KEY_B)[:63], NONCE_B],
    "short-nonce": [public_key_bytes(EPHEMERAL_KEY_B), NONCE_B[:31]],
}


def _signer(signature: bytes) -> bytes:
    """Return the public key that signed the auth message."""
    message = _xor(
        agree(STATIC_KEY_B, public_key_bytes(STATIC_KEY_A)), NONCE_A
    )
    signer = PublicKey.from_signature_and_message(signature, message)
    return signer.format(compressed=False)[1:]


class TestAuth:
    """Node B reads what node A sends."""

    @pytest.mark.parametrize(
        "auth, version",
        [
            (AUTH_VERSION_4, 4),
            (AUTH_VERSION_56, 56),
            (
                _build_auth(
                    STATIC_KEY_A,
                    EPHEMERAL_KEY_A,
                    NONCE_A,
                    public_key_bytes(STATIC_KEY_B),
                ),
                4,
            ),
        ],
        ids=["version_4", "version_56_with_extra_elements", "ours"],
    )
    def test_an_auth_decodes(self, auth: bytes, version: int) -> None:
        """An EIP-8 auth, or ours, yields A's key, nonce, version, signer."""
        assert int.from_bytes(auth[:2], "big") == len(auth) - 2
        signature, public_key, nonce, auth_version = _decode_auth(auth)
        assert public_key == public_key_bytes(STATIC_KEY_A)
        assert nonce == NONCE_A
        assert int.from_bytes(auth_version, "big") == version
        assert _signer(signature) == public_key_bytes(EPHEMERAL_KEY_A)


class TestAck:
    """Node A reads what node B sends."""

    @pytest.mark.parametrize(
        "ack",
        [ACK_VERSION_4, ACK_VERSION_57],
        ids=["version_4", "version_57_with_extra_elements"],
    )
    def test_the_vector_ack_parses(self, ack: bytes) -> None:
        """The EIP-8 ack yields B's ephemeral key and nonce."""
        assert _parse_ack(STATIC_KEY_A, ack) == (
            public_key_bytes(EPHEMERAL_KEY_B),
            NONCE_B,
        )

    @pytest.mark.parametrize(
        "fields", SHORT_ACK_FIELDS.values(), ids=SHORT_ACK_FIELDS.keys()
    )
    def test_a_field_of_the_wrong_length_is_refused(
        self, fields: List[bytes]
    ) -> None:
        """A key or nonce of the wrong length is a malformed ack."""
        with pytest.raises(RLPxError, match="expected 64 and 32"):
            _parse_ack(STATIC_KEY_A, _ack(fields))


class TestSecrets:
    """Both ends derive the same session secrets."""

    def test_the_vector_secrets_are_derived(self) -> None:
        """The aes-secret, mac-secret and ingress-mac("foo") of EIP-8."""
        aes_secret, mac_secret, egress_seed, _ = _derive_secrets(
            agree(EPHEMERAL_KEY_A, public_key_bytes(EPHEMERAL_KEY_B)),
            NONCE_A,
            NONCE_B,
            AUTH_VERSION_4,
            ACK_VERSION_4,
        )
        assert aes_secret == AES_SECRET
        assert mac_secret == MAC_SECRET
        # A's egress MAC is seeded exactly as B's ingress MAC.
        assert Keccak256(egress_seed + b"foo").digest() == INGRESS_MAC_FOO


@pytest.fixture
def listener() -> Iterator[socket.socket]:
    """Yield a loopback listening socket, closed afterwards."""
    server = socket.create_server(("127.0.0.1", 0))
    server.settimeout(5.0)
    yield server
    server.close()


def _read_auth(connection: socket.socket) -> bytes:
    """Read one size-prefixed auth message, prefix included."""
    size = _recv_exactly(connection, 2)
    return size + _recv_exactly(connection, int.from_bytes(size, "big"))


def _dial_node_b(listener: socket.socket) -> RLPxSession:
    """Dial `listener` as node A of EIP-8."""
    return rlpx.connect(
        "127.0.0.1",
        listener.getsockname()[1],
        public_key_bytes(STATIC_KEY_B),
        STATIC_KEY_A,
        timeout=5.0,
    )


def _fix_initiator_randomness(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make `connect` draw the vector's ephemeral key and nonce."""
    real_urandom = rlpx.os.urandom
    fixed = [EPHEMERAL_KEY_A, NONCE_A]

    def urandom(length: int) -> bytes:
        """Return the fixed values first, then real randomness."""
        return fixed.pop(0) if fixed else real_urandom(length)

    monkeypatch.setattr(rlpx, "os", types.SimpleNamespace(urandom=urandom))


class _NodeB:
    """
    Node B of EIP-8, run on its own thread.

    An exception on that thread would otherwise only show as a confusing
    timeout on the dialing side, so `join` raises it in the test.
    """

    def __init__(self, behavior: Callable[[], None]) -> None:
        """Start running `behavior`."""
        self.errors: List[BaseException] = []
        self.thread = threading.Thread(
            target=self._run, args=(behavior,), daemon=True
        )
        self.thread.start()

    def _run(self, behavior: Callable[[], None]) -> None:
        """Run `behavior`, keeping what it raises."""
        try:
            behavior()
        except BaseException as error:  # noqa: BLE001
            self.errors.append(error)

    def join(self) -> None:
        """Wait for node B, then raise what it raised, if anything."""
        self.thread.join(timeout=5.0)
        if self.errors:
            raise self.errors[0]
        assert not self.thread.is_alive(), "node B never finished"


class TestConnect:
    """The dialer completes a handshake with node B of EIP-8."""

    def test_connect_speaks_with_the_vector_secrets(
        self,
        listener: socket.socket,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A session built from the EIP-8 secrets reads what we send."""
        received: List[tuple[int, bytes]] = []

        def node_b() -> None:
            """Answer with Ack2, then frame as B under the EIP-8 secrets."""
            connection, _ = listener.accept()
            auth = _read_auth(connection)
            connection.sendall(ACK_VERSION_4)
            session = RLPxSession(
                connection,
                AES_SECRET,
                MAC_SECRET,
                egress_seed=_xor(MAC_SECRET, NONCE_A) + ACK_VERSION_4,
                ingress_seed=_xor(MAC_SECRET, NONCE_B) + auth,
            )
            session.set_timeout(5.0)
            received.append(session.read_message())
            session.write_message(0x11, b"from b")
            session.close()

        _fix_initiator_randomness(monkeypatch)
        node = _NodeB(node_b)
        session: RLPxSession | None = None
        try:
            session = _dial_node_b(listener)
            session.set_timeout(5.0)
            session.write_message(0x10, b"from a")
            assert session.read_message() == (0x11, b"from b")
        finally:
            if session is not None:
                session.close()
            node.join()
        assert received == [(0x10, b"from a")]

    def test_a_malformed_ack_is_a_handshake_error(
        self,
        listener: socket.socket,
    ) -> None:
        """An ack that fails decryption raises `RLPxError`."""

        def node_b() -> None:
            """Answer the auth with a well-sized but garbage ack."""
            connection, _ = listener.accept()
            _read_auth(connection)
            connection.sendall(len(ACK_VERSION_4[2:]).to_bytes(2, "big"))
            connection.sendall(bytes(len(ACK_VERSION_4) - 2))
            connection.recv(1)
            connection.close()

        node = _NodeB(node_b)
        try:
            with pytest.raises(RLPxError, match="malformed handshake"):
                _dial_node_b(listener)
        finally:
            node.join()

    @pytest.mark.parametrize(
        "fields",
        [
            SHORT_ACK_FIELDS["short-nonce"],
            [b"\x00" * 63 + b"\x01", NONCE_B],
        ],
        ids=["short-nonce", "key-off-the-curve"],
    )
    def test_a_malformed_ack_field_fails_the_dial_and_hangs_up(
        self,
        listener: socket.socket,
        fields: List[bytes],
    ) -> None:
        """The dialer raises `RLPxError` and closes its end at once."""
        read_after_ack: List[bytes] = []

        def node_b() -> None:
            """Answer the auth with an ack carrying `fields`."""
            connection, _ = listener.accept()
            connection.settimeout(5.0)
            _read_auth(connection)
            connection.sendall(_ack(fields))
            read_after_ack.append(connection.recv(1))
            connection.close()

        node = _NodeB(node_b)
        try:
            with pytest.raises(RLPxError, match="malformed"):
                _dial_node_b(listener)
        finally:
            node.join()
        assert read_after_ack == [b""]
