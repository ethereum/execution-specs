"""
Incremental Merkle Patricia Trie.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Provide a mutable MPT that supports incremental updates and
witness tracking. The tree structure is updated in-place rather
than rebuilt from scratch on each root calculation.
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
    final,
)

from ethereum_rlp import Extended, rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import Uint, ulen

from ethereum.crypto.hash import keccak256
from ethereum.merkle_patricia_trie import (
    EMPTY_TRIE_ROOT,
    K,
    V,
    _prepare_data,
    bytes_to_nibble_list,
    common_prefix_length,
    encode_node,
    nibble_list_to_compact,
)
from ethereum.state import Account, Address, Root


@final
@dataclass
class MutableLeafNode:
    """Mutable leaf node in the Merkle Trie for in-place updates."""

    rest_of_key: Bytes
    value: Bytes
    _hash: Optional[Bytes] = None
    _rlp: Optional[Bytes] = None
    _dirty: bool = False


@final
@dataclass
class MutableExtensionNode:
    """Mutable extension node in the Merkle Trie for in-place updates."""

    key_segment: Bytes
    child: "MutableNode"
    _hash: Optional[Bytes] = None
    _rlp: Optional[Bytes] = None
    _dirty: bool = False


@final
@dataclass
class MutableBranchNode:
    """Mutable branch node in the Merkle Trie for in-place updates."""

    children: List[Optional["MutableNode"]]
    value: Bytes
    _hash: Optional[Bytes] = None
    _rlp: Optional[Bytes] = None
    _dirty: bool = False


@final
@dataclass
class HashedNode:
    """Placeholder for a trie subtree known only by its hash."""

    _hash: Bytes


MutableNode = Union[
    MutableLeafNode,
    MutableExtensionNode,
    MutableBranchNode,
    HashedNode,
    None,
]


@final
@dataclass
class Witness:
    """Track nodes accessed during trie operations for witness generation."""

    accessed_nodes: Dict[Bytes, Bytes] = field(default_factory=dict)


@final
@dataclass
class IncrementalMPT(Generic[K, V]):
    """
    An MPT that supports incremental updates and witness tracking.

    Maintain an actual tree structure that can be updated in-place,
    rather than rebuilding the entire tree on each root calculation.
    """

    secured: bool
    default: V
    root_node: MutableNode = None
    witness: Witness = field(default_factory=Witness)
    _data: Dict[K, V] = field(default_factory=dict)


def _build_mutable_tree(
    obj: Mapping[Bytes, Bytes], level: Uint
) -> MutableNode:
    """
    Build a mutable tree structure from a prepared key-value mapping.

    Similar to ``patricialize()`` but create mutable nodes for
    in-place updates.

    Parameters
    ----------
    obj :
        Underlying trie key-value pairs, with keys in
        nibble-list format.
    level :
        Current trie level.

    Returns
    -------
    node : `MutableNode`
        Root node of the mutable tree.

    """
    if len(obj) == 0:
        return None

    arbitrary_key = next(iter(obj))

    if len(obj) == 1:
        return MutableLeafNode(
            rest_of_key=arbitrary_key[level:],
            value=obj[arbitrary_key],
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
        child = _build_mutable_tree(obj, level + Uint(prefix_length))
        return MutableExtensionNode(key_segment=prefix, child=child)

    branches: List[MutableMapping[Bytes, Bytes]] = [{} for _ in range(16)]
    value = b""

    for key in obj:
        if len(key) == level:
            value = obj[key]
        else:
            branches[key[level]][key] = obj[key]

    children: List[Optional[MutableNode]] = [
        _build_mutable_tree(branches[k], level + Uint(1)) for k in range(16)
    ]

    return MutableBranchNode(children=children, value=value)


def build_mpt(
    data: Mapping[K, V],
    secured: bool,
    default: V,
    get_storage_root: Optional[Callable[[Address], Root]] = None,
) -> IncrementalMPT[K, V]:
    """
    Build an IncrementalMPT from key-value data.

    Call with the pre-execution state to create a mutable tree
    structure that can be updated in-place during execution.

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
    root_node = _build_mutable_tree(prepared, Uint(0))

    return IncrementalMPT(
        secured=secured,
        default=default,
        root_node=root_node,
        _data=dict(data),
    )


def _invalidate_hash(node: MutableNode) -> None:
    """Invalidate the cached hash of a node."""
    assert not isinstance(node, HashedNode), "HashedNode cannot be invalidated"
    if node is None:
        return
    node._hash = None
    node._rlp = None


