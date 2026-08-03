"""
Independent, insertion-based (incremental) implementation of the
binary radix trie, used by `test_trie.py` to cross-check
`ethereum.binary_trie.trie`'s rebuild-from-scratch implementation.
"""

from typing import List, Optional

from blake3 import blake3


def _bits(data: bytes) -> List[int]:
    return [(byte >> (7 - i)) & 1 for byte in data for i in range(8)]


def _pack_padded(bits: List[int]) -> bytes:
    packed = bytearray((len(bits) + 7) // 8)
    for i, bit in enumerate(bits):
        packed[i // 8] |= bit << (7 - i % 8)
    return bytes(packed)


def _leaf_hash(key: bytes, value: bytes) -> bytes:
    return blake3(b"\x00" + key + value).digest()


def _branch_hash(prefix: List[int], left: bytes, right: bytes) -> bytes:
    return blake3(
        b"\x01"
        + len(prefix).to_bytes(2, "big")
        + _pack_padded(prefix)
        + left
        + right
    ).digest()


class IncrementalRadixTree:
    """
    Insertion-based compressed binary radix tree, used only to
    cross-check `ethereum.binary_trie`.

    Follows the standard descend/split insertion algorithm and hashes
    with independently written tagged rules, so agreement with the
    rebuild-from-scratch spec implementation also checks that both
    produce the same canonical structure.
    """

    class Leaf:
        """
        Terminal node of the incremental implementation.
        """

        def __init__(self, key: bytes, value: bytes) -> None:
            self.key = key
            self.value = value

    class Branch:
        """
        Prefix-carrying binary branch of the incremental implementation.
        """

        def __init__(
            self, prefix: List[int], left: object, right: object
        ) -> None:
            self.prefix = prefix
            self.left = left
            self.right = right

    def __init__(self) -> None:
        self.root: Optional[object] = None

    def insert(self, key: bytes, value: bytes) -> None:
        """
        Insert `key` and `value`, splitting nodes as needed.
        """
        assert len(value) == 32
        if self.root is None:
            self.root = self.Leaf(key, value)
            return
        self.root = self._insert(self.root, _bits(key), key, value, 0)

    def _insert(  # type: ignore[no-untyped-def]
        self, node, bits, key, value, depth
    ):
        if isinstance(node, self.Leaf):
            if node.key == key:
                node.value = value
                return node
            other_bits = _bits(node.key)
            run = 0
            while True:
                position = depth + run
                assert position < len(bits) and position < len(other_bits)
                if bits[position] != other_bits[position]:
                    break
                run += 1
            prefix = bits[depth : depth + run]
            leaf = self.Leaf(key, value)
            if bits[depth + run] == 0:
                return self.Branch(prefix, leaf, node)
            return self.Branch(prefix, node, leaf)

        matched = 0
        while matched < len(node.prefix):
            position = depth + matched
            assert position < len(bits)
            if bits[position] != node.prefix[matched]:
                break
            matched += 1
        if matched == len(node.prefix):
            split = depth + matched
            assert split < len(bits)
            if bits[split] == 0:
                node.left = self._insert(
                    node.left, bits, key, value, split + 1
                )
            else:
                node.right = self._insert(
                    node.right, bits, key, value, split + 1
                )
            return node
        # The key diverges inside the prefix: the surviving branch
        # keeps the bits after the divergence, and a new branch takes
        # the bits before it.
        survivor = self.Branch(
            node.prefix[matched + 1 :], node.left, node.right
        )
        leaf = self.Leaf(key, value)
        if bits[depth + matched] == 0:
            return self.Branch(node.prefix[:matched], leaf, survivor)
        return self.Branch(node.prefix[:matched], survivor, leaf)

    def delete(self, key: bytes) -> None:
        """
        Remove `key` if present, collapsing the branch it leaves
        behind; deleting an absent key does nothing.
        """
        if self.root is None:
            return
        if isinstance(self.root, self.Leaf):
            if self.root.key == key:
                self.root = None
            return
        self.root = self._delete(self.root, _bits(key), key, 0)

    def _delete(  # type: ignore[no-untyped-def]
        self, node, bits, key, depth
    ):
        assert isinstance(node, self.Branch)
        matched = 0
        while matched < len(node.prefix):
            position = depth + matched
            if position >= len(bits) or bits[position] != node.prefix[matched]:
                return node  # The key is not in this subtree.
            matched += 1
        split = depth + matched
        if split >= len(bits):
            return node  # The key ends at the split; not present.

        take_left = bits[split] == 0
        child = node.left if take_left else node.right
        if isinstance(child, self.Branch):
            replacement = self._delete(child, bits, key, split + 1)
            if take_left:
                node.left = replacement
            else:
                node.right = replacement
            return node

        if child.key != key:
            return node

        # The child leaf is the deletion target: this branch now has a
        # single subtree, so the sibling takes its place. A leaf
        # sibling moves up unchanged (it commits its full key); a
        # branch sibling absorbs this branch's prefix and the split
        # bit that selected it into its own prefix.
        sibling = node.right if take_left else node.left
        if isinstance(sibling, self.Leaf):
            return sibling
        assert isinstance(sibling, self.Branch)
        sibling_bit = 1 if take_left else 0
        return self.Branch(
            node.prefix + [sibling_bit] + sibling.prefix,
            sibling.left,
            sibling.right,
        )

    def merkelize(self) -> bytes:
        """
        Compute the root hash of the reference tree.
        """
        if self.root is None:
            return b"\x00" * 32

        def _hash(node: object) -> bytes:
            if isinstance(node, self.Leaf):
                return _leaf_hash(node.key, node.value)
            assert isinstance(node, self.Branch)
            return _branch_hash(
                node.prefix, _hash(node.left), _hash(node.right)
            )

        return _hash(self.root)
