"""
Tests for the binary trie implementation.
"""

import pytest

from ethereum.forks.amsterdam.bintrie import (
    BASIC_DATA_LEAF_KEY,
    CODE_HASH_LEAF_KEY,
    BinaryTree,
    copy_tree,
    get_tree_key_for_basic_data,
    get_tree_key_for_code_hash,
    root,
    trie_get,
    trie_set,
)


class TestBinaryTreeOperations:
    """Test basic insert/get operations."""

    def test_insert_and_get(self):
        """Insert a key-value pair and retrieve it."""
        tree = BinaryTree()
        key = b"\xab" * 32
        value = b"\xcd" * 32
        tree.insert(key, value)
        assert tree.get(key) == value

    def test_get_missing_key(self):
        """Getting a missing key returns None."""
        tree = BinaryTree()
        assert tree.get(b"\x00" * 32) is None

    def test_same_stem_different_suffix(self):
        """Keys with same stem but different suffix are stored separately."""
        tree = BinaryTree()
        stem = b"\xab" * 31
        tree.insert(stem + b"\x00", b"\x11" * 32)
        tree.insert(stem + b"\xff", b"\x22" * 32)
        assert tree.get(stem + b"\x00") == b"\x11" * 32
        assert tree.get(stem + b"\xff") == b"\x22" * 32

    def test_different_stems(self):
        """Keys with different stems cause tree to split."""
        tree = BinaryTree()
        tree.insert(b"\x00" * 32, b"\x11" * 32)
        tree.insert(b"\xff" * 32, b"\x22" * 32)
        assert tree.get(b"\x00" * 32) == b"\x11" * 32
        assert tree.get(b"\xff" * 32) == b"\x22" * 32


class TestMerkleRoot:
    """Test merkleization."""

    def test_empty_tree(self):
        """Empty tree has zero root."""
        tree = BinaryTree()
        assert tree.merkelize() == b"\x00" * 32

    def test_deterministic(self):
        """Same tree produces same root."""
        tree = BinaryTree()
        tree.insert(b"\x00" * 32, b"\x42" * 32)
        assert tree.merkelize() == tree.merkelize()

    def test_different_values_different_roots(self):
        """Different values produce different roots."""
        t1, t2 = BinaryTree(), BinaryTree()
        t1.insert(b"\x00" * 32, b"\x11" * 32)
        t2.insert(b"\x00" * 32, b"\x22" * 32)
        assert t1.merkelize() != t2.merkelize()


class TestCopyTree:
    """Test tree copying."""

    def test_copy_is_independent(self):
        """Copied tree is independent of original."""
        t1 = BinaryTree()
        t1.insert(b"\x00" * 32, b"\x11" * 32)
        t2 = copy_tree(t1)
        t2.insert(b"\x00" * 32, b"\x22" * 32)
        assert t1.get(b"\x00" * 32) == b"\x11" * 32
        assert t2.get(b"\x00" * 32) == b"\x22" * 32


class TestTreeKeys:
    """Test tree key computation."""

    def test_basic_data_key(self):
        """Basic data key has correct suffix."""
        addr = b"\x00" * 12 + b"\xab" * 20
        key = get_tree_key_for_basic_data(addr)
        assert len(key) == 32
        assert key[31] == BASIC_DATA_LEAF_KEY

    def test_code_hash_key(self):
        """Code hash key has correct suffix."""
        addr = b"\x00" * 12 + b"\xab" * 20
        key = get_tree_key_for_code_hash(addr)
        assert len(key) == 32
        assert key[31] == CODE_HASH_LEAF_KEY

    def test_same_address_same_stem(self):
        """Same address produces same stem for different key types."""
        addr = b"\x00" * 12 + b"\xab" * 20
        key1 = get_tree_key_for_basic_data(addr)
        key2 = get_tree_key_for_code_hash(addr)
        assert key1[:31] == key2[:31]


class TestTrieInterface:
    """Test trie interface functions."""

    def test_trie_set_get(self):
        """trie_set and trie_get work together."""
        tree = BinaryTree()
        trie_set(tree, b"\xab" * 32, b"\xcd" * 32)
        assert trie_get(tree, b"\xab" * 32) == b"\xcd" * 32

    def test_trie_get_missing(self):
        """trie_get returns zero bytes for missing key."""
        tree = BinaryTree()
        assert trie_get(tree, b"\x00" * 32) == b"\x00" * 32

    def test_root(self):
        """root function returns 32 byte hash."""
        tree = BinaryTree()
        trie_set(tree, b"\x00" * 32, b"\x42" * 32)
        r = root(tree)
        assert len(r) == 32
