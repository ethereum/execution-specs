"""
Binary Trie.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

The state trie is the structure responsible for storing
`.fork_types.Account` objects.
"""

# import copy
from typing import (
    Callable,
    Optional,
)

from ethereum_types.bytes import Bytes32

# from ethereum.forks.bpo5 import trie as previous_trie

from .fork_types import Account, Address, Root

from blake3 import blake3

class StemNode:
    def __init__(self, stem: bytes):
        assert len(stem) == 31, "stem must be 31 bytes"
        self.stem = stem
        self.values: list[Optional[bytes]] = [None] * 256

    def set_value(self, index: int, value: bytes):
        self.values[index] = value

    def get_value(self, index: int) -> Optional[bytes]:
        return self.values[index]

class InternalNode:
    def __init__(self):
        self.left = None
        self.right = None

class BinaryTree:
    def __init__(self):
        self.root = None

    def insert(self, key: bytes, value: bytes):
        assert len(key) == 32, "key must be 32 bytes"
        assert len(value) == 32, "value must be 32 bytes"
        stem = key[:31]
        subindex = key[31]

        if self.root is None:
            self.root = StemNode(stem)
            self.root.set_value(subindex, value)
            return

        self.root = self._insert(self.root, stem, subindex, value, 0)

    def _insert(self, node, stem, subindex, value, depth):
        assert depth < 248, "depth must be less than 248"

        if node is None:
            node = StemNode(stem)
            node.set_value(subindex, value)
            return node

        stem_bits = self._bytes_to_bits(stem)
        if isinstance(node, StemNode):
            # If the stem already exists, update the value.
            if node.stem == stem:
                node.set_value(subindex, value)
                return node
            existing_stem_bits = self._bytes_to_bits(node.stem)
            return self._split_leaf(
                node, stem_bits, existing_stem_bits, subindex, value, depth
            )

        # We're in an internal node, go left or right based on the bit.
        bit = stem_bits[depth]
        if bit == 0:
            node.left = self._insert(node.left, stem, subindex, value, depth + 1)
        else:
            node.right = self._insert(node.right, stem, subindex, value, depth + 1)
        return node

    def get(self, key: bytes) -> Optional[bytes]:
        assert len(key) == 32, "key must be 32 bytes"

        if self.root is None:
            return None

        return self._get(self.root, key[:31], key[31], 0)

    def _get(self, node, stem, subindex, depth) -> Optional[bytes]:
        assert depth < 248, "depth must be less than 248"

        if node is None:
            return None

        stem_bits = self._bytes_to_bits(stem)
        if isinstance(node, StemNode):
            if node.stem == stem:
                return node.get_value(subindex)

            # Stems differ, value is missing
            return None

        bit = stem_bits[depth]
        if bit == 0:
            return self._get(self.left, stem, subindex, depth+1)
        else:
            return self._get(self.right, stem, subindex, depth+1)

    def _split_leaf(self, leaf, stem_bits, existing_stem_bits, subindex, value, depth):
        # If the stem bits are the same up to this depth, we need to create
        # another internal node and recurse.
        if stem_bits[depth] == existing_stem_bits[depth]:
            new_internal = InternalNode()
            bit = stem_bits[depth]
            if bit == 0:
                new_internal.left = self._split_leaf(
                    leaf, stem_bits, existing_stem_bits, subindex, value, depth + 1
                )
            else:
                new_internal.right = self._split_leaf(
                    leaf, stem_bits, existing_stem_bits, subindex, value, depth + 1
                )
            return new_internal
        else:
            new_internal = InternalNode()
            bit = stem_bits[depth]
            stem = self._bits_to_bytes(stem_bits)
            if bit == 0:
                new_internal.left = StemNode(stem)
                new_internal.left.set_value(subindex, value)
                new_internal.right = leaf
            else:
                new_internal.right = StemNode(stem)
                new_internal.right.set_value(subindex, value)
                new_internal.left = leaf
            return new_internal

    def _bytes_to_bits(self, byte_data):
        bits = []
        for byte in byte_data:
            for i in range(8):
                bits.append((byte >> (7 - i)) & 1)
        return bits

    def _bits_to_bytes(self, bits):
        byte_data = bytearray()
        for i in range(0, len(bits), 8):
            byte = 0
            for j in range(8):
                byte |= bits[i + j] << (7 - j)
            byte_data.append(byte)
        return bytes(byte_data)

    def _hash(self, data):
        if data in (None, b"\x00" * 64):
            return b"\x00" * 32

        assert len(data) == 64 or len(data) == 32, "data must be 32 or 64 bytes"
        return blake3(data).digest()

    def merkelize(self):
        def _merkelize(node):
            if node is None:
                return b"\x00" * 32
            if isinstance(node, InternalNode):
                left_hash = _merkelize(node.left)
                right_hash = _merkelize(node.right)
                return self._hash(left_hash + right_hash)

            level = [self._hash(x) for x in node.values]
            while len(level) > 1:
                new_level = []
                for i in range(0, len(level), 2):
                    new_level.append(self._hash(level[i] + level[i + 1]))
                level = new_level

            return self._hash(node.stem + b"\0" + level[0])

        return _merkelize(self.root)

# def copy_trie(trie: Trie[K, V]) -> Trie[K, V]:
#     """
#     Create a copy of `trie`. Since only frozen objects may be stored in tries,
#     the contents are reused.

#     Parameters
#     ----------
#     trie: `Trie`
#         Trie to copy.

#     Returns
#     -------
#     new_trie : `Trie[K, V]`
#         A copy of the trie.

#     """
#     return Trie(trie.secured, trie.default, copy.copy(trie._data))

# TODO replace value : bytes by several types: accounts or slots
def trie_set(trie: BinaryTree, key: Bytes32, value: bytes) -> None:
    """
    """
    # TODO compute key using get_tree_key
    trie.insert(key, value)


def trie_get(trie: BinaryTree, key: Bytes32) -> Bytes32:
    """
    """
    v = trie.get(key)
    if v is None:
        v = 0
    return v


def root(
    trie: BinaryTree,
    _: Optional[Callable[[Address], Root]] = None,
) -> Root:
    """
    """
    return Root(trie.merkleize())
