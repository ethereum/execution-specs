"""
Modified Merkle Patricia Trie (MPT), the data structure that commits to
large amounts of state with a single hash.

The MPT is a 16-ary radix trie augmented with cryptographic hashing, so each
unique mapping of keys to values has a deterministic root hash. Block headers
commit to the state, transactions, and receipts through these roots, allowing
nodes to verify any individual entry against the header without storing the
entire trie.

The trie has three kinds of internal node:

- A [`LeafNode`] terminates a path and stores a value.
- An [`ExtensionNode`] compresses a sequence of nibbles shared by every key
  passing through it, avoiding chains of single-child branches.
- A [`BranchNode`] has up to sixteen children, one per nibble value, plus an
  optional value for a key that terminates exactly at this node.

Keys are processed as **nibbles** (half-bytes, each `0` to `15` inclusive)
by [`bytes_to_nibble_list`][bnl], and stored within nodes in a compressed
[hex-prefix encoding][hp] produced by [`nibble_list_to_compact`][nlc].

Some tries are _secured_, meaning their keys are hashed with [`keccak256`]
before insertion. Hashing distributes keys uniformly so adversarial choices
cannot create a deeply unbalanced trie. The state and storage tries are
secured; the transaction and receipt tries are not.

The mapping of keys to values is exposed through [`Trie`]; the [`root`]
function reduces a trie to its 32-byte commitment.

[`LeafNode`]: ref:ethereum.merkle_patricia_trie.LeafNode
[`ExtensionNode`]: ref:ethereum.merkle_patricia_trie.ExtensionNode
[`BranchNode`]: ref:ethereum.merkle_patricia_trie.BranchNode
[`Trie`]: ref:ethereum.merkle_patricia_trie.Trie
[`root`]: ref:ethereum.merkle_patricia_trie.root
[bnl]: ref:ethereum.merkle_patricia_trie.bytes_to_nibble_list
[nlc]: ref:ethereum.merkle_patricia_trie.nibble_list_to_compact
[`keccak256`]: ref:ethereum.crypto.hash.keccak256
[hp]: https://ethereum.org/en/developers/docs/data-structures-and-encoding/patricia-merkle-trie/#optimization
"""  # noqa: E501

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import (
    Callable,
    Dict,
    Generic,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    cast,
    final,
)

from ethereum_rlp import Extended, rlp
from ethereum_types.bytes import Bytes
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import Uint
from typing_extensions import assert_type

from ethereum.crypto.hash import keccak256
from ethereum.state import Account, Address, Root
from ethereum.utils.hexadecimal import hex_to_bytes

EMPTY_TRIE_ROOT = Root(
    hex_to_bytes(
        "56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
    )
)
"""
Root hash of an empty Merkle Patricia Trie.

Used in block headers (state, transactions, receipts, etc.) when the
corresponding trie has no entries. This is the [`keccak256`] hash of the RLP
encoding of an empty byte string, regardless of whether the trie would have
been secured.

[`keccak256`]: ref:ethereum.crypto.hash.keccak256
"""


@final
@slotted_freezable
@dataclass
class LeafNode:
    """
    Terminal node in the trie, holding a value at the end of a key path.
    """

    rest_of_key: Bytes
    """
    Nibbles of the key not yet consumed by ancestor nodes.
    """

    value: Extended
    """
    Value stored at this key, in its encoded form.
    """


@final
@slotted_freezable
@dataclass
class ExtensionNode:
    """
    Internal node that compresses a run of nibbles shared by every key
    passing through it.

    Without this optimization, deep tries of similar keys would otherwise
    require long chains of single-child [`BranchNode`]s.

    [`BranchNode`]: ref:ethereum.merkle_patricia_trie.BranchNode
    """

    key_segment: Bytes
    """
    Sequence of nibbles shared by all keys descending through this node.
    """

    subnode: Extended
    """
    Encoded child node reached after consuming [`key_segment`][ks].

    [ks]: ref:ethereum.merkle_patricia_trie.ExtensionNode.key_segment
    """


BranchSubnodes = Tuple[
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
    Extended,
]
"""
Children of a [`BranchNode`], one per nibble value (`0` to `15` inclusive).

Each entry is the encoded form of another internal node, or `b""` if no key
descends through that nibble.

[`BranchNode`]: ref:ethereum.merkle_patricia_trie.BranchNode
"""


