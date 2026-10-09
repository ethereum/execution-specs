"""Defines EIP-8250 specification constants and types."""

from dataclasses import dataclass
from typing import Sequence

from execution_testing import Address, keccak256


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8250 = ReferenceSpec(
    "EIPS/eip-8250.md", "8b225fbc980e98831058a393c0f35df6e878bda0"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-8250 specification as defined at
    https://eips.ethereum.org/EIPS/eip-8250.
    """

    NONCE_MANAGER = Address(0x8250968C12E01A19D6F667B9B2F3B3A4D0E51CB7)
    NONCE_MANAGER_CODE = bytes.fromhex("60006000fd")
    NONCE_MANAGER_NONCE = 1
    MAX_NONCE_KEYS = 16
    MAX_NONCE_SEQ = 2**64 - 1

    # `0x11` is the first selector after the four this EIP adds.
    TXPARAM_NONCE_SEQ = 0x01
    TXPARAM_LEGACY_NONCE = 0x0D
    TXPARAM_NONCE_KEY_COUNT = 0x0E
    TXPARAM_NONCE_KEYS_HASH = 0x0F
    TXPARAM_NONCE_KEY_0 = 0x10
    TXPARAM_FIRST_UNDEFINED = 0x11


def keyed_nonce_slot(sender: Address, nonce_key: int) -> int:
    """
    Return the `NONCE_MANAGER` slot holding `sender`'s sequence for
    `nonce_key`.
    """
    padded_sender = bytes(12) + bytes(sender)
    key_bytes = nonce_key.to_bytes(32, "big")
    return int.from_bytes(keccak256(padded_sender + key_bytes), "big")


def nonce_keys_hash(nonce_keys: Sequence[int]) -> int:
    """Return the `TXPARAM` hash of a nonce key set."""
    encoded = len(nonce_keys).to_bytes(32, "big")
    for key in nonce_keys:
        encoded += key.to_bytes(32, "big")
    return int.from_bytes(keccak256(encoded), "big")
