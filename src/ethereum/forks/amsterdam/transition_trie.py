"""
Transition Trie.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

A transition trie that overlays a BinaryTree on top of a base Trie.
Reads check the overlay first, then fall back to the base.
Writes always go to the overlay.
"""

from typing import Callable, Optional

from ethereum_types.bytes import Bytes32

from .bintrie import BinaryTree
from .fork_types import Address, Root
from .trie import Trie
from .trie import trie_get as base_trie_get


class TransitionTree:
    """A tree that overlays a BinaryTree on top of a base Trie."""

    def __init__(self, base: Trie, overlay: BinaryTree):
        """
        Initialize a TransitionTree.

        Parameters
        ----------
        base :
            The base Trie for fallback reads.
        overlay :
            The overlay BinaryTree for writes and primary reads.

        """
        self.base = base
        self.overlay = overlay

    def get(self, key: Bytes32) -> Optional[bytes]:
        """
        Get a value by key, checking overlay first then base.

        Parameters
        ----------
        key :
            The 32-byte key to look up.

        Returns
        -------
        value : Optional[bytes]
            The value if found, or None if not found in either tree.

        """
        # Check overlay first
        value = self.overlay.get(key)
        if value is not None:
            return value

        # Fall back to base trie
        base_value = base_trie_get(self.base, key)
        if base_value is None or base_value == self.base.default:
            return None

        # Convert to bytes if needed
        if isinstance(base_value, bytes):
            return base_value
        return None

    def insert(self, key: Bytes32, value: bytes) -> None:
        """
        Insert a key-value pair into the overlay.

        Parameters
        ----------
        key :
            The 32-byte key.
        value :
            The value to store (must be 32 bytes for BinaryTree).

        """
        self.overlay.insert(key, value)


def trie_get(trie: TransitionTree, key: Bytes32) -> Bytes32:
    """
    Get a value from the transition trie at the given key.

    Parameters
    ----------
    trie :
        The TransitionTree to read from.
    key :
        The 32-byte key to look up.

    Returns
    -------
    value : Bytes32
        The value at the key, or 0 if not found.

    """
    v = trie.get(key)
    if v is None:
        return Bytes32(b'\x00' * 32)
    return v


def trie_set(trie: TransitionTree, key: Bytes32, value: bytes) -> None:
    """
    Set a value in the transition trie at the given key.

    Parameters
    ----------
    trie :
        The TransitionTree to write to.
    key :
        The 32-byte key.
    value :
        The value to store.

    """
    trie.insert(key, value)


def root(
    trie: TransitionTree,
    _: Optional[Callable[[Address], Root]] = None,
) -> Root:
    """
    Compute and return the root hash of the overlay tree.

    Parameters
    ----------
    trie :
        The TransitionTree to compute the root of.
    _ :
        Unused parameter for API compatibility.

    Returns
    -------
    root : Root
        The merkle root of the overlay BinaryTree.

    """
    return Root(trie.overlay.merkelize())
