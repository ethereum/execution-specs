"""
Tests for the ECIES scheme protecting the RLPx handshake messages.

A round trip alone cannot catch a key derivation bug shared by both
directions, so decryption is pinned to the EIP-8 auth vector, which
another implementation encrypted.
"""

import pytest

from ..ecies import DecryptionError, decrypt
from .handshake_vectors import AUTH_VERSION_4, NONCE_A, STATIC_KEY_B

PREFIX = AUTH_VERSION_4[:2]
"""The size prefix, authenticated as the shared MAC data."""

MESSAGE = AUTH_VERSION_4[2:]
"""The ECIES message that follows the size prefix."""


class TestDecrypt:
    """Decryption authenticates everything the tag covers."""

    def test_the_vector_auth_decrypts(self) -> None:
        """The EIP-8 auth decrypts to a body carrying Nonce A."""
        assert NONCE_A in decrypt(STATIC_KEY_B, MESSAGE, PREFIX)

    def test_the_tag_covers_the_shared_mac_data(self) -> None:
        """A changed size prefix fails the tag check."""
        tampered_prefix = bytes([PREFIX[0], PREFIX[1] ^ 1])
        with pytest.raises(DecryptionError, match="tag mismatch"):
            decrypt(STATIC_KEY_B, MESSAGE, tampered_prefix)

    def test_the_tag_covers_the_ciphertext(self) -> None:
        """A flipped ciphertext byte fails the tag check."""
        tampered = bytearray(MESSAGE)
        tampered[100] ^= 1
        with pytest.raises(DecryptionError, match="tag mismatch"):
            decrypt(STATIC_KEY_B, bytes(tampered), PREFIX)

    def test_a_truncated_message_is_refused(self) -> None:
        """A message shorter than the ECIES overhead raises."""
        with pytest.raises(DecryptionError, match="malformed"):
            decrypt(STATIC_KEY_B, MESSAGE[:100], PREFIX)
