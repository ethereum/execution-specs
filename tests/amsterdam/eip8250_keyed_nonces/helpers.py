"""Helpers for EIP-8250 keyed nonce tests."""

from typing import Dict, Iterable, Sequence

from execution_testing import Account, Address, Alloc, keccak256

from .spec import Spec

KEY_A = 0x0A
"""A small non-zero nonce key."""

KEY_B = 0x0B
"""A second small non-zero nonce key, above `KEY_A`."""

NULLIFIER_KEY = int.from_bytes(keccak256(b"nullifier")[1:], "big")
"""
A nonce key derived from a hash, as a privacy application would derive
it from a nullifier, keeping its most significant byte zero.
"""

FULL_WIDTH_KEY = 2**256 - 1
"""The largest nonce key, whose encoding is the widest a key can take."""


def nonce_slot(sender: Address, nonce_key: int) -> int:
    """
    Return the `NONCE_MANAGER` storage slot of `sender`'s sequence for
    `nonce_key`.
    """
    preimage = bytes(sender).rjust(32, b"\x00") + nonce_key.to_bytes(32, "big")
    return int.from_bytes(keccak256(preimage), "big")


def nonce_keys_hash(nonce_keys: Sequence[int]) -> int:
    """Return the `TXPARAM` commitment to a nonce key set."""
    words = len(nonce_keys).to_bytes(32, "big") + b"".join(
        key.to_bytes(32, "big") for key in nonce_keys
    )
    return int.from_bytes(keccak256(words), "big")


def keyed_storage(
    sender: Address, sequences: Dict[int, int]
) -> Dict[int, int]:
    """
    Return the `NONCE_MANAGER` storage holding `sender`'s sequence for
    each key in `sequences`.
    """
    return {nonce_slot(sender, key): seq for key, seq in sequences.items()}


def nonce_manager(storage: Dict[int, int] | None = None) -> Account:
    """
    Return the `NONCE_MANAGER` account as installed at activation,
    holding `storage`.
    """
    return Account(
        nonce=1,
        code=Spec.NONCE_MANAGER_CODE,
        storage=storage or {},
    )


def set_keyed_nonces(
    pre: Alloc, entries: Iterable[tuple[Address, Dict[int, int]]]
) -> None:
    """
    Seed the pre-state `NONCE_MANAGER` with the given keyed sequences,
    as left behind by earlier transactions.
    """
    storage: Dict[int, int] = {}
    for sender, sequences in entries:
        storage |= keyed_storage(sender, sequences)
    pre[Spec.NONCE_MANAGER] = nonce_manager(storage)