@final
@slotted_freezable
@dataclass
class BranchNode:
    """
    Internal node with up to sixteen children, one per nibble value, plus an
    optional value for a key that terminates exactly at this node.
    """

    subnodes: BranchSubnodes
    """
    Encoded children, indexed by the next nibble of the key.
    """

    value: Extended
    """
    Value for a key that terminates at this node, or `b""` if no such key
    exists.
    """


InternalNode = LeafNode | ExtensionNode | BranchNode
"""
Any of the three node types making up a Merkle Patricia Trie.
"""


K = TypeVar("K", bound=Bytes)
V = TypeVar("V", bound=Extended | None)


def encode_account(raw_account_data: Account, storage_root: Bytes) -> Bytes:
    """
    Encode an [`Account`] for inclusion in the state trie.

    The [`Account`] dataclass holds nonce, balance, and code hash, but not
    the account's storage. The corresponding `storage_root` (the root of the
    account's own storage trie) is therefore passed in separately.

    [`Account`]: ref:ethereum.state.Account
    """
    return rlp.encode(
        (
            raw_account_data.nonce,
            raw_account_data.balance,
            storage_root,
            raw_account_data.code_hash,
        )
    )


def encode_internal_node(node: Optional[InternalNode]) -> Extended:
    """
    Encode an [`InternalNode`] into its RLP form.

    When the resulting serialization is at least 32 bytes, [`keccak256`] is
    applied so that parents store a fixed-size hash. Shorter encodings are
    returned unhashed and embedded directly into the parent, since storing a
    hash would only waste space.

    `None` represents the absence of a node and is encoded as `b""`.

    [`InternalNode`]: ref:ethereum.merkle_patricia_trie.InternalNode
    [`keccak256`]: ref:ethereum.crypto.hash.keccak256
    """
    unencoded: Extended
    if node is None:
        unencoded = b""
    elif isinstance(node, LeafNode):
        unencoded = (
            nibble_list_to_compact(node.rest_of_key, True),
            node.value,
        )
    elif isinstance(node, ExtensionNode):
        unencoded = (
            nibble_list_to_compact(node.key_segment, False),
            node.subnode,
        )
    elif isinstance(node, BranchNode):
        unencoded = list(node.subnodes) + [node.value]
    else:
        raise AssertionError(f"Invalid internal node type {type(node)}!")

    encoded = rlp.encode(unencoded)
    if len(encoded) < 32:
        return unencoded
    else:
        return keccak256(encoded)


def encode_node(node: Extended, storage_root: Bytes | None = None) -> Bytes:
    """
    Encode a value for storage in the trie.

    [`Account`] values require a `storage_root` and are encoded with
    [`encode_account`]; raw `Bytes` are returned unchanged; everything else
    is RLP-encoded.

    [`Account`]: ref:ethereum.state.Account
    [`encode_account`]: ref:ethereum.merkle_patricia_trie.encode_account
    """
    if isinstance(node, Account):
        assert storage_root is not None
        return encode_account(node, storage_root)
    elif isinstance(node, Bytes):
        return node
    else:
        return rlp.encode(node)


@final
@dataclass
class Trie(Generic[K, V]):
    """
    Key-value mapping with a single root hash that uniquely identifies its
    contents.

    A trie may be _secured_, meaning keys are hashed with [`keccak256`]
    before insertion to prevent adversarial keys from producing a deeply
    unbalanced trie. The state and storage tries are secured; the transaction
    and receipt tries are not.

    A trie has a [`default`] value representing key absence: storing
    [`default`] at a key is equivalent to omitting the key, since the
    underlying MPT represents missing keys by leaving them out entirely.

    [`keccak256`]: ref:ethereum.crypto.hash.keccak256
    [`default`]: ref:ethereum.merkle_patricia_trie.Trie.default
    """

    secured: bool
    """
    When `True`, keys are hashed with [`keccak256`] before being inserted
    into the underlying MPT.

    [`keccak256`]: ref:ethereum.crypto.hash.keccak256
    """

    default: V
    """
    Value treated as key absence — storing this value through [`trie_set`]
    removes the key, and [`trie_get`] returns it for missing keys.

    [`trie_set`]: ref:ethereum.merkle_patricia_trie.trie_set
    [`trie_get`]: ref:ethereum.merkle_patricia_trie.trie_get
    """

    # Held in a plain Python dictionary; the MPT structure is built only when
    # `root` is called. This trades performance for clarity, since storing
    # intermediate nodes is not needed for the spec's outputs.
    _data: Dict[K, V] = field(default_factory=dict)


