"""
leanSPHINCS keys for EIP-8141 frame transaction tests.

Key generation and signing run EthLib's compiled specification, which
takes tens of seconds per call, so their results are cached on disk,
keyed by the seed and the message. Signing is deterministic, so a
cached signature is the one signing would produce.
"""

import hashlib
from functools import cached_property
from pathlib import Path
from typing import Callable

from ethlib.cryptography import sphincs
from filelock import FileLock
from platformdirs import user_cache_dir

from execution_testing.base_types import Address

from .utils import keccak256

SPHINCS_PUBLIC_KEY_LENGTH = sphincs.PUB_KEY_SIZE
"""Length of a leanSPHINCS public key."""

SPHINCS_SIGNATURE_LENGTH = sphincs.SIG_SIZE
"""Length of a leanSPHINCS signature."""

SPHINCS_ENTRY_SIGNATURE_LENGTH = (
    SPHINCS_PUBLIC_KEY_LENGTH + SPHINCS_SIGNATURE_LENGTH
)
"""
Length of an EIP-8141 SPHINCS entry's raw signature bytes: the public
key followed by the signature.
"""

CACHE_DIRECTORY = Path(user_cache_dir("ethereum-execution-testing")) / (
    "sphincs"
)
"""Directory holding cached public keys and signatures."""


def _cached(name: str, length: int, compute: Callable[[], bytes]) -> bytes:
    """
    Return the bytes cached under `name`, computing and storing them on
    a miss.
    """
    CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIRECTORY / name
    with FileLock(str(path) + ".lock"):
        if path.exists():
            data = path.read_bytes()
            if len(data) == length:
                return data
        data = compute()
        assert len(data) == length
        path.write_bytes(data)
        return data


class SphincsKey:
    """A leanSPHINCS key grown from a 32-byte seed."""

    seed: bytes

    def __init__(self, seed: bytes) -> None:
        """Create the key grown from `seed`."""
        assert len(seed) == sphincs.SEED_LEN
        self.seed = bytes(seed)

    @cached_property
    def _seed_id(self) -> str:
        return hashlib.sha256(self.seed).hexdigest()

    @cached_property
    def public_key(self) -> bytes:
        """Return the key's 32-byte public key."""
        return _cached(
            f"{self._seed_id}.pk",
            SPHINCS_PUBLIC_KEY_LENGTH,
            lambda: sphincs.key_gen(self.seed),
        )

    @cached_property
    def address(self) -> Address:
        """Return the address the public key hashes to."""
        return Address(keccak256(self.public_key)[12:])

    def sign(self, message: bytes) -> bytes:
        """Return the signature of a 32-byte `message`."""
        message = bytes(message)
        return _cached(
            f"{self._seed_id}.{message.hex()}.sig",
            SPHINCS_SIGNATURE_LENGTH,
            lambda: sphincs.sign(self.seed, message),
        )

    def entry_signature(self, message: bytes) -> bytes:
        """
        Return the raw signature bytes of an EIP-8141 SPHINCS entry over
        `message`: the public key followed by the signature.
        """
        return self.public_key + self.sign(message)

    def __repr__(self) -> str:
        """Return the key's address, never its seed."""
        return f"SphincsKey(address={self.address})"


def sphincs_verify(
    public_key: bytes, message: bytes, signature: bytes
) -> bool:
    """Return whether `signature` signs `message` under `public_key`."""
    return sphincs.verify(bytes(public_key), bytes(message), bytes(signature))