def _record_witness(
    witness: Witness,
    node: MutableNode,
) -> None:
    """Record a node access in the witness."""
    assert not isinstance(node, HashedNode), "HashedNode cannot be witnessed"
    if node is None:
        return

    if node._dirty:
        return

    node_hash, node_rlp = _compute_node_hash_and_rlp(node)
    if node_hash is not None and node_hash not in witness.accessed_nodes:
        witness.accessed_nodes[node_hash] = node_rlp


def _encode_mutable_node(node: MutableNode) -> Extended:
    """
    Encode a mutable node to its RLP form.

    Similar to ``encode_internal_node`` but for mutable nodes.
    """
    if node is None:
        return b""
    elif isinstance(node, HashedNode):
        raise AssertionError("HashedNode cannot be inline-encoded")
    elif isinstance(node, MutableLeafNode):
        return (
            nibble_list_to_compact(node.rest_of_key, True),
            node.value,
        )
    elif isinstance(node, MutableExtensionNode):
        child_encoded = _encode_mutable_node_to_extended(node.child)
        return (
            nibble_list_to_compact(node.key_segment, False),
            child_encoded,
        )
    elif isinstance(node, MutableBranchNode):
        children_encoded = [
            _encode_mutable_node_to_extended(child) for child in node.children
        ]
        return children_encoded + [node.value]
    else:
        raise AssertionError(f"Invalid mutable node type {type(node)}!")


def _encode_mutable_node_to_extended(
    node: MutableNode,
) -> Extended:
    """
    Encode a mutable node for embedding in parent.

    Return the hash if RLP >= 32 bytes, otherwise return
    unencoded form.
    """
    if node is None:
        return b""

    if isinstance(node, HashedNode):
        return node._hash

    if not node._dirty and node._hash is not None:
        return node._hash

    unencoded = _encode_mutable_node(node)
    encoded = rlp.encode(unencoded)
    node._rlp = encoded

    if len(encoded) < 32:
        return unencoded
    else:
        node._hash = keccak256(encoded)
        return node._hash


def _compute_node_hash_and_rlp(
    node: MutableNode,
) -> Tuple[Optional[Bytes], Bytes]:
    """
    Compute the hash and RLP encoding of a node.

    Return (hash, rlp) where hash may be None for small nodes.
    """
    if node is None:
        return None, b""

    assert not isinstance(node, HashedNode), (
        "HashedNode cannot appear in _compute_node_hash_and_rlp"
    )

    if node._rlp is not None:
        if node._hash is not None:
            return node._hash, node._rlp
        elif len(node._rlp) >= 32:
            return keccak256(node._rlp), node._rlp

    unencoded = _encode_mutable_node(node)
    encoded = rlp.encode(unencoded)

    node._rlp = encoded

    if len(encoded) >= 32:
        node._hash = keccak256(encoded)
        return node._hash, encoded
    else:
        return None, encoded


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
    node: MutableNode,
    key: Bytes,
    level: Uint,
) -> None:
    """Traverse the tree recording nodes in the witness."""
    if node is None:
        return

    _record_witness(mpt.witness, node)

    if isinstance(node, MutableLeafNode):
        pass
    elif isinstance(node, MutableExtensionNode):
        segment_len = len(node.key_segment)
        lvl = int(level)
        if key[lvl : lvl + segment_len] == node.key_segment:
            _mpt_traverse_for_witness(
                mpt,
                node.child,
                key,
                Uint(lvl + segment_len),
            )
    elif isinstance(node, MutableBranchNode):
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

    Update the tree in-place and invalidate cached hashes along
    the path.

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
    elif value is None:
        raise AssertionError("cannot encode `None`")
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
    node: MutableNode,
    key: Bytes,
    value: Bytes,
    level: Uint,
) -> MutableNode:
    """
    Insert or update a value in the mutable tree.

    Return the new/updated node for this position.
    """
    if node is None:
        return MutableLeafNode(
            rest_of_key=key[level:], value=value, _dirty=True
        )

    _invalidate_hash(node)

    if isinstance(node, MutableLeafNode):
        return _insert_into_leaf(mpt, node, key, value, level)
    elif isinstance(node, MutableExtensionNode):
        return _insert_into_extension(mpt, node, key, value, level)
    elif isinstance(node, MutableBranchNode):
        return _insert_into_branch(mpt, node, key, value, level)
    else:
        raise AssertionError(f"Invalid node type {type(node)}")


