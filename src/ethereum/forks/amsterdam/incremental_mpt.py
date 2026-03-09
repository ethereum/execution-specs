"""
Incremental Merkle Patricia Trie.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Provide an MPT that supports incremental updates and witness tracking.
The tree structure is rebuilt along modified paths rather than rebuilt
from scratch on each root calculation.
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
    Tuple,
    Union,
)

from ethereum_rlp import Extended, rlp
from ethereum_types.bytes import Bytes
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import Uint

from ethereum.crypto.hash import keccak256
from ethereum.state import Account, Address, Root

from .trie import (
    EMPTY_TRIE_ROOT,
    K,
    V,
    _prepare_data,
    bytes_to_nibble_list,
    common_prefix_length,
    encode_node,
    nibble_list_to_compact,
)


@slotted_freezable
@dataclass
class LeafNode:
    """Leaf node in the Merkle Trie."""

    rest_of_key: Bytes
    value: Bytes
    _dirty: bool


@slotted_freezable
@dataclass
class ExtensionNode:
    """Extension node in the Merkle Trie."""

    key_segment: Bytes
    child: "Node"
    _dirty: bool


@slotted_freezable
@dataclass
class BranchNode:
    """Branch node in the Merkle Trie."""

    children: Tuple[Optional["Node"], ...]
    value: Bytes
    _dirty: bool


@slotted_freezable
@dataclass
class HashedNode:
    """Placeholder for a trie subtree known only by its hash."""

    _hash: Bytes


Node = Union[
    LeafNode,
    ExtensionNode,
    BranchNode,
    HashedNode,
    None,
]


@dataclass
class Witness:
    """Track nodes accessed during trie operations for witness generation."""

    accessed_nodes: Dict[Bytes, Bytes] = field(default_factory=dict)


@dataclass
class IncrementalMPT(Generic[K, V]):
    """
    An MPT that supports incremental updates and witness tracking.

    Maintain an actual tree structure that can be updated along
    modified paths, rather than rebuilding the entire tree on each
    root calculation.
    """

    secured: bool
    default: V
    root_node: Node = None
    witness: Witness = field(default_factory=Witness)
    _data: Dict[K, V] = field(default_factory=dict)


def _build_tree(obj: Mapping[Bytes, Bytes], level: Uint) -> Node:
    """
    Build a tree structure from a prepared key-value mapping.

    Similar to ``patricialize()`` but build nodes for
    path-based updates.

    Parameters
    ----------
    obj :
        Underlying trie key-value pairs, with keys in
        nibble-list format.
    level :
        Current trie level.

    Returns
    -------
    node : `Node`
        Root node of the tree.

    """
    if len(obj) == 0:
        return None

    arbitrary_key = next(iter(obj))

    if len(obj) == 1:
        return LeafNode(
            rest_of_key=arbitrary_key[level:],
            value=obj[arbitrary_key],
            _dirty=False,
        )

    substring = arbitrary_key[level:]
    prefix_length = len(substring)
    for key in obj:
        prefix_length = min(
            prefix_length,
            common_prefix_length(substring, key[level:]),
        )
        if prefix_length == 0:
            break

    if prefix_length > 0:
        prefix = arbitrary_key[int(level) : int(level) + prefix_length]
        child = _build_tree(obj, level + Uint(prefix_length))
        return ExtensionNode(key_segment=prefix, child=child, _dirty=False)

    branches: List[MutableMapping[Bytes, Bytes]] = [{} for _ in range(16)]
    value = b""

    for key in obj:
        if len(key) == level:
            value = obj[key]
        else:
            branches[key[level]][key] = obj[key]

    children = tuple(
        _build_tree(branches[k], level + Uint(1)) for k in range(16)
    )

    return BranchNode(children=children, value=value, _dirty=False)


def build_mpt(
    data: Mapping[K, V],
    secured: bool,
    default: V,
    get_storage_root: Optional[Callable[[Address], Root]] = None,
) -> IncrementalMPT[K, V]:
    """
    Build an IncrementalMPT from key-value data.

    Call with the pre-execution state to create a tree structure
    that can be updated along modified paths during execution.

    Parameters
    ----------
    data :
        The source key-value data to build from.
    secured :
        Whether to hash keys before insertion.
    default :
        Default value for missing keys.
    get_storage_root :
        Function to get the storage root of an account.

    Returns
    -------
    mpt : `IncrementalMPT[K, V]`
        An incremental MPT with the same data.

    """
    prepared = _prepare_data(data, secured, get_storage_root)
    root_node = _build_tree(prepared, Uint(0))

    return IncrementalMPT(
        secured=secured,
        default=default,
        root_node=root_node,
        _data=dict(data),
    )


def _record_witness(
    witness: Witness,
    node: Node,
) -> None:
    """Record a node access in the witness."""
    assert not isinstance(node, HashedNode), "HashedNode cannot be witnessed"
    if node is None:
        return

    if node._dirty:
        return

    unencoded = _encode_node(node)
    encoded = rlp.encode(unencoded)
    if len(encoded) >= 32:
        node_hash = keccak256(encoded)
        if node_hash not in witness.accessed_nodes:
            witness.accessed_nodes[node_hash] = encoded


def _encode_node(node: Node) -> Extended:
    """
    Encode a node to its RLP form.

    Similar to ``encode_internal_node``.
    """
    if node is None:
        return b""
    elif isinstance(node, HashedNode):
        raise AssertionError("HashedNode cannot be inline-encoded")
    elif isinstance(node, LeafNode):
        return (
            nibble_list_to_compact(node.rest_of_key, True),
            node.value,
        )
    elif isinstance(node, ExtensionNode):
        child_encoded = _encode_node_to_extended(node.child)
        return (
            nibble_list_to_compact(node.key_segment, False),
            child_encoded,
        )
    elif isinstance(node, BranchNode):
        children_encoded = [
            _encode_node_to_extended(child) for child in node.children
        ]
        return children_encoded + [node.value]
    else:
        raise AssertionError(f"Invalid node type {type(node)}!")


def _encode_node_to_extended(
    node: Node,
) -> Extended:
    """
    Encode a node for embedding in parent.

    Return the hash if RLP >= 32 bytes, otherwise return
    unencoded form.
    """
    if node is None:
        return b""

    if isinstance(node, HashedNode):
        return node._hash

    unencoded = _encode_node(node)
    encoded = rlp.encode(unencoded)

    if len(encoded) < 32:
        return unencoded
    else:
        return keccak256(encoded)


def mpt_get(mpt: IncrementalMPT[K, V], key: K) -> V:
    """
    Get a value from the incremental MPT.

    Traverse the tree and record accessed nodes in the witness
    for execution witness generation.

    Parameters
    ----------
    mpt :
        The incremental MPT to get from.
    key :
        Key to lookup.

    Returns
    -------
    value : `V`
        Value at the key, or the default value if not found.

    """
    value = mpt._data.get(key, mpt.default)

    if mpt.secured:
        nibble_key = bytes_to_nibble_list(keccak256(key))
    else:
        nibble_key = bytes_to_nibble_list(key)

    _mpt_traverse_for_witness(mpt, mpt.root_node, nibble_key, Uint(0))

    return value


def _mpt_traverse_for_witness(
    mpt: IncrementalMPT,
    node: Node,
    key: Bytes,
    level: Uint,
) -> None:
    """Traverse the tree recording nodes in the witness."""
    if node is None:
        return

    _record_witness(mpt.witness, node)

    if isinstance(node, LeafNode):
        pass
    elif isinstance(node, ExtensionNode):
        segment_len = len(node.key_segment)
        lvl = int(level)
        if key[lvl : lvl + segment_len] == node.key_segment:
            _mpt_traverse_for_witness(
                mpt,
                node.child,
                key,
                Uint(lvl + segment_len),
            )
    elif isinstance(node, BranchNode):
        lvl = int(level)
        if lvl < len(key):
            child_idx = key[lvl]
            _mpt_traverse_for_witness(
                mpt,
                node.children[child_idx],
                key,
                Uint(lvl + 1),
            )


def mpt_set(
    mpt: IncrementalMPT[K, V],
    key: K,
    value: V,
    get_storage_root: Optional[Callable[[Address], Root]] = None,
) -> None:
    """
    Set a value in the incremental MPT.

    Update the tree along the modified path.

    Parameters
    ----------
    mpt :
        The incremental MPT to update.
    key :
        Key to set.
    value :
        Value to set at the key.
    get_storage_root :
        Function to get storage root (for Account values).

    """
    if value == mpt.default:
        if key in mpt._data:
            del mpt._data[key]
    else:
        mpt._data[key] = value

    if mpt.secured:
        nibble_key = bytes_to_nibble_list(keccak256(key))
    else:
        nibble_key = bytes_to_nibble_list(key)

    if value == mpt.default:
        encoded_value = b""
    elif isinstance(value, Account):
        assert get_storage_root is not None
        address = Address(key)
        encoded_value = encode_node(value, get_storage_root(address))
    else:
        encoded_value = encode_node(value)

    if encoded_value == b"":
        mpt.root_node = _mpt_delete_node(
            mpt, mpt.root_node, nibble_key, Uint(0)
        )
    else:
        mpt.root_node = _mpt_insert_node(
            mpt, mpt.root_node, nibble_key, encoded_value, Uint(0)
        )


def _mpt_insert_node(
    mpt: IncrementalMPT,
    node: Node,
    key: Bytes,
    value: Bytes,
    level: Uint,
) -> Node:
    """
    Insert or update a value in the tree.

    Return a new node for this position.
    """
    if node is None:
        return LeafNode(rest_of_key=key[level:], value=value, _dirty=True)

    if isinstance(node, LeafNode):
        return _insert_into_leaf(node, key, value, level)
    elif isinstance(node, ExtensionNode):
        return _insert_into_extension(mpt, node, key, value, level)
    elif isinstance(node, BranchNode):
        return _insert_into_branch(mpt, node, key, value, level)
    else:
        raise AssertionError(f"Invalid node type {type(node)}")


def _insert_into_leaf(
    node: LeafNode,
    key: Bytes,
    value: Bytes,
    level: Uint,
) -> Node:
    """Handle insertion when current node is a leaf."""
    existing_key = node.rest_of_key
    remaining_key = key[level:]

    if existing_key == remaining_key:
        return LeafNode(
            rest_of_key=existing_key,
            value=value,
            _dirty=True,
        )

    prefix_len = common_prefix_length(existing_key, remaining_key)

    if prefix_len > 0:
        branch = _create_branch_from_two_leaves(
            existing_key[prefix_len:],
            node.value,
            remaining_key[prefix_len:],
            value,
        )
        return ExtensionNode(
            key_segment=existing_key[:prefix_len],
            child=branch,
            _dirty=True,
        )
    else:
        return _create_branch_from_two_leaves(
            existing_key, node.value, remaining_key, value
        )


def _create_branch_from_two_leaves(
    key1: Bytes,
    value1: Bytes,
    key2: Bytes,
    value2: Bytes,
) -> BranchNode:
    """Create a branch node from two key-value pairs."""
    children: List[Optional[Node]] = [None] * 16
    branch_value = b""

    if len(key1) == 0:
        branch_value = value1
    else:
        idx1 = key1[0]
        children[idx1] = LeafNode(
            rest_of_key=key1[1:],
            value=value1,
            _dirty=True,
        )

    if len(key2) == 0:
        branch_value = value2
    else:
        idx2 = key2[0]
        children[idx2] = LeafNode(
            rest_of_key=key2[1:],
            value=value2,
            _dirty=True,
        )

    return BranchNode(
        children=tuple(children),
        value=branch_value,
        _dirty=True,
    )


def _insert_into_extension(
    mpt: IncrementalMPT,
    node: ExtensionNode,
    key: Bytes,
    value: Bytes,
    level: Uint,
) -> Node:
    """Handle insertion when current node is an extension."""
    remaining_key = key[level:]
    segment = node.key_segment
    prefix_len = common_prefix_length(segment, remaining_key)

    if prefix_len == len(segment):
        new_child = _mpt_insert_node(
            mpt,
            node.child,
            key,
            value,
            level + Uint(prefix_len),
        )
        return ExtensionNode(
            key_segment=segment,
            child=new_child,
            _dirty=True,
        )

    if prefix_len > 0:
        new_child = _split_extension(node, remaining_key, value, prefix_len)
        return ExtensionNode(
            key_segment=segment[:prefix_len],
            child=new_child,
            _dirty=True,
        )
    else:
        return _split_extension(node, remaining_key, value, 0)


def _split_extension(
    node: ExtensionNode,
    remaining_key: Bytes,
    value: Bytes,
    prefix_len: int,
) -> Node:
    """Split an extension node when keys diverge."""
    segment = node.key_segment
    children: List[Optional[Node]] = [None] * 16
    branch_value = b""

    segment_after_prefix = segment[prefix_len:]
    if len(segment_after_prefix) == 1:
        idx = segment_after_prefix[0]
        children[idx] = node.child
    elif len(segment_after_prefix) > 1:
        idx = segment_after_prefix[0]
        children[idx] = ExtensionNode(
            key_segment=segment_after_prefix[1:],
            child=node.child,
            _dirty=True,
        )

    key_after_prefix = remaining_key[prefix_len:]
    if len(key_after_prefix) == 0:
        branch_value = value
    else:
        idx = key_after_prefix[0]
        if children[idx] is None:
            children[idx] = LeafNode(
                rest_of_key=key_after_prefix[1:],
                value=value,
                _dirty=True,
            )
        else:
            raise AssertionError("Unexpected collision during split")

    return BranchNode(
        children=tuple(children),
        value=branch_value,
        _dirty=True,
    )


def _insert_into_branch(
    mpt: IncrementalMPT,
    node: BranchNode,
    key: Bytes,
    value: Bytes,
    level: Uint,
) -> Node:
    """Handle insertion when current node is a branch."""
    remaining_key = key[level:]

    if len(remaining_key) == 0:
        return BranchNode(
            children=node.children,
            value=value,
            _dirty=True,
        )

    child_idx = remaining_key[0]
    new_child = _mpt_insert_node(
        mpt,
        node.children[child_idx],
        key,
        value,
        level + Uint(1),
    )
    children = list(node.children)
    children[child_idx] = new_child
    return BranchNode(
        children=tuple(children),
        value=node.value,
        _dirty=True,
    )


def _mpt_delete_node(
    mpt: IncrementalMPT,
    node: Node,
    key: Bytes,
    level: Uint,
) -> Node:
    """
    Delete a key from the tree.

    Return the updated node (may be different type or None).
    """
    if node is None:
        return None

    if isinstance(node, LeafNode):
        if node.rest_of_key == key[level:]:
            return None
        return node
    elif isinstance(node, ExtensionNode):
        return _delete_from_extension(mpt, node, key, level)
    elif isinstance(node, BranchNode):
        return _delete_from_branch(mpt, node, key, level)
    else:
        raise AssertionError(f"Invalid node type {type(node)}")


def _delete_from_extension(
    mpt: IncrementalMPT,
    node: ExtensionNode,
    key: Bytes,
    level: Uint,
) -> Node:
    """Handle deletion when current node is an extension."""
    segment = node.key_segment
    remaining_key = key[level:]
    prefix_len = common_prefix_length(segment, remaining_key)

    if prefix_len < len(segment):
        return node

    old_child = node.child
    new_child = _mpt_delete_node(
        mpt, old_child, key, level + Uint(len(segment))
    )

    if new_child is None:
        return None

    if isinstance(new_child, ExtensionNode):
        return ExtensionNode(
            key_segment=segment + new_child.key_segment,
            child=new_child.child,
            _dirty=True,
        )
    elif isinstance(new_child, LeafNode):
        return LeafNode(
            rest_of_key=segment + new_child.rest_of_key,
            value=new_child.value,
            _dirty=True,
        )

    assert not isinstance(new_child, HashedNode)
    if new_child is old_child:
        return node

    return ExtensionNode(
        key_segment=segment,
        child=new_child,
        _dirty=True,
    )


def _delete_from_branch(
    mpt: IncrementalMPT,
    node: BranchNode,
    key: Bytes,
    level: Uint,
) -> Node:
    """Handle deletion when current node is a branch."""
    remaining_key = key[level:]

    if len(remaining_key) == 0:
        if node.value == b"":
            return node
        new_node = BranchNode(
            children=node.children,
            value=b"",
            _dirty=True,
        )
    else:
        child_idx = remaining_key[0]
        old_child = node.children[child_idx]
        new_child = _mpt_delete_node(
            mpt,
            old_child,
            key,
            level + Uint(1),
        )
        assert not isinstance(new_child, HashedNode)
        if new_child is old_child:
            return node
        children = list(node.children)
        children[child_idx] = new_child
        new_node = BranchNode(
            children=tuple(children),
            value=node.value,
            _dirty=True,
        )

    return _collapse_branch(mpt, new_node)


def _collapse_branch(mpt: IncrementalMPT, node: BranchNode) -> Node:
    """Collapse a branch node if it has only one child."""
    non_empty = [(i, c) for i, c in enumerate(node.children) if c is not None]

    assert len(non_empty) > 0 or node.value != b""

    if len(non_empty) == 1 and node.value == b"":
        idx, child = non_empty[0]
        _record_witness(mpt.witness, child)
        nibble = Bytes([idx])

        if isinstance(child, LeafNode):
            return LeafNode(
                rest_of_key=nibble + child.rest_of_key,
                value=child.value,
                _dirty=True,
            )
        elif isinstance(child, ExtensionNode):
            return ExtensionNode(
                key_segment=nibble + child.key_segment,
                child=child.child,
                _dirty=True,
            )
        elif isinstance(child, BranchNode):
            return ExtensionNode(
                key_segment=nibble,
                child=child,
                _dirty=True,
            )
        else:
            raise AssertionError(f"Unexpected node type {type(child)}")

    if len(non_empty) == 0 and node.value != b"":
        return LeafNode(
            rest_of_key=b"",
            value=node.value,
            _dirty=True,
        )

    return node


def mpt_root(mpt: IncrementalMPT) -> Root:
    """
    Compute the root hash of the incremental MPT.

    Parameters
    ----------
    mpt :
        The incremental MPT.

    Returns
    -------
    root : `Root`
        The MPT root hash.

    """
    if mpt.root_node is None:
        return EMPTY_TRIE_ROOT

    root_encoded = _encode_node_to_extended(mpt.root_node)

    if isinstance(root_encoded, Bytes):
        return Root(root_encoded)
    else:
        return keccak256(rlp.encode(root_encoded))


def compact_to_nibbles(compact: Bytes) -> Tuple[Bytes, bool]:
    """
    Decode hex-prefix (compact) encoding into nibbles and leaf flag.

    Inverse of ``nibble_list_to_compact``.

    Parameters
    ----------
    compact :
        Compact-encoded key bytes.

    Returns
    -------
    nibbles :
        The decoded nibble sequence.
    is_leaf :
        ``True`` if the compact encoding indicates a leaf node.

    """
    first_nibble = compact[0] >> 4
    is_leaf = (first_nibble & 0x02) != 0
    odd = (first_nibble & 0x01) != 0

    nibbles = bytearray()
    if odd:
        nibbles.append(compact[0] & 0x0F)
    for byte in compact[1:]:
        nibbles.append(byte >> 4)
        nibbles.append(byte & 0x0F)

    return Bytes(nibbles), is_leaf


def _resolve_child_ref(
    node_db: Dict[Bytes, Bytes],
    child_ref: Extended,
) -> Node:
    """
    Resolve a child reference from an RLP-decoded trie node.

    Handle three cases: empty string (no child), 32-byte hash
    (look up in node_db or create a ``HashedNode``), and inline RLP list
    (decode directly).
    """
    if isinstance(child_ref, (bytes, bytearray)):
        ref_bytes = Bytes(child_ref)
        if len(ref_bytes) == 0:
            return None
        assert len(ref_bytes) == 32, (
            f"Unexpected child ref length: {len(ref_bytes)}"
        )
        if ref_bytes in node_db:
            return _decode_witness_node(node_db, node_db[ref_bytes])
        return HashedNode(_hash=ref_bytes)
    else:
        return _decode_witness_node(node_db, rlp.encode(child_ref))


def _decode_witness_node(
    node_db: Dict[Bytes, Bytes],
    rlp_bytes: Bytes,
) -> Node:
    """
    Decode an RLP-encoded trie node into a ``Node``.

    Parameters
    ----------
    node_db :
        Mapping from node hash to RLP-encoded node data.
    rlp_bytes :
        The RLP-encoded node to decode.

    """
    decoded = rlp.decode(rlp_bytes)

    if isinstance(decoded, (bytes, bytearray)):
        assert len(decoded) == 0, "Expected empty node"
        return None

    assert isinstance(decoded, list)

    if len(decoded) == 2:
        path_bytes = decoded[0]
        assert isinstance(path_bytes, (bytes, bytearray))
        nibbles, is_leaf = compact_to_nibbles(Bytes(path_bytes))

        if is_leaf:
            value = decoded[1]
            assert isinstance(value, (bytes, bytearray))
            return LeafNode(
                rest_of_key=nibbles,
                value=Bytes(value),
                _dirty=False,
            )
        else:
            child = _resolve_child_ref(node_db, decoded[1])
            assert isinstance(child, (BranchNode, HashedNode)), (
                "ExtensionNode child must be a BranchNode"
            )
            return ExtensionNode(
                key_segment=nibbles,
                child=child,
                _dirty=False,
            )

    elif len(decoded) == 17:
        children: List[Optional[Node]] = []
        for i in range(16):
            children.append(_resolve_child_ref(node_db, decoded[i]))
        value_raw = decoded[16]
        if isinstance(value_raw, (bytes, bytearray)):
            value = Bytes(value_raw)
        else:
            value = b""
        # TODO: value is always empty in practice; refactor
        occupied = 16 - children.count(None) + (value != b"")
        assert occupied >= 2, "BranchNode must have at least 2 children"
        return BranchNode(
            children=tuple(children),
            value=value,
            _dirty=False,
        )
    else:
        raise AssertionError(f"Invalid RLP node length: {len(decoded)}")


def decode_witness_to_mpt(
    node_db: Dict[Bytes, Bytes],
    root_hash: Root,
    secured: bool,
    default: V,
) -> IncrementalMPT[K, V]:
    """
    Build an ``IncrementalMPT`` from a witness node database.

    Decode the trie starting at ``root_hash``, resolving child
    references from ``node_db``. Unknown children become
    ``HashedNode`` placeholders.

    Parameters
    ----------
    node_db :
        Mapping from node hash to RLP-encoded node data.
    root_hash :
        Root hash of the trie to decode.
    secured :
        Whether keys are hashed before insertion.
    default :
        Default value for missing keys.

    Returns
    -------
    mpt : `IncrementalMPT[K, V]`
        The decoded incremental MPT.

    """
    if root_hash == EMPTY_TRIE_ROOT:
        return IncrementalMPT(
            secured=secured,
            default=default,
            root_node=None,
            _data={},
        )

    root_rlp = node_db[root_hash]
    root_node = _decode_witness_node(node_db, root_rlp)

    return IncrementalMPT(
        secured=secured,
        default=default,
        root_node=root_node,
        _data={},
    )
