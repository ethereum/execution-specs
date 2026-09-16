"""
Fill-time Merkle Patricia Trie shape inspection.

Walks the reference implementation's `patricialize` along one key and
reports the node kind at every depth, so a test can assert the structure
it claims to exercise ("a 16-child branch at depth 4", "an extension of 5
nibbles") instead of stating it in prose. Only key positions matter for
topology, so every key is given the same placeholder value.
"""

from typing import Iterable, List, Tuple

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import Uint

from ethereum.crypto.hash import keccak256
from ethereum.merkle_patricia_trie import (
    BranchNode,
    ExtensionNode,
    LeafNode,
    bytes_to_nibble_list,
    patricialize,
)

Shape = List[Tuple[int, str, int]]
"""`(depth, kind, size)` per node on the path: kind is `leaf` (size =
remaining nibbles), `ext` (size = segment nibbles) or `branch` (size =
child count)."""


def _nibbles(preimage: bytes, secured: bool) -> Bytes:
    key = keccak256(preimage) if secured else preimage
    return bytes_to_nibble_list(Bytes(key))


def path_shape(
    preimages: Iterable[bytes], target: bytes, secured: bool = True
) -> Shape:
    """Return the node shape along `target`'s path in a trie of `preimages`."""
    mapping = {_nibbles(p, secured): Bytes(b"\x01") for p in preimages}
    key = _nibbles(target, secured)
    depth = 0
    shape: Shape = []
    while True:
        node = patricialize(mapping, Uint(depth))
        if node is None:
            shape.append((depth, "empty", 0))
            return shape
        if isinstance(node, LeafNode):
            shape.append((depth, "leaf", len(node.rest_of_key)))
            return shape
        if isinstance(node, ExtensionNode):
            shape.append((depth, "ext", len(node.key_segment)))
            depth += len(node.key_segment)
            continue
        assert isinstance(node, BranchNode)
        children = sum(1 for child in node.subnodes if child != b"")
        shape.append((depth, "branch", children))
        nibble = key[depth]
        mapping = {k: v for k, v in mapping.items() if k[depth] == nibble}
        depth += 1


def node_at(shape: Shape, depth: int) -> Tuple[str, int]:
    """Return `(kind, size)` of the node positioned at `depth`."""
    for d, kind, size in shape:
        if d == depth:
            return kind, size
    raise AssertionError(f"no node at depth {depth} in {shape}")


def slot_key(slot: int) -> bytes:
    """Storage-trie preimage for a slot index."""
    return slot.to_bytes(32, "big")
