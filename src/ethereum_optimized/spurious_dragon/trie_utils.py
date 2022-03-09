"""
Optimized Trie Utility Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This module contains utility functions needed by the optimized state.
"""
from typing import Tuple

from ethereum import rlp
from ethereum.base_types import Bytes
from ethereum.spurious_dragon.trie import (
    BranchNode,
    ExtensionNode,
    InternalNode,
    LeafNode,
    nibble_list_to_compact,
)
from ethereum.utils.ensure import ensure


def compact_to_nibble_list(bytes: Bytes) -> Tuple[Bytes, bool]:
    """
    Performs the reverse of
    `ethereum.spurious_dragon.trie.nibble_list_to_compact`.
    """
    is_leaf = bool(bytes[0] & 0x20)
    parity = bool(bytes[0] & 0x10)
    nibble_list = bytearray()
    if parity:
        nibble_list.append(bytes[0] & 0x0F)
    for byte in bytes[1:]:
        nibble_list.append(byte >> 4)
        nibble_list.append(byte & 0x0F)
    return (Bytes(nibble_list), is_leaf)


def encode_internal_node_nohash(node: InternalNode) -> Bytes:
    """
    Perform an `ethereum.spurious_dragon.trie.encode_internal_node`, but skip
    the hashing step.
    """
    if isinstance(node, LeafNode):
        return rlp.encode(
            [
                nibble_list_to_compact(node.rest_of_key, True),
                node.value,
            ]
        )
    elif isinstance(node, ExtensionNode):
        return rlp.encode(
            [
                nibble_list_to_compact(node.key_segment, False),
                node.subnode,
            ]
        )
    elif isinstance(node, BranchNode):
        return rlp.encode(node.subnodes + [node.value])
    else:
        raise Exception(f"Invalid internal node type {type(node)}!")


def decode_to_internal_node(data_in: Bytes) -> InternalNode:
    """
    Decode an `InternalNode` from it's `RLP` representation.
    """
    data = rlp.decode(data_in)
    assert isinstance(data, list)
    if len(data) == 2:
        key_segment, is_leaf = compact_to_nibble_list(data[0])
        if is_leaf:
            return LeafNode(key_segment, data[1])
        else:
            return ExtensionNode(key_segment, data[1])
    else:
        ensure(len(data) == 17, AssertionError)
        return BranchNode(data[:-1], data[-1])