def copy_trie(trie: Trie[K, V]) -> Trie[K, V]:
    """
    Create a copy of `trie`.

    Since only frozen objects may be stored in a trie, the contents are
    shared between the original and the copy.
    """
    return Trie(trie.secured, trie.default, copy.copy(trie._data))


def trie_set(trie: Trie[K, V], key: K, value: V) -> None:
    """
    Insert or update `key` in `trie` with the given `value`.

    Storing the trie's [`default`] value deletes the key, since a trie
    represents `default` by omitting the key entirely.

    [`default`]: ref:ethereum.merkle_patricia_trie.Trie.default
    """
    if value == trie.default:
        if key in trie._data:
            del trie._data[key]
    else:
        trie._data[key] = value


def trie_get(trie: Trie[K, V], key: K) -> V:
    """
    Look up `key` in `trie`, returning the trie's [`default`] value if absent.

    [`default`]: ref:ethereum.merkle_patricia_trie.Trie.default
    """
    return trie._data.get(key, trie.default)


def common_prefix_length(a: Sequence, b: Sequence) -> int:
    """
    Find the length of the longest common prefix of two sequences.
    """
    for i in range(len(a)):
        if i >= len(b) or a[i] != b[i]:
            return i
    return len(a)


def nibble_list_to_compact(x: Bytes, is_leaf: bool) -> Bytes:
    """
    Compress a list of nibbles into bytes using hex-prefix encoding.

    Nibbles are packed two-per-byte, preceded by a single flag nibble at the
    high position of the first byte:

    ```
    +---+---+---------+--------+
    | _ | _ | is_leaf | parity |
    +---+---+---------+--------+
      3   2      1        0
    ```

    The lowest bit of the flag nibble encodes the parity of the nibble-list
    length (`0` for even, `1` for odd). The next bit distinguishes leaf nodes
    from extension nodes. The two highest bits are unused.

    When the length is odd the first nibble of `x` is packed into the same
    byte as the flag, leaving an even number of remaining nibbles to pair off.
    """
    compact = bytearray()

    if len(x) % 2 == 0:  # ie even length
        compact.append(16 * (2 * is_leaf))
        for i in range(0, len(x), 2):
            compact.append(16 * x[i] + x[i + 1])
    else:
        compact.append(16 * ((2 * is_leaf) + 1) + x[0])
        for i in range(1, len(x), 2):
            compact.append(16 * x[i] + x[i + 1])

    return Bytes(compact)


def bytes_to_nibble_list(bytes_: Bytes) -> Bytes:
    """
    Split each input byte into its high and low nibble, producing a sequence
    of bytes each holding a value from `0` to `15` inclusive.
    """
    nibble_list = bytearray(2 * len(bytes_))
    for byte_index, byte in enumerate(bytes_):
        nibble_list[byte_index * 2] = (byte & 0xF0) >> 4
        nibble_list[byte_index * 2 + 1] = byte & 0x0F
    return Bytes(nibble_list)


def _prepare_data(
    data: Mapping[K, V],
    secured: bool,
    get_storage_root: Optional[Callable[[Address], Root]] = None,
) -> Mapping[Bytes, Bytes]:
    """
    Convert trie data into the nibble-keyed mapping consumed by
    [`patricialize`].

    Each value is encoded with [`encode_node`]; if the value is an
    [`Account`], `get_storage_root` must be supplied to provide its storage
    root. Keys are hashed with [`keccak256`] when the trie is secured, then
    expanded into nibble form via [`bytes_to_nibble_list`][bnl].

    [`patricialize`]: ref:ethereum.merkle_patricia_trie.patricialize
    [`encode_node`]: ref:ethereum.merkle_patricia_trie.encode_node
    [`Account`]: ref:ethereum.state.Account
    [bnl]: ref:ethereum.merkle_patricia_trie.bytes_to_nibble_list
    [`keccak256`]: ref:ethereum.crypto.hash.keccak256
    """
    mapped: MutableMapping[Bytes, Bytes] = {}

    for preimage, value in data.items():
        if isinstance(value, Account):
            assert get_storage_root is not None
            address = Address(preimage)
            encoded_value = encode_node(value, get_storage_root(address))
        elif value is None:
            raise AssertionError("cannot encode `None`")
        else:
            encoded_value = encode_node(value)
        if encoded_value == b"":
            raise AssertionError
        key: Bytes
        if secured:
            # "secure" tries hash keys once before construction
            key = keccak256(preimage)
        else:
            key = preimage
        mapped[bytes_to_nibble_list(key)] = encoded_value

    return mapped