def _insert_into_leaf(
    _mpt: IncrementalMPT,
    node: MutableLeafNode,
    key: Bytes,
    value: Bytes,
    level: Uint,
) -> MutableNode:
    """Handle insertion when current node is a leaf."""
    existing_key = node.rest_of_key
    remaining_key = key[level:]

    if existing_key == remaining_key:
        node.value = value
        node._dirty = True
        return node

    prefix_len = common_prefix_length(existing_key, remaining_key)

    if prefix_len > 0:
        branch = _create_branch_from_two_leaves(
            existing_key[prefix_len:],
            node.value,
            remaining_key[prefix_len:],
            value,
        )
        return MutableExtensionNode(
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
) -> MutableBranchNode:
    """Create a branch node from two key-value pairs."""
    children: List[Optional[MutableNode]] = [None] * 16
    branch_value = b""

    if len(key1) == 0:
        branch_value = value1
    else:
        idx1 = key1[0]
        children[idx1] = MutableLeafNode(
            rest_of_key=key1[1:],
            value=value1,
            _dirty=True,
        )

    if len(key2) == 0:
        branch_value = value2
    else:
        idx2 = key2[0]
        children[idx2] = MutableLeafNode(
            rest_of_key=key2[1:],
            value=value2,
            _dirty=True,
        )

    return MutableBranchNode(
        children=children,
        value=branch_value,
        _dirty=True,
    )


def _insert_into_extension(
    mpt: IncrementalMPT,
    node: MutableExtensionNode,
    key: Bytes,
    value: Bytes,
    level: Uint,
) -> MutableNode:
    """Handle insertion when current node is an extension."""
    remaining_key = key[level:]
    segment = node.key_segment
    prefix_len = common_prefix_length(segment, remaining_key)

    if prefix_len == len(segment):
        node.child = _mpt_insert_node(
            mpt,
            node.child,
            key,
            value,
            level + Uint(prefix_len),
        )
        node._dirty = True
        return node

    if prefix_len > 0:
        new_child = _split_extension(node, remaining_key, value, prefix_len)
        return MutableExtensionNode(
            key_segment=segment[:prefix_len],
            child=new_child,
            _dirty=True,
        )
    else:
        return _split_extension(node, remaining_key, value, 0)


