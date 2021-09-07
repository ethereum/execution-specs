"""
State Trie
^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

The state trie is the structure responsible for storing
`eth1spec.eth_types.Account` objects.
"""

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
    TypeVar,
    Union,
    cast,
)

from ethereum.utils.hexadecimal import hex_to_bytes

from .. import crypto
from ..base_types import U256, Bytes, Uint, slotted_freezable
from . import rlp
from .eth_types import Account, Receipt, Root, Transaction

# note: an empty trie (regardless of whether it is secured) has root:
#
#   crypto.keccak256(RLP(b''))
#       ==
#   56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421 # noqa: E501,SC10
#
# also:
#
#   crypto.keccak256(RLP(()))
#       ==
#   1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347 # noqa: E501,SC10
#
# which is the sha3Uncles hash in block header with no uncles
EMPTY_TRIE_ROOT = hex_to_bytes(
    "56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
)

Node = Union[Account, Bytes, Transaction, Receipt, Uint, U256, None]
T = TypeVar(
    "T",
    Optional[Account],
    Bytes,
    Optional[Transaction],
    Optional[Receipt],
    Uint,
    U256,
)


@slotted_freezable
@dataclass
class LeafNode:
    """Leaf node in the Merkle Trie"""

    rest_of_key: Bytes
    value: Bytes


@slotted_freezable
@dataclass
class ExtensionNode:
    """Extension node in the Merkle Trie"""

    key_segment: Bytes
    subnode: rlp.RLP


@slotted_freezable
@dataclass
class BranchNode:
    """Branch node in the Merkle Trie"""

    subnodes: List[rlp.RLP]
    value: rlp.RLP


InternalNode = Union[LeafNode, ExtensionNode, BranchNode]


def encode_internal_node(node: Optional[InternalNode]) -> rlp.RLP:
    """
    Encodes a Merkle Trie node into its RLP form. The RLP will then be
    serialized into a `Bytes` and hashed unless it is less that 32 bytes
    when serialized.

    This function also accepts `None`, representing the absence of a node,
    which is encoded to `b""`.

    Parameters
    ----------
    node : Optional[InternalNode]
        The node to encode.

    Returns
    -------
    encoded : `rlp.RLP`
        The node encoded as RLP.
    """
    unencoded: rlp.RLP
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
        unencoded = node.subnodes + [node.value]
    else:
        raise Exception(f"Invalid internal node type {type(node)}!")

    encoded = rlp.encode(unencoded)
    if len(encoded) < 32:
        return unencoded
    else:
        return crypto.keccak256(encoded)


def encode_node(node: Node, storage_root: Optional[Bytes] = None) -> Bytes:
    """
    Encode a Node for storage in the Merkle Trie.

    Currently mostly an unimplemented stub.
    """
    if isinstance(node, Account):
        assert storage_root is not None
        return rlp.encode_account(node, storage_root)
    elif isinstance(node, (Transaction, Receipt, U256)):
        return rlp.encode(cast(rlp.RLP, node))
    elif isinstance(node, Bytes):
        return node
    else:
        raise NotImplementedError(
            f"encoding for {type(node)} is not currently implemented"
        )


@dataclass
class Trie(Generic[T]):
    """
    The Merkle Trie.
    """

    secured: bool
    default: T
    _data: Dict[Bytes, T] = field(default_factory=dict)


def trie_set(trie: Trie[T], key: Bytes, value: T) -> None:
    """
    Stores an item in a Merkle Trie.

    This method deletes the key if `value == trie.default`, because the Merkle
    Trie represents the default value by omitting it from the trie.

    Parameters
    ----------
    trie: `Trie`
        Trie to store in.
    key : `Bytes`
        Key to lookup.
    value : `T`
        Node to insert at `key`.
    """
    if value == trie.default:
        if key in trie._data:
            del trie._data[key]
    else:
        trie._data[key] = value


def trie_get(trie: Trie, key: Bytes) -> T:
    """
    Gets an item from the Merkle Trie.

    This method returns `trie.default` if the key is missing.

    Parameters
    ----------
    trie: `Trie`
        Trie to lookup in.
    key : `Bytes`
        Key to lookup.

    Returns
    -------
    node : `T`
        Node at `key` in the trie.
    """
    return trie._data.get(key, trie.default)


def common_prefix_length(a: Sequence, b: Sequence) -> int:
    """
    Find the longest common prefix of two sequences.
    """
    for i in range(len(a)):
        if i >= len(b) or a[i] != b[i]:
            return i
    return len(a)


