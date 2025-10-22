"""Utility functions and sentinel classes for Ethereum test types."""

from typing import Any

from ethereum_test_base_types import Bytes, Hash


def keccak256(data: bytes) -> Hash:
    """Calculate keccak256 hash of the given data."""
    return Bytes(data).keccak256()


def int_to_bytes(value: int) -> bytes:
    """Convert integer to its big-endian representation."""
    if value == 0:
        return b""

    return int_to_bytes(value // 256) + bytes([value % 256])


# Sentinel classes
class Removable:
    """
    Sentinel class to detect if a parameter should be removed.
    (`None` normally means "do not modify").
    """

    def __eq__(self, other: Any) -> bool:
        """Return True for all Removable."""
        if not isinstance(other, Removable):
            return NotImplemented
        return True
