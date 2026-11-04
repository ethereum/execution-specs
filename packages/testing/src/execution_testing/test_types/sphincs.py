"""leanSPHINCS keys for EIP-8141 frame transaction tests."""

from functools import cached_property

import py_lean_pq

from execution_testing.base_types import Address

from .utils import keccak256

SPHINCS_SEED_LENGTH = 32
"""Length of the seed a leanSPHINCS key is grown from."""

SPHINCS_PUBLIC_KEY_LENGTH = 32
"""Length of a leanSPHINCS public key."""

SPHINCS_SIGNATURE_LENGTH = 7740
"""Length of a leanSPHINCS signature."""

SPHINCS_ENTRY_SIGNATURE_LENGTH = (
    SPHINCS_PUBLIC_KEY_LENGTH + SPHINCS_SIGNATURE_LENGTH
)
"""
Length of an EIP-8141 SPHINCS entry's raw signature bytes: the public
key followed by the signature.
"""


class SphincsKey:
    """A leanSPHINCS key grown from a 32-byte seed."""

    seed: bytes

    def __init__(self, seed: bytes) -> None:
        """Create the key grown from `seed`."""
        assert len(seed) == SPHINCS_SEED_LENGTH
        self.seed = bytes(seed)

    def _secret_key(self) -> py_lean_pq.SphincsSecretKey:
        return py_lean_pq.SphincsSecretKey.from_seed(self.seed)

    @cached_property
    def public_key(self) -> bytes:
        """Return the key's 32-byte public key."""
        public_key = self._secret_key().public_key
        assert len(public_key) == SPHINCS_PUBLIC_KEY_LENGTH
        return public_key

    @cached_property
    def address(self) -> Address:
        """Return the address the public key hashes to."""
        return Address(keccak256(self.public_key)[12:])

    def sign(self, message: bytes) -> bytes:
        """Return the signature of a 32-byte `message`."""
        signature = self._secret_key().sign(bytes(message))
        assert len(signature) == SPHINCS_SIGNATURE_LENGTH
        return signature

    def entry_signature(self, message: bytes) -> bytes:
        """
        Return the raw signature bytes of an EIP-8141 SPHINCS entry over
        `message`: the public key followed by the signature.
        """
        return self.public_key + self.sign(message)

    def __repr__(self) -> str:
        """Return the key's address, never its seed."""
        return f"SphincsKey(address={self.address})"
