"""
Fill-time Merkle Patricia Trie shape inspection.

Walks the reference implementation's `patricialize` along one key and
reports the node kind at every depth, so a test can assert the structure
it claims to exercise ("a 16-child branch at depth 4", "an extension of 5
nibbles") instead of stating it in prose. Only key positions matter for
topology, so every key is given the same placeholder value.
"""

from typing import Iterable, List, Sequence, Tuple

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import keccak256
from ethereum.merkle_patricia_trie import (
    BranchNode,
    ExtensionNode,
    LeafNode,
    bytes_to_nibble_list,
    nibble_list_to_compact,
    patricialize,
)

Shape = List[Tuple[int, str, int]]
"""`(depth, kind, size)` per node on the path: kind is `leaf` (size =
remaining nibbles), `ext` (size = segment nibbles), `branch` (size =
child count) or `empty` (size 0, an empty trie)."""


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


def storage_shape(slots: Sequence[int], target: int) -> Shape:
    """Shape along `target` in a storage trie holding `slots`."""
    return path_shape([slot_key(s) for s in slots], slot_key(target))


def account_shape(addresses: Iterable[bytes], target: bytes) -> Shape:
    """Shape along `target` in an account trie holding `addresses`."""
    return path_shape([bytes(a) for a in addresses], bytes(target))


def index_shape(count: int, position: int) -> Shape:
    """Shape along `position` in an index trie of `count` entries."""
    keys = [bytes(rlp.encode(Uint(i))) for i in range(count)]
    return path_shape(keys, keys[position], secured=False)


def node_at(shape: Shape, depth: int) -> Tuple[str, int]:
    """Return `(kind, size)` of the node positioned exactly at `depth`."""
    for d, kind, size in shape:
        if d == depth:
            return kind, size
    raise AssertionError(f"no node at depth {depth} in {shape}")


def covering(shape: Shape, depth: int) -> Tuple[int, str, int]:
    """
    Return the node whose span contains `depth`.

    A branch spans one nibble, an extension its segment, a leaf the rest
    of the key. Unlike `node_at`, this never raises on a well-formed path,
    so an assertion about "what sits at depth 4" is never vacuous.
    """
    for entry in shape:
        d, kind, size = entry
        span = {"branch": 1, "ext": size}.get(kind, 64 - d)
        if d <= depth < d + span:
            return entry
    raise AssertionError(f"depth {depth} beyond {shape}")


def slot_key(slot: int) -> bytes:
    """Storage-trie preimage for a slot index."""
    return slot.to_bytes(32, "big")


def leaf_rlp_size(rest_nibbles: int, value_rlp: bytes) -> int:
    """
    RLP size of a leaf with `rest_nibbles` left and an RLP-encoded value.

    Mirrors `encode_internal_node`: under 32 bytes the node is inlined into
    its parent, from 32 bytes on it is referenced by hash.
    """
    compact = nibble_list_to_compact(Bytes(bytes(rest_nibbles)), True)
    return len(rlp.encode((compact, Bytes(value_rlp))))


def storage_leaf_size(rest_nibbles: int, value: int) -> int:
    """`leaf_rlp_size` for a storage slot holding `value`."""
    return leaf_rlp_size(rest_nibbles, bytes(rlp.encode(U256(value))))
