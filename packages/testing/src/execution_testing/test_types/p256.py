"""Deterministic NIST P-256 (secp256r1) signing for tests."""

from typing import NamedTuple

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    Prehashed,
    decode_dss_signature,
)
from cryptography.hazmat.primitives.hashes import SHA256

SECP256R1N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
"""Order of the NIST P-256 (secp256r1) curve."""


class P256Signature(NamedTuple):
    """A P-256 signature and the public key that verifies it."""

    r: int
    s: int
    qx: int
    qy: int

    def __bytes__(self) -> bytes:
        """Return `r || s || qx || qy`, each a 32-byte big-endian word."""
        return b"".join(
            sig.to_bytes(32, "big")
            for sig in (self.r, self.s, self.qx, self.qy)
        )


def p256_sign(digest: bytes, key: int | bytes) -> P256Signature:
    """
    Sign a 32-byte `digest` with the P-256 private `key`.

    The digest is signed as is, without hashing it again, as P256VERIFY
    expects. The nonce is derived from the key and digest (RFC 6979), so
    the same inputs always give the same signature, and `s` is
    normalized to the lower half of the curve order.
    """
    if len(digest) != 32:
        raise ValueError(f"digest must be 32 bytes, got {len(digest)}")
    if isinstance(key, bytes):
        key = int.from_bytes(key, "big")
    private_key = ec.derive_private_key(key, ec.SECP256R1())
    r, s = decode_dss_signature(
        private_key.sign(
            digest, ec.ECDSA(Prehashed(SHA256()), deterministic_signing=True)
        )
    )
    public_key = private_key.public_key().public_numbers()
    return P256Signature(
        r=r, s=min(s, SECP256R1N - s), qx=public_key.x, qy=public_key.y
    )
