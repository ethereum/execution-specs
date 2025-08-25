"""The state trie is the structure responsible for storing."""

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
)

from Crypto.Hash import keccak
from ethereum_rlp import Extended, rlp
from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U256, Uint
from typing_extensions import assert_type


@slotted_freezable
@dataclass
class FrontierAccount:
    """State associated with an address."""

    nonce: Uint
    balance: U256
    code: Bytes


def keccak256(buffer: Bytes) -> Bytes32:
    """Compute the keccak256 hash of the input `buffer`."""
    k = keccak.new(digest_bits=256)
    return Bytes32(k.update(buffer).digest())


def encode_account(raw_account_data: FrontierAccount, storage_root: Bytes) -> Bytes:
    """
    Encode `Account` dataclass.

    Storage is not stored in the `Account` dataclass, so `Accounts` cannot be
    encoded without providing a storage root.
    """
    return rlp.encode(
        (
            raw_account_data.nonce,
            raw_account_data.balance,
            storage_root,
            keccak256(raw_account_data.code),
        )
    )


# note: an empty trie (regardless of whether it is secured) has root:
#
#   keccak256(RLP(b''))
#       ==
#   56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421 # noqa: E501,SC10
#
# also:
#
#   keccak256(RLP(()))
#       ==
#   1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347 # noqa: E501,SC10
#
# which is the sha3Uncles hash in block header with no uncles
EMPTY_TRIE_ROOT = Bytes32(
    bytes.fromhex("56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421")
)

Node = FrontierAccount | Bytes | Uint | U256 | None
K = TypeVar("K", bound=Bytes)
V = TypeVar(
    "V",
    Optional[FrontierAccount],
    Bytes,
    Uint,
    U256,
)


@slotted_freezable
@dataclass
class LeafNode:
    """Leaf node in the Merkle Trie."""

    rest_of_key: Bytes
    value: Extended


@slotted_freezable
@dataclass
class ExtensionNode:
    """Extension node in the Merkle Trie."""

    key_segment: Bytes
    subnode: Extended


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


@slotted_freezable
@dataclass
class BranchNode:
    """Branch node in the Merkle Trie."""

    subnodes: BranchSubnodes
    value: Extended


InternalNode = LeafNode | ExtensionNode | BranchNode


def encode_internal_node(node: Optional[InternalNode]) -> Extended:
    """
    Encode a Merkle Trie node into its RLP form. The RLP will then be
    serialized into a `Bytes` and hashed unless it is less that 32 bytes
    when serialized.

    This function also accepts `None`, representing the absence of a node,
    which is encoded to `b""`.
    """
    unencoded: Extended
    match node:
        case None:
            unencoded = b""
        case LeafNode():
            unencoded = (
                nibble_list_to_compact(node.rest_of_key, True),
                node.value,
            )
        case ExtensionNode():
            unencoded = (
                nibble_list_to_compact(node.key_segment, False),
                node.subnode,
            )
        case BranchNode():
            unencoded = list(node.subnodes) + [node.value]
        case _:
            raise AssertionError(f"Invalid internal node type {type(node)}!")

    encoded = rlp.encode(unencoded)
    if len(encoded) < 32:
        return unencoded
    else:
        return keccak256(encoded)


def encode_node(node: Node, storage_root: Optional[Bytes] = None) -> Bytes:
    """
    Encode a Node for storage in the Merkle Trie.

    Currently mostly an unimplemented stub.
    """
    match node:
        case FrontierAccount():
            assert storage_root is not None
            return encode_account(node, storage_root)
        case U256():
            return rlp.encode(node)
        case Bytes():
            return node
        case _:
            raise AssertionError(f"encoding for {type(node)} is not currently implemented")


@dataclass(slots=True)
class Trie(Generic[K, V]):
    """The Merkle Trie."""

    secured: bool
    default: V
    _data: Dict[K, V] = field(default_factory=dict)


def copy_trie(trie: Trie[K, V]) -> Trie[K, V]:
    """
    Create a copy of `trie`. Since only frozen objects may be stored in tries,
    the contents are reused.
    """
    return Trie(trie.secured, trie.default, copy.copy(trie._data))