def _split_extension(
    node: MutableExtensionNode,
    remaining_key: Bytes,
    value: Bytes,
    prefix_len: int,
) -> MutableNode:
    """Split an extension node when keys diverge."""
    segment = node.key_segment
    children: List[Optional[MutableNode]] = [None] * 16
    branch_value = b""

    segment_after_prefix = segment[prefix_len:]
    if len(segment_after_prefix) == 1:
        idx = segment_after_prefix[0]
        children[idx] = node.child
    elif len(segment_after_prefix) > 1:
        idx = segment_after_prefix[0]
        children[idx] = MutableExtensionNode(
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
            children[idx] = MutableLeafNode(
                rest_of_key=key_after_prefix[1:],
                value=value,
                _dirty=True,
            )
        else:
            raise AssertionError("Unexpected collision during split")

    return MutableBranchNode(
        children=children,
        value=branch_value,
        _dirty=True,
    )


def _insert_into_branch(
    mpt: IncrementalMPT,
    node: MutableBranchNode,
    key: Bytes,
    value: Bytes,
    level: Uint,
) -> MutableNode:
    """Handle insertion when current node is a branch."""
    remaining_key = key[level:]

    if len(remaining_key) == 0:
        node.value = value
        node._dirty = True
        return node

    child_idx = remaining_key[0]
    node.children[child_idx] = _mpt_insert_node(
        mpt,
        node.children[child_idx],
        key,
        value,
        level + Uint(1),
    )
    node._dirty = True
    return node


def _mpt_delete_node(
    mpt: IncrementalMPT,
    node: MutableNode,
    key: Bytes,
    level: Uint,
) -> MutableNode:
    """
    Delete a key from the mutable tree.

    Return the updated node (may be different type or None).
    """
    if node is None:
        return None

    _invalidate_hash(node)

    if isinstance(node, MutableLeafNode):
        if node.rest_of_key == key[level:]:
            return None
        return node
    elif isinstance(node, MutableExtensionNode):
        return _delete_from_extension(mpt, node, key, level)
    elif isinstance(node, MutableBranchNode):
        return _delete_from_branch(mpt, node, key, level)
    else:
        raise AssertionError(f"Invalid node type {type(node)}")


def _delete_from_extension(
    mpt: IncrementalMPT,
    node: MutableExtensionNode,
    key: Bytes,
    level: Uint,
) -> MutableNode:
    """Handle deletion when current node is an extension."""
    segment = node.key_segment
    remaining_key = key[level:]
    prefix_len = common_prefix_length(segment, remaining_key)

    if prefix_len < len(segment):
        return node

    old_child = node.child
    new_child = _mpt_delete_node(mpt, old_child, key, level + ulen(segment))

    if new_child is None:
        return None

    if isinstance(new_child, MutableExtensionNode):
        return MutableExtensionNode(
            key_segment=segment + new_child.key_segment,
            child=new_child.child,
            _dirty=True,
        )
    elif isinstance(new_child, MutableLeafNode):
        return MutableLeafNode(
            rest_of_key=segment + new_child.rest_of_key,
            value=new_child.value,
            _dirty=True,
        )

    assert not isinstance(new_child, HashedNode)
    child_changed = new_child is not old_child or (
        new_child is not None and new_child._dirty
    )
    if not child_changed:
        return node

    node.child = new_child
    node._dirty = True
    return node


def _delete_from_branch(
    mpt: IncrementalMPT,
    node: MutableBranchNode,
    key: Bytes,
    level: Uint,
) -> MutableNode:
    """Handle deletion when current node is a branch."""
    remaining_key = key[level:]

    if len(remaining_key) == 0:
        if node.value == b"":
            return node
        node.value = b""
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
        child_changed = new_child is not old_child or (
            new_child is not None and new_child._dirty
        )
        if not child_changed:
            return node
        node.children[child_idx] = new_child

    node._dirty = True
    return _collapse_branch(mpt, node)


def _collapse_branch(
    mpt: IncrementalMPT, node: MutableBranchNode
) -> MutableNode:
    """Collapse a branch node if it has only one child."""
    non_empty = [(i, c) for i, c in enumerate(node.children) if c is not None]

    assert len(non_empty) > 0 or node.value != b""

    if len(non_empty) == 1 and node.value == b"":
        idx, child = non_empty[0]
        _record_witness(mpt.witness, child)
        nibble = Bytes([idx])

        if isinstance(child, MutableLeafNode):
            return MutableLeafNode(
                rest_of_key=nibble + child.rest_of_key,
                value=child.value,
                _dirty=True,
            )
        elif isinstance(child, MutableExtensionNode):
            return MutableExtensionNode(
                key_segment=nibble + child.key_segment,
                child=child.child,
                _dirty=True,
            )
        elif isinstance(child, MutableBranchNode):
            return MutableExtensionNode(
                key_segment=nibble,
                child=child,
                _dirty=True,
            )
        else:
            raise AssertionError(f"Unexpected node type {type(child)}")

    if len(non_empty) == 0 and node.value != b"":
        return MutableLeafNode(
            rest_of_key=b"",
            value=node.value,
            _dirty=True,
        )

    return node


def mpt_root(mpt: IncrementalMPT) -> Root:
    """
    Compute the root hash of the incremental MPT.

    Use cached hashes where available for efficiency.

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

    root_encoded = _encode_mutable_node_to_extended(mpt.root_node)

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
) -> MutableNode:
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
) -> MutableNode:
    """
    Decode an RLP-encoded trie node into a ``MutableNode``.

    Parameters
    ----------
    node_db :
        Mapping from node hash to RLP-encoded node data.
    rlp_bytes :
        The RLP-encoded node to decode.

    """
    node_hash: Optional[Bytes] = None
    if len(rlp_bytes) >= 32:
        node_hash = keccak256(rlp_bytes)

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
            return MutableLeafNode(
                rest_of_key=nibbles,
                value=Bytes(value),
                _hash=node_hash,
                _rlp=rlp_bytes,
            )
        else:
            assert len(nibbles) > 0, "ExtensionNode must have a non-empty path"
            child = _resolve_child_ref(node_db, decoded[1])
            assert isinstance(child, (MutableBranchNode, HashedNode)), (
                "ExtensionNode child must be a BranchNode"
            )
            return MutableExtensionNode(
                key_segment=nibbles,
                child=child,
                _hash=node_hash,
                _rlp=rlp_bytes,
            )

    elif len(decoded) == 17:
        children: List[Optional[MutableNode]] = []
        for i in range(16):
            children.append(_resolve_child_ref(node_db, decoded[i]))
        value_raw = decoded[16]
        if isinstance(value_raw, (bytes, bytearray)):
            value = Bytes(value_raw)
        else:
            value = b""
        occupied = 16 - children.count(None) + (value != b"")
        assert occupied >= 2, (
            "BranchNode must have at least 2 occupied entries"
        )
        return MutableBranchNode(
            children=children,
            value=value,
            _hash=node_hash,
            _rlp=rlp_bytes,
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
