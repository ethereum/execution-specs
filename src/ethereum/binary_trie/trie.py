"""
The raw key/value tree underlying the [EIP-8297] Partitioned Binary
Tree, structured as a compressed binary radix trie.

The tree maps variable-length keys to 32-byte values and commits to
its entire contents with a single root hash. Keys are consumed bit by
bit, most significant bit first, and must be prefix-free; see
[`Key`].

The mapping of keys to values is exposed through [`BinaryTrie`]; the
[`root`] function reduces a trie to its 32-byte commitment. The hash
function used here follows the EIP's reference implementation
(BLAKE3).

This module defines only the raw tree. How Ethereum state; accounts,
storage, and code is mapped into keys and values, including the
logical **stem** grouping, is defined in
[`ethereum.binary_trie.embedding`].

[EIP-8297]: https://eips.ethereum.org/EIPS/eip-8297
[`Key`]: ref:ethereum.binary_trie.trie.Key
[`BranchNode`]: ref:ethereum.binary_trie.trie.BranchNode
[`LeafNode`]: ref:ethereum.binary_trie.trie.LeafNode
[`BinaryTrie`]: ref:ethereum.binary_trie.trie.BinaryTrie
[`root`]: ref:ethereum.binary_trie.trie.root
[`ethereum.binary_trie.embedding`]: ref:ethereum.binary_trie.embedding
"""

import copy
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional, Union, final

from blake3 import blake3
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import Uint

from ethereum.crypto.hash import Hash32

EMPTY_TRIE_ROOT = Hash32(b"\x00" * 32)
"""
Root hash of an empty binary tree, defined as 32 zero bytes.

This is a sentinel value rather than a hash output: whp no input is
expected to hash to all zeroes, so it cannot collide with the
commitment of a non-empty tree.
"""


def blake3_hash(data: Bytes) -> Hash32:
    """
    Hash `data` with the tree's hash function.
    """
    return Hash32(blake3(data).digest())


def bytes_to_bit_list(data: Bytes) -> Bytes:
    """
    Expand each input byte into eight bits, most significant bit first.
    """
    return Bytes(
        bytearray(
            (byte >> (7 - offset)) & 1 for byte in data for offset in range(8)
        )
    )


Key = Bytes
"""
A tree key is any non-empty byte string, consumed bit by bit, MSB first.

Keys must be **prefix-free**, so no key may be a prefix of another. A
key is its path and a [`LeafNode`] ends a path, so a longer key
could never pass through the position a shorter key terminates at.

[`LeafNode`]: ref:ethereum.binary_trie.trie.LeafNode
[`binarize`]: ref:ethereum.binary_trie.trie.binarize
"""

MAX_KEY_LENGTH = Uint(8192)
"""
Longest key the tree accepts, in bytes.

The bound is derived from the prefix encoding algorithm: a branch prefix can
approach the full bit length of the keys sharing it, and
[`encode_bit_prefix`] stores the bit count in two bytes, so keys
longer than this could produce a prefix the encoding cannot
represent. Since this is worse case, in practice we can support keys
that are larger, but in terms of simplicity, enforcing the bound on
every key in [`trie_set`] keeps the limit a stated contract
instead of a data-dependent failure during merkleization.

[`encode_bit_prefix`]: ref:ethereum.binary_trie.trie.encode_bit_prefix
[`trie_set`]: ref:ethereum.binary_trie.trie.trie_set
"""

LEAF_NODE_TAG = Bytes(b"\x00")
"""
First byte of every [`LeafNode`] hash preimage.

This is needed so that two different nodes can never share a
preimage (since their first byte will always differ).

See [`merkleize`] for usage.

[`LeafNode`]: ref:ethereum.binary_trie.trie.LeafNode
[`merkleize`]: ref:ethereum.binary_trie.trie.merkleize
"""

BRANCH_NODE_TAG = Bytes(b"\x01")
"""
First byte of every [`BranchNode`] hash preimage.

[`BranchNode`]: ref:ethereum.binary_trie.trie.BranchNode
"""


@final
@slotted_freezable
@dataclass
class LeafNode:
    """
    Terminal node holding a single key's value.

    Note: the complete key is committed, not just the bits below the
    leaf's position, so a leaf's meaning never depends on the path
    taken to reach it.
    """

    key: Key
    """
    The complete key whose value this leaf holds.
    """

    value: Bytes32
    """
    The 32-byte value stored under [`key`].

    [`key`]: ref:ethereum.binary_trie.trie.LeafNode.key
    """


@final
@slotted_freezable
@dataclass
class BranchNode:
    """
    Binary branch splitting on a single bit, carrying the run of bits
    every key below it shares beyond the bits consumed above it.

    (We have essentially inlined the concept of an extension node)
    """

    prefix: Bytes
    """
    The compressed run of bits shared by every key below this branch,
    one bit per byte, in consumption order.
    This is  empty when the keys diverge immediately.

    Like the MPT,the run is relative: it holds only the bits between the
    parent's split point and this branch's split bit, never the path
    from the root, which is reconstructed by the walk down.
    """

    left: "BinaryNode"
    """
    Subtree of keys whose bit after [`prefix`] is `0`.

    [`prefix`]: ref:ethereum.binary_trie.trie.BranchNode.prefix
    """

    right: "BinaryNode"
    """
    Subtree of keys whose bit after [`prefix`] is `1`.

    [`prefix`]: ref:ethereum.binary_trie.trie.BranchNode.prefix
    """