def nibble_list_to_compact(x: Bytes, is_leaf: bool) -> bytearray:
    """
    Compresses nibble-list into a standard byte array with a flag.

    A nibble-list is a list of byte values no greater than `15`. The flag is
    encoded in high nibble of the highest byte. The flag nibble can be broken
    down into two two-bit flags.

    Highest nibble::

        +---+---+----------+--------+
        | _ | _ | is_leaf | parity |
        +---+---+----------+--------+
          3   2      1         0


    The lowest bit of the nibble encodes the parity of the length of the
    remaining nibbles -- `0` when even and `1` when odd. The second lowest bit
    is used to distinguish leaf and extension nodes. The other two bits are not
    used.

    Parameters
    ----------
    x :
        Array of nibbles.
    is_leaf :
        True if this is part of a leaf node, or false if it is an extension
        node.

    Returns
    -------
    compressed : `bytearray`
        Compact byte array.
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

    return compact


def bytes_to_nibble_list(bytes: Bytes) -> Bytes:
    """
    Converts a `Bytes` into to a sequence of nibbles (bytes with value < 16).

    Parameters
    ----------
    bytes: `Bytes`
        The `Bytes` to convert.

    Returns
    -------
    nibble_list : `Bytes`
        The `Bytes` in nibble-list format.
    """
    nibble_list = bytearray(2 * len(bytes))
    for byte_index, byte in enumerate(bytes):
        nibble_list[byte_index * 2] = (byte & 0xF0) >> 4
        nibble_list[byte_index * 2 + 1] = byte & 0x0F
    return Bytes(nibble_list)


def _prepare_trie(
    trie: Trie,
    get_storage_root: Callable[[Bytes], Bytes] = None,
) -> Mapping[Bytes, Bytes]:
    """
    Prepares the trie for root calculation. Removes values that are empty,
    hashes the keys (if `secured == True`) and encodes all the nodes.

    Parameters
    ----------
    trie : `Trie`
        The `Trie` to prepare.
    get_storage_root : `Callable[[Bytes], Bytes]`
        Function to get the storage root of an account. Needed to encode
        `Account` objects.

    Returns
    -------
    out : `Mapping[eth1spec.base_types.Bytes, Node]`
        Object with keys mapped to nibble-byte form.
    """
    mapped: MutableMapping[Bytes, Bytes] = {}

    for (preimage, value) in trie._data.items():
        if isinstance(value, Account):
            assert get_storage_root is not None
            encoded_value = encode_node(value, get_storage_root(preimage))
        else:
            encoded_value = encode_node(value)
        # Empty values are represented by their absence
        assert encoded_value != b""
        # "secure" tries hash keys once before construction
        key = crypto.keccak256(preimage) if trie.secured else preimage
        mapped[bytes_to_nibble_list(key)] = encoded_value

    return mapped


def root(
    trie: Trie,
    get_storage_root: Callable[[Bytes], Bytes] = None,
) -> Root:
    """
    Computes the root of a modified merkle patricia trie (MPT).

    Parameters
    ----------
    trie : `Trie`
        `Trie` to get the root of.
    get_storage_root : `Callable[[Bytes], Bytes]`
        Function to get the storage root of an account. Needed to encode
        `Account` objects.


    Returns
    -------
    root : `eth1spec.eth_types.Root`
        MPT root of the underlying key-value pairs.
    """
    obj = _prepare_trie(trie, get_storage_root)

    root_node = encode_internal_node(patricialize(obj, Uint(0)))
    if len(rlp.encode(root_node)) < 32:
        return crypto.keccak256(rlp.encode(root_node))
    else:
        assert isinstance(root_node, Bytes)
        return root_node


def patricialize(
    obj: Mapping[Bytes, Bytes], level: Uint
) -> Optional[InternalNode]:
    """
    Structural composition function.

    Used to recursively patricialize and merkleize a dictionary. Includes
    memoization of the tree structure and hashes.

    Parameters
    ----------
    obj :
        Underlying trie key-value pairs, with keys in nibble-list format.
    level :
        Current trie level.

    Returns
    -------
    node : `eth1spec.base_types.Bytes`
        Root node of `obj`.
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
        prefix = arbitrary_key[level : level + prefix_length]
        return ExtensionNode(
            prefix,
            encode_internal_node(patricialize(obj, level + prefix_length)),
        )

    branches: List[MutableMapping[Bytes, Bytes]] = []
    for _ in range(16):
        branches.append({})
    value = b""
    for key in obj:
        if len(key) == level:
            # shouldn't ever have an account or receipt in an internal node
            if isinstance(obj[key], (Account, Receipt, Uint)):
                raise TypeError()
            value = obj[key]
        else:
            branches[key[level]][key] = obj[key]

    return BranchNode(
        [
            encode_internal_node(patricialize(branches[k], level + 1))
            for k in range(16)
        ],
        value,
    )
