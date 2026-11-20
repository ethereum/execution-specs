"""
The ECIES scheme that protects the RLPx handshake messages.

RLPx encrypts its `auth` and `ack` messages with ECIES: an ephemeral
Diffie-Hellman agreement feeds a concatenation KDF, whose output is split
into an AES-128-CTR key and a HMAC-SHA256 key. The two byte big endian
length prefix of the message is authenticated alongside the ciphertext as
shared MAC data.
"""

import hashlib
import hmac
import os

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from .secp256k1 import agree, public_key_bytes

PUBLIC_KEY_LENGTH = 64
"""Length of an uncompressed public key without its SEC tag."""

_IV_LENGTH = 16
_MAC_LENGTH = 32

OVERHEAD = 1 + PUBLIC_KEY_LENGTH + _IV_LENGTH + _MAC_LENGTH
"""Bytes an encrypted message adds to its plaintext."""


class DecryptionError(Exception):
    """Raised when an ECIES message fails its authentication check."""


def _concat_kdf(shared_secret: bytes) -> bytes:
    """
    Derive 32 key bytes from `shared_secret` (NIST SP 800-56 KDF).

    One SHA-256 block is 32 bytes, so the KDF runs once, at counter 1.
    """
    return hashlib.sha256(b"\x00\x00\x00\x01" + shared_secret).digest()


def _aes_ctr(key: bytes, initialization_vector: bytes, data: bytes) -> bytes:
    """Return `data` run through AES-128-CTR under `key`."""
    cipher = Cipher(
        algorithms.AES(key), modes.CTR(initialization_vector)
    ).encryptor()
    return cipher.update(data) + cipher.finalize()


def _tag(key_material: bytes, data: bytes) -> bytes:
    """Return the HMAC-SHA256 of `data` under the derived MAC key."""
    mac_key = hashlib.sha256(key_material[16:]).digest()
    return hmac.new(mac_key, data, hashlib.sha256).digest()


def encrypt(
    remote_public_key: bytes, plaintext: bytes, shared_mac_data: bytes
) -> bytes:
    """
    Encrypt `plaintext` to `remote_public_key`.

    The result is `ephemeral-public-key || iv || ciphertext || tag`, with
    `shared_mac_data` covered by the tag but not included in the output.
    """
    ephemeral_private_key = os.urandom(32)
    shared_secret = agree(ephemeral_private_key, remote_public_key)
    key_material = _concat_kdf(shared_secret)

    initialization_vector = os.urandom(_IV_LENGTH)
    ciphertext = _aes_ctr(key_material[:16], initialization_vector, plaintext)
    tag = _tag(
        key_material, initialization_vector + ciphertext + shared_mac_data
    )

    return (
        b"\x04"
        + public_key_bytes(ephemeral_private_key)
        + initialization_vector
        + ciphertext
        + tag
    )


def decrypt(
    private_key: bytes, message: bytes, shared_mac_data: bytes
) -> bytes:
    """
    Decrypt an ECIES `message` addressed to `private_key`.

    Raise `DecryptionError` if the message is truncated or its tag does
    not authenticate the ciphertext and `shared_mac_data`.
    """
    if len(message) < OVERHEAD or message[0] != 0x04:
        raise DecryptionError("malformed ECIES message")

    iv_start = 1 + PUBLIC_KEY_LENGTH
    ciphertext_start = iv_start + _IV_LENGTH
    ephemeral_public_key = message[1:iv_start]
    initialization_vector = message[iv_start:ciphertext_start]
    ciphertext = message[ciphertext_start:-_MAC_LENGTH]
    tag = message[-_MAC_LENGTH:]

    key_material = _concat_kdf(agree(private_key, ephemeral_public_key))
    expected_tag = _tag(
        key_material, initialization_vector + ciphertext + shared_mac_data
    )
    if not hmac.compare_digest(tag, expected_tag):
        raise DecryptionError("ECIES tag mismatch")

    return _aes_ctr(key_material[:16], initialization_vector, ciphertext)