BinaryNode = Union[BranchNode, LeafNode]
"""
Either of the node types making up a non-empty binary tree.
"""


@final
@dataclass
class BinaryTrie:
    """
    Mapping of variable-length keys to 32-byte values with a single
    root hash that cryptographically commits to the mapping.

    Only the key/value pairs are stored; [`root`] rebuilds the node
    structure and rehashes it from scratch on every call, which makes
    the canonical compressed form automatic rather than a rule the
    caller must maintain.

    A production client would instead keep the tree's nodes in
    memory between calls and recompute only the hashes along the
    path to a changed key; this reference implementation rebuilds
    everything each time for readability.

    [`root`]: ref:ethereum.binary_trie.trie.root
    """

    _data: Dict[Key, Bytes32] = field(default_factory=dict)


def copy_trie(trie: BinaryTrie) -> BinaryTrie:
    """
    Create a copy of `trie`.

    Keys and values are immutable, so the contents are shared between
    the original and the copy.
    """
    return BinaryTrie(copy.copy(trie._data))


def trie_set(trie: BinaryTrie, key: Key, value: Bytes32) -> None:
    """
    Insert or update `key` in `trie` with the given `value`.

    The caller must keep keys prefix-free; see [`Key`].

    [`Key`]: ref:ethereum.binary_trie.trie.Key
    """
    assert (
        len(key) >= 1
    )  # Reject the empty key since it is a prefix of every other key
    assert Uint(len(key)) <= MAX_KEY_LENGTH
    assert (
        len(value) == 32
    )  # TODO: type is Bytes32 but not sure those are enforced at runtime
    trie._data[key] = value


def trie_get(trie: BinaryTrie, key: Key) -> Optional[Bytes32]:
    """
    Look up `key` in `trie`, returning `None` if absent.
    """
    return trie._data.get(key)


def encode_bit_prefix(prefix: Bytes) -> Bytes:
    """
    Encodes a branch prefix: a two-byte big-endian bit
    count followed by the bits packed most significant bit first,
    zero padded to a byte boundary.

    The explicit bit count keeps the encoding injective. Without it, two
    prefixes differing only by trailing zero bits would pack to the
    same bytes and two different trees could share a root.

    Two bytes are enough because a prefix cannot outgrow the bit length
    of the keys sharing it, and [`trie_set`] bounds every key at
    [`MAX_KEY_LENGTH`].

    [`trie_set`]: ref:ethereum.binary_trie.trie.trie_set
    [`MAX_KEY_LENGTH`]: ref:ethereum.binary_trie.trie.MAX_KEY_LENGTH
    """
    assert len(prefix) < 2**16
    packed = bytearray((len(prefix) + 7) // 8)
    for bit_index, bit in enumerate(prefix):
        packed[bit_index // 8] |= bit << (7 - bit_index % 8)
    return Bytes(len(prefix).to_bytes(2, "big") + bytes(packed))


def merkleize(node: BinaryNode) -> Hash32:
    """
    Compute the hash committing to `node` and everything below it.
    """
    if isinstance(node, LeafNode):
        return blake3_hash(LEAF_NODE_TAG + node.key + node.value)
    return blake3_hash(
        BRANCH_NODE_TAG
        + encode_bit_prefix(node.prefix)
        + merkleize(node.left)
        + merkleize(node.right)
    )


def binarize(entries: Mapping[Key, Bytes32], depth: Uint) -> BinaryNode:
    """
    Build the canonical node structure for `entries`, whose keys all
    share their first `depth` bits. `entries` must not be empty.

    A single entry becomes a [`LeafNode`] immediately. Multiple
    entries become a [`BranchNode`] carrying the run of bits they
    share beyond `depth` and splitting on the first bit where they
    differ.

    [`LeafNode`]: ref:ethereum.binary_trie.trie.LeafNode
    [`BranchNode`]: ref:ethereum.binary_trie.trie.BranchNode
    """
    assert len(entries) > 0
    if len(entries) == 1:
        ((key, value),) = entries.items()
        return LeafNode(key, value)

    bit_lists = {key: bytes_to_bit_list(key) for key in entries}

    split = depth
    while True:
        # A key running out of bits while still grouped with others
        # would be a prefix of theirs; see `Key`.
        for bit_list in bit_lists.values():
            assert split < Uint(len(bit_list))
        distinct_bits_at_split = {
            bit_list[split] for bit_list in bit_lists.values()
        }
        if len(distinct_bits_at_split) > 1:
            break
        split += Uint(1)

    left = {
        key: value
        for key, value in entries.items()
        if bit_lists[key][split] == 0
    }
    right = {
        key: value
        for key, value in entries.items()
        if bit_lists[key][split] == 1
    }
    shared_bits = next(iter(bit_lists.values()))
    return BranchNode(
        Bytes(shared_bits[depth:split]),
        binarize(left, split + Uint(1)),
        binarize(right, split + Uint(1)),
    )


def root(trie: BinaryTrie) -> Hash32:
    """
    Compute the root hash of `trie`.

    An empty trie commits to [`EMPTY_TRIE_ROOT`]; any other trie
    commits to the hash of its canonical node structure.

    [`EMPTY_TRIE_ROOT`]: ref:ethereum.binary_trie.trie.EMPTY_TRIE_ROOT
    """
    if len(trie._data) == 0:
        return EMPTY_TRIE_ROOT
    return merkleize(binarize(trie._data, Uint(0)))
