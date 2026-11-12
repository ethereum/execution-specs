"""NIST P-256 keys for EIP-8141 frame transaction tests."""

from functools import cached_property

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils

from execution_testing.base_types import Address, Bytes

P256_SIGNATURE_LENGTH = 128
"""Length of an EIP-8141 P256 signature: `r || s || qx || qy`."""

P256_ORDER = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
"""Order of the NIST P-256 curve."""


class P256Key:
    """A NIST P-256 key that signs deterministically (RFC 6979)."""

    secret: int

    def __init__(self, secret: int) -> None:
        """Create the key with private scalar `secret`."""
        assert 0 < secret < P256_ORDER
        self.secret = secret

    def _private_key(self) -> ec.EllipticCurvePrivateKey:
        return ec.derive_private_key(self.secret, ec.SECP256R1())

    @cached_property
    def public_key(self) -> bytes:
        """Return the key's public key as `qx || qy`."""
        numbers = self._private_key().public_key().public_numbers()
        return numbers.x.to_bytes(32, "big") + numbers.y.to_bytes(32, "big")

    @cached_property
    def address(self) -> Address:
        """Return the address the key's public key hashes to."""
        return Address(Bytes(self.public_key).keccak256()[12:])

    def sign(self, digest: bytes) -> bytes:
        """Return the low-`s` signature of `digest` with the public key."""
        assert len(digest) == 32
        der = self._private_key().sign(
            bytes(digest),
            ec.ECDSA(
                utils.Prehashed(hashes.SHA256()), deterministic_signing=True
            ),
        )
        r, s = utils.decode_dss_signature(der)
        s = min(s, P256_ORDER - s)
        return r.to_bytes(32, "big") + s.to_bytes(32, "big") + self.public_key

    def __repr__(self) -> str:
        """Return the key's address, never its secret."""
        return f"P256Key(address={self.address})"
