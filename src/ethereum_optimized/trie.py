"""
Optimized Trie
^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This module contains an implementation of a merkle trie that supports efficient
updates.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generic, List, Set

from ethereum import crypto
from ethereum.base_types import Bytes
from ethereum.frontier import rlp
from ethereum.frontier.eth_types import Root
from ethereum.frontier.trie import (
    EMPTY_TRIE_ROOT,
    BranchNode,
    ExtensionNode,
    InternalNode,
    LeafNode,
    T,
    bytes_to_nibble_list,
    common_prefix_length,
    encode_internal_node,
    encode_node,
)


@dataclass
class Trie(Generic[T]):
    """An optimized Trie implementation."""

    secured: bool
    default: T
    _data: Dict[Bytes, T] = field(default_factory=dict)
    _internal_nodes: Dict[Bytes, InternalNode] = field(default_factory=dict)
    _dirty_set: Set[Bytes] = field(default_factory=set)
    _root: Root = field(default=EMPTY_TRIE_ROOT)

    def __eq__(self, other: Any) -> bool:
        """
        Test for equality by comparing roots.

        This function does not work on tries that contain accounts.
        """
        if type(self) != type(other):
            return NotImplemented
        return root(self) == root(other)


def get_internal_key(trie: Trie[T], key: Bytes) -> Bytes:
    """
    Convert a key to the form used internally inside the trie.
    """
    if trie.secured:
        return bytes_to_nibble_list(crypto.keccak256(key))
    else:
        return bytes_to_nibble_list(key)


def trie_get(trie: Trie, key: Bytes) -> T:
    """
    Gets an item from the Merkle Trie.
    """
    return trie._data.get(get_internal_key(trie, key), trie.default)


def trie_set(trie: Trie[T], key: Bytes, value: T) -> None:
    """
    Stores an item in a Merkle Trie and adds `key` to `trie.dirty_set`.
    """
    nibble_list_key = get_internal_key(trie, key)
    trie._dirty_set.add(nibble_list_key)
    if value == trie.default:
        if nibble_list_key in trie._data:
            del trie._data[nibble_list_key]
    else:
        trie._data[nibble_list_key] = value


def no_storage(x: Bytes) -> Bytes:
    """
    A stub to replace the `get_storage_root` argument in tries that don't
    contain `Account` objects.
    """
    return None  # type: ignore


def root(
    trie: Trie,
    get_storage_root: Callable[[Bytes], Bytes] = no_storage,
) -> Root:
    """
    Calculate the root of the trie, by regenerating all internal nodes as
    required by `trie.dirty_set`.
    """
    if trie._dirty_set == set():
        return trie._root
    walk(
        trie,
        b"",
        list(sorted(trie._dirty_set, reverse=True)),
        get_storage_root,
    )
    trie._dirty_set = set()
    if b"" in trie._internal_nodes:
        root = encode_internal_node(trie._internal_nodes[b""])
        if isinstance(root, Bytes):
            trie._root = root
        else:
            trie._root = crypto.keccak256(rlp.encode(root))
    else:
        trie._root = crypto.keccak256(rlp.encode(b""))
    return trie._root


def walk(
    trie: Trie,
    node_key: Bytes,
    dirty_list: List[Bytes],
    get_storage_root: Callable[[Bytes], Bytes],
) -> None:
    """
    Visit the internal node at `node_key` and update it and all its subnodes as
    required by possible changes to elements in `dirty_list`.
    """
    while dirty_list and dirty_list[-1].startswith(node_key):
        current_node = trie._internal_nodes.get(node_key, None)
        if current_node is None:
            walk_empty(trie, node_key, dirty_list, get_storage_root)
        elif isinstance(current_node, LeafNode):
            walk_leaf(trie, node_key, dirty_list, get_storage_root)
        elif isinstance(current_node, ExtensionNode):
            walk_extension(trie, node_key, dirty_list, get_storage_root)
        elif isinstance(current_node, BranchNode):
            walk_branch(trie, node_key, dirty_list, get_storage_root)
        else:
            assert False  # Invalid internal node type


def walk_empty(
    trie: Trie,
    node_key: Bytes,
    dirty_list: List[Bytes],
    get_storage_root: Callable[[Bytes], Bytes],
) -> None:
    """
    Consume the last element of `dirty_list` and create a `LeafNode` pointing
    to it at `node_key`.
    """
    assert trie._internal_nodes.get(node_key) is None
    key = dirty_list.pop()
    value = trie._data.get(key)
    if value is not None:
        trie._internal_nodes[node_key] = LeafNode(
            key[len(node_key) :], encode_node(value, get_storage_root(key))
        )


def walk_leaf(
    trie: Trie,
    node_key: Bytes,
    dirty_list: List[Bytes],
    get_storage_root: Callable[[Bytes], Bytes],
) -> None:
    """
    Consume the last element of `dirty_list` and update the `LeafNode` at
    `node_key`, potentially turning it into `ExtensionNode` -> `BranchNode`
    -> `LeafNode`.
    """
    leaf_node = trie._internal_nodes[node_key]
    assert isinstance(leaf_node, LeafNode)
    key = dirty_list[-1]
    value = trie._data.get(key, None)
    if key[len(node_key) :] == leaf_node.rest_of_key:
        if value is None:
            del trie._internal_nodes[node_key]
        else:
            trie._internal_nodes[node_key] = LeafNode(
                leaf_node.rest_of_key,
                encode_node(value, get_storage_root(key)),
            )
        dirty_list.pop()
    else:
        prefix_length = common_prefix_length(
            leaf_node.rest_of_key, key[len(node_key) :]
        )
        prefix = leaf_node.rest_of_key[:prefix_length]
        if len(leaf_node.rest_of_key) != prefix_length:
            trie._internal_nodes[
                node_key + leaf_node.rest_of_key[: prefix_length + 1]
            ] = LeafNode(
                leaf_node.rest_of_key[prefix_length + 1 :],
                encode_node(
                    leaf_node.value,
                    get_storage_root(
                        node_key + leaf_node.rest_of_key[: prefix_length + 1]
                    ),
                ),
            )
        walk_branch(trie, node_key + prefix, dirty_list, get_storage_root)
        if prefix_length != 0:
            make_extension_node(trie, node_key, node_key + prefix)


def walk_extension(
    trie: Trie,
    node_key: Bytes,
    dirty_list: List[Bytes],
    get_storage_root: Callable[[Bytes], Bytes],
) -> None:
    """
    Consume the last element of `dirty_list` and update the `ExtensionNode` at
    `node_key`, potentially turning it into `ExtensionNode` -> `BranchNode`
    -> `ExtensionNode`.
    """
    extension_node = trie._internal_nodes[node_key]
    assert isinstance(extension_node, ExtensionNode)
    key = dirty_list[-1]
    if key[len(node_key) :].startswith(extension_node.key_segment):
        walk(
            trie,
            node_key + extension_node.key_segment,
            dirty_list,
            get_storage_root,
        )
        make_extension_node(
            trie, node_key, node_key + extension_node.key_segment
        )
        return
    prefix_length = common_prefix_length(
        extension_node.key_segment, key[len(node_key) :]
    )
    prefix = extension_node.key_segment[:prefix_length]
    if prefix_length != len(extension_node.key_segment) - 1:
        make_extension_node(
            trie,
            node_key + extension_node.key_segment[: prefix_length + 1],
            node_key + extension_node.key_segment,
        )
    walk_branch(trie, node_key + prefix, dirty_list, get_storage_root)
    if prefix_length != 0:
        make_extension_node(trie, node_key, node_key + prefix)


def walk_branch(
    trie: Trie,
    node_key: Bytes,
    dirty_list: List[Bytes],
    get_storage_root: Callable[[Bytes], Bytes],
) -> None:
    """
    Make a `BranchNode` at `node_key` and consume all elements of `dirty_list`
    that are under it.
    """
    if dirty_list[-1] == node_key:
        dirty_list.pop()

    subnodes = []
    for i in range(16):
        walk(trie, node_key + bytes([i]), dirty_list, get_storage_root)
        subnodes.append(trie._internal_nodes.get(node_key + bytes([i]), None))

    value_at_node = trie._data.get(node_key, None)
    number_of_subnodes = 16 - subnodes.count(None)

    if number_of_subnodes == 0:
        if value_at_node is None:
            if node_key in trie._internal_nodes:
                del trie._internal_nodes[node_key]
        else:
            trie._internal_nodes[node_key] = LeafNode(
                b"", encode_node(value_at_node, get_storage_root(node_key))
            )
    elif number_of_subnodes == 1 and value_at_node is None:
        for i in range(16):
            if subnodes[i] is not None:
                subnode_index = i
                break
        make_extension_node(trie, node_key, node_key + bytes([subnode_index]))
    else:
        encoded_subnodes = [
            encode_internal_node(subnode) for subnode in subnodes
        ]
        if value_at_node is None:
            trie._internal_nodes[node_key] = BranchNode(encoded_subnodes, b"")
        else:
            trie._internal_nodes[node_key] = BranchNode(
                encoded_subnodes, value_at_node
            )


def make_extension_node(
    trie: Trie, node_key: Bytes, target_key: Bytes
) -> None:
    """
    Make an extension node at `node_key` pointing at `target_key`. This
    function will correctly replace `ExtensionNode -> LeafNode` with `LeafNode`
    and `ExtensionNode -> ExtensionNode` with `ExtensionNode`.
    """
    assert node_key != target_key
    target_node = trie._internal_nodes.get(target_key, None)
    if target_node is None:
        if (
            node_key in trie._internal_nodes
        ):  # This condition never fails, but is included for correctness
            del trie._internal_nodes[node_key]
    elif isinstance(target_node, LeafNode):
        trie._internal_nodes[node_key] = LeafNode(
            target_key[len(node_key) :] + target_node.rest_of_key,
            target_node.value,
        )
        del trie._internal_nodes[target_key]
    elif isinstance(target_node, ExtensionNode):
        trie._internal_nodes[node_key] = ExtensionNode(
            target_key[len(node_key) :] + target_node.key_segment,
            target_node.subnode,
        )
        del trie._internal_nodes[target_key]
    elif isinstance(target_node, BranchNode):
        trie._internal_nodes[node_key] = ExtensionNode(
            target_key[len(node_key) :], encode_internal_node(target_node)
        )
    else:
        assert False  # Invalid internal node type