def trie_set(trie: Trie[K, V], key: K, value: V) -> None:
    """
    Store an item in a Merkle Trie.

    This method deletes the key if `value == trie.default`, because the Merkle
    Trie represents the default value by omitting it from the trie.

    """
    if value == trie.default:
        if key in trie._data:
            del trie._data[key]
    else:
        trie._data[key] = value


def trie_get(trie: Trie[K, V], key: K) -> V:
    """
    Get an item from the Merkle Trie.

    This method returns `trie.default` if the key is missing.

    """
    return trie._data.get(key, trie.default)


def common_prefix_length(a: Sequence, b: Sequence) -> int:
    """Find the longest common prefix of two sequences."""
    for i in range(len(a)):
        if i >= len(b) or a[i] != b[i]:
            return i
    return len(a)


def nibble_list_to_compact(x: Bytes, is_leaf: bool) -> Bytes:
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
    """Convert a `Bytes` into to a sequence of nibbles (bytes with value < 16)."""
    nibble_list = bytearray(2 * len(bytes_))
    for byte_index, byte in enumerate(bytes_):
        nibble_list[byte_index * 2] = (byte & 0xF0) >> 4
        nibble_list[byte_index * 2 + 1] = byte & 0x0F
    return Bytes(nibble_list)


def _prepare_trie(
    trie: Trie[K, V],
    get_storage_root: Optional[Callable[[Bytes20], Bytes32]] = None,
) -> Mapping[Bytes, Bytes]:
    """
    Prepare the trie for root calculation. Removes values that are empty,
    hashes the keys (if `secured == True`) and encodes all the nodes.
    """
    mapped: MutableMapping[Bytes, Bytes] = {}

    for preimage, value in trie._data.items():
        if isinstance(value, FrontierAccount):
            assert get_storage_root is not None
            address = Bytes20(preimage)
            encoded_value = encode_node(value, get_storage_root(address))
        else:
            encoded_value = encode_node(value)
        if encoded_value == b"":
            raise AssertionError
        key: Bytes
        if trie.secured:
            # "secure" tries hash keys once before construction
            key = keccak256(preimage)
        else:
            key = preimage
        mapped[bytes_to_nibble_list(key)] = encoded_value

    return mapped


def root(
    trie: Trie[K, V],
    get_storage_root: Optional[Callable[[Bytes20], Bytes32]] = None,
) -> Bytes32:
    """Compute the root of a modified merkle patricia trie (MPT)."""
    obj = _prepare_trie(trie, get_storage_root)

    root_node = encode_internal_node(patricialize(obj, Uint(0)))
    if len(rlp.encode(root_node)) < 32:
        return keccak256(rlp.encode(root_node))
    else:
        assert isinstance(root_node, Bytes)
        return Bytes32(root_node)


def patricialize(obj: Mapping[Bytes, Bytes], level: Uint) -> Optional[InternalNode]:
    """
    Structural composition function.

    Used to recursively patricialize and merkleize a dictionary. Includes
    memoization of the tree structure and hashes.
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
        prefix_length = min(prefix_length, common_prefix_length(substring, key[level:]))

        # finished searching, found another key at the current level
        if prefix_length == 0:
            break

    # if extension node
    if prefix_length > 0:
        prefix = arbitrary_key[int(level) : int(level) + prefix_length]
        return ExtensionNode(
            prefix,
            encode_internal_node(patricialize(obj, level + Uint(prefix_length))),
        )

    branches: List[MutableMapping[Bytes, Bytes]] = []
    for _ in range(16):
        branches.append({})
    value = b""
    for key in obj:
        if len(key) == level:
            # shouldn't ever have an account or receipt in an internal node
            if isinstance(obj[key], (FrontierAccount, Uint)):
                raise AssertionError
            value = obj[key]
        else:
            branches[key[level]][key] = obj[key]

    subnodes = tuple(
        encode_internal_node(patricialize(branches[k], level + Uint(1))) for k in range(16)
    )
    return BranchNode(
        cast(BranchSubnodes, assert_type(subnodes, Tuple[Extended, ...])),
        value,
    )