def _prepare_trie(
    trie: Trie[K, V],
    get_storage_root: Optional[Callable[[Address], Root]] = None,
) -> Mapping[Bytes, Bytes]:
    """
    Prepare the trie for root calculation.

    Remove values that are empty, hash the keys (if
    ``secured == True``) and encode all the nodes.

    Parameters
    ----------
    trie :
        The ``Trie`` to prepare.
    get_storage_root :
        Function to get the storage root of an account. Needed
        to encode ``Account`` objects.

    Returns
    -------
    out : `Mapping[ethereum.base_types.Bytes, Node]`
        Object with keys mapped to nibble-byte form.

    """
    return _prepare_data(trie._data, trie.secured, get_storage_root)


def root(
    trie: Trie[K, V],
    get_storage_root: Optional[Callable[[Address], Root]] = None,
) -> Root:
    """
    Compute the root hash of `trie`.

    The trie is patricialized into a tree of [`InternalNode`]s; the root node
    is RLP-encoded and hashed with [`keccak256`] to produce the fixed-size
    [`Hash32`] used in block headers.

    `get_storage_root` is required when encoding [`Account`] values, so it
    must be supplied when computing the state root.

    [`InternalNode`]: ref:ethereum.merkle_patricia_trie.InternalNode
    [`keccak256`]: ref:ethereum.crypto.hash.keccak256
    [`Hash32`]: ref:ethereum.crypto.hash.Hash32
    [`Account`]: ref:ethereum.state.Account
    """
    obj = _prepare_trie(trie, get_storage_root)

    root_node = encode_internal_node(patricialize(obj, Uint(0)))
    if len(rlp.encode(root_node)) < 32:
        return keccak256(rlp.encode(root_node))
    else:
        assert isinstance(root_node, Bytes)
        return Root(root_node)


def patricialize(
    obj: Mapping[Bytes, Bytes], level: Uint
) -> Optional[InternalNode]:
    """
    Recursively build the trie for `obj`, starting `level` nibbles into the
    keys.

    The structure of the returned subtree is determined by inspecting the
    keys present at the current `level`:

    1. With no keys, the subtree is empty and `None` is returned.
    1. With a single key, a [`LeafNode`] holds the remaining nibbles and the
       value.
    1. When every key shares a non-empty prefix at this level, an
       [`ExtensionNode`] consumes the prefix and the algorithm recurses for
       the rest.
    1. Otherwise the keys are partitioned by their next nibble into up to
       sixteen groups, each recursively patricialized, and combined into a
       [`BranchNode`].

    [`LeafNode`]: ref:ethereum.merkle_patricia_trie.LeafNode
    [`ExtensionNode`]: ref:ethereum.merkle_patricia_trie.ExtensionNode
    [`BranchNode`]: ref:ethereum.merkle_patricia_trie.BranchNode
    """
    if len(obj) == 0:
        return None

    arbitrary_key = next(iter(obj))

    # if leaf node
    if len(obj) == 1:
        leaf = LeafNode(arbitrary_key[level:], obj[arbitrary_key])
        return leaf

    # prepare for extension node check by finding max j such that all keys in
    # obj have the same key[i:j]
    substring = arbitrary_key[level:]
    prefix_length = len(substring)
    for key in obj:
        prefix_length = min(
            prefix_length, common_prefix_length(substring, key[level:])
        )

        # finished searching, found another key at the current level
        if prefix_length == 0:
            break

    # if extension node
    if prefix_length > 0:
        prefix = arbitrary_key[int(level) : int(level) + prefix_length]
        return ExtensionNode(
            prefix,
            encode_internal_node(
                patricialize(obj, level + Uint(prefix_length))
            ),
        )

    branches: List[MutableMapping[Bytes, Bytes]] = []
    for _ in range(16):
        branches.append({})
    value = b""
    for key in obj:
        if len(key) == level:
            value = obj[key]
        else:
            branches[key[level]][key] = obj[key]

    subnodes = tuple(
        encode_internal_node(patricialize(branches[k], level + Uint(1)))
        for k in range(16)
    )
    return BranchNode(
        cast(BranchSubnodes, assert_type(subnodes, Tuple[Extended, ...])),
        value,
    )
