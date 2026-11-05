"""leanSPHINCS keys for EIP-8141 frame transaction tests."""

from functools import cached_property

import py_lean_pq

LEANSPHINCS_SEED_LENGTH = 32
"""Length of the seed a leanSPHINCS key is grown from."""

LEANSPHINCS_PUBLIC_KEY_LENGTH = 32
"""Length of a leanSPHINCS public key."""

LEANSPHINCS_SIGNATURE_LENGTH = 7740
"""Length of a leanSPHINCS signature."""


class LeanSphincsKey:
    """A leanSPHINCS key grown from a 32-byte seed."""

    seed: bytes

    def __init__(self, seed: bytes) -> None:
        """Create the key grown from `seed`."""
        assert len(seed) == LEANSPHINCS_SEED_LENGTH
        self.seed = bytes(seed)

    def _secret_key(self) -> py_lean_pq.SphincsSecretKey:
        return py_lean_pq.SphincsSecretKey.from_seed(self.seed)

    @cached_property
    def public_key(self) -> bytes:
        """Return the key's 32-byte public key."""
        public_key = self._secret_key().public_key
        assert len(public_key) == LEANSPHINCS_PUBLIC_KEY_LENGTH
        return public_key

    def sign(self, message: bytes) -> bytes:
        """Return the signature of a 32-byte `message`."""
        signature = self._secret_key().sign(bytes(message))
        assert len(signature) == LEANSPHINCS_SIGNATURE_LENGTH
        return signature

    def __repr__(self) -> str:
        """Return the key's public key, never its seed."""
        return f"LeanSphincsKey(public_key=0x{self.public_key.hex()})"
