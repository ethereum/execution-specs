"""
Optimized State
^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This module contains functions can be monkey patched into
`ethereum.frontier.state` to use an optmized database backed state.
"""
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Set, Tuple

import lmdb

import ethereum.crypto as crypto
from ethereum.base_types import U256, Bytes, Uint
from ethereum.frontier import rlp
from ethereum.frontier.eth_types import EMPTY_ACCOUNT, Account, Address, Root
from ethereum.frontier.trie import (
    EMPTY_TRIE_ROOT,
    BranchNode,
    ExtensionNode,
    InternalNode,
    LeafNode,
    Node,
    bytes_to_nibble_list,
    common_prefix_length,
    encode_internal_node,
)

from .trie_utils import decode_to_internal_node, encode_internal_node_nohash

# 0x0 : Metadata
# 0x1 : Accounts and storage
# 0x2 : Internal Nodes


@dataclass
class State:
    """
    The State, backed by a LMDB database.

    When created with `State()` store the db in a temporary directory. When
    created with `State(path)` open or create the db located at `path`.
    """

    _db: Any
    _tx_stack: List[Any]
    _dirty_accounts: List[Dict[Bytes, Optional[Account]]]
    _dirty_storage: List[Dict[Bytes, Dict[Bytes, Optional[U256]]]]
    _destroyed_accounts: List[Set[Bytes]]
    _root: Root

    def __init__(self, path: Optional[str] = None) -> None:
        if path is None:
            # Reference kept so directory won't be deleted until State is
            self._tempdir = TemporaryDirectory()
            self._db = lmdb.open(self._tempdir.name, map_size=2 ** 20)
        else:
            self._db = lmdb.open(path, map_size=2 ** 40)
        self._tx_stack = []
        self._dirty_accounts = [{}]
        self._dirty_storage = [{}]
        self._destroyed_accounts = [set()]
        begin_db_transaction(self)

    def __eq__(self, other: object) -> bool:
        """
        Test for equality by comparing state roots.
        """
        if not isinstance(other, State):
            return NotImplemented
        return state_root(self) == state_root(other)


def begin_db_transaction(state: State) -> None:
    """
    Start a database transaction. A transaction is automatically started when a
    `State` is created and the entire stack of transactions must be commited
    for any permanent changes to be made to the database.

    Database transctions are more expensive than normal transactions, but the
    state root can be calculated while in them.

    No operations are supported when not in a transaction.
    """
    if state._tx_stack == []:
        state._tx_stack.append(lmdb.Transaction(state._db, write=True))
    else:
        state_root(state)
        state._tx_stack.append(
            lmdb.Transaction(state._db, parent=state._tx_stack[-1], write=True)
        )


def commit_db_transaction(state: State) -> None:
    """
    Commit the current database transaction.
    """
    state_root(state)
    state._tx_stack.pop().commit()


def rollback_db_transaction(state: State) -> None:
    """
    Rollback the current database transaction.
    """
    state._tx_stack.pop().abort()
    state._dirty_accounts = [{}]
    state._dirty_storage = [{}]
    state._destroyed_accounts = [set()]


def begin_transaction(state: State) -> None:
    """
    See `ethereum.frontier.state`.
    """
    state._tx_stack.append(state._tx_stack[-1])
    state._dirty_accounts.append({})
    state._dirty_storage.append({})
    state._destroyed_accounts.append(set())


def commit_transaction(state: State) -> None:
    """
    See `ethereum.frontier.state`.
    """
    for (internal_address, account) in state._dirty_accounts.pop().items():
        state._dirty_accounts[-1][internal_address] = account
    state._destroyed_accounts[-2] |= state._destroyed_accounts[-1]
    for internal_address in state._destroyed_accounts.pop():
        state._dirty_storage[-2].pop(internal_address)
    for (internal_address, cache) in state._dirty_storage.pop().items():
        if internal_address not in state._dirty_storage[-1]:
            state._dirty_storage[-1][internal_address] = {}
        for (key, value) in cache.items():
            state._dirty_storage[-1][internal_address][key] = value
    state._tx_stack.pop()


def rollback_transaction(state: State) -> None:
    """
    See `ethereum.frontier.state`.
    """
    state._tx_stack.pop()
    state._dirty_accounts.pop()
    state._dirty_storage.pop()
    state._destroyed_accounts.pop()


def get_internal_key(key: Bytes) -> Bytes:
    """
    Convert a key to the form used internally inside the trie.
    """
    return bytes_to_nibble_list(crypto.keccak256(key))


def get_storage(state: State, address: Address, key: Bytes) -> U256:
    """
    See `ethereum.frontier.state`.
    """
    internal_address = get_internal_key(address)
    internal_key = get_internal_key(key)
    for i in range(len(state._tx_stack) - 1, -1, -1):
        if internal_address in state._dirty_storage[i]:
            if internal_key in state._dirty_storage[i][internal_address]:
                cached_res = state._dirty_storage[i][internal_address][
                    internal_key
                ]
                if cached_res is None:
                    return U256(0)
                else:
                    return cached_res
            if internal_key in state._destroyed_accounts[i]:
                # Higher levels refer to the account prior to destruction
                return U256(0)
    res = state._tx_stack[-1].get(
        b"\x01" + internal_address + b"\x00" + internal_key
    )
    if res is None:
        return U256(0)
    else:
        res = rlp.decode(res)
        assert isinstance(res, bytes)
        return U256.from_be_bytes(res)


def set_storage(
    state: State, address: Address, key: Bytes, value: U256
) -> None:
    """
    See `ethereum.frontier.state`.
    """
    internal_address = get_internal_key(address)
    internal_key = get_internal_key(key)
    if internal_address not in state._dirty_accounts[-1]:
        state._dirty_accounts[-1][internal_address] = get_account_optional(
            state, address
        )
    if internal_address not in state._dirty_storage[-1]:
        state._dirty_storage[-1][internal_address] = {}
    if value == 0:
        state._dirty_storage[-1][internal_address][internal_key] = None
    else:
        state._dirty_storage[-1][internal_address][internal_key] = value


def get_account_optional(state: State, address: Address) -> Optional[Account]:
    """
    See `ethereum.frontier.state`.
    """
    internal_address = get_internal_key(address)
    for cache in reversed(state._dirty_accounts):
        if internal_address in cache:
            return cache[internal_address]
    res = state._tx_stack[-1].get(b"\x01" + internal_address)
    if res is None:
        return None
    else:
        data = rlp.decode(res)
        assert isinstance(data, list)
        return Account(
            Uint.from_be_bytes(data[0]), U256.from_be_bytes(data[1]), data[2]
        )


def get_account(state: State, address: Address) -> Account:
    """
    See `ethereum.frontier.state`.
    """
    res = get_account_optional(state, address)
    if res is None:
        return EMPTY_ACCOUNT
    else:
        return res


def set_account(
    state: State, address: Address, account: Optional[Account]
) -> None:
    """
    See `ethereum.frontier.state`.
    """
    internal_address = get_internal_key(address)
    if account is None:
        state._dirty_accounts[-1][internal_address] = None
    else:
        state._dirty_accounts[-1][internal_address] = account


def destroy_account(state: State, address: Address) -> None:
    """
    See `ethereum.frontier.state`.
    """
    internal_address = get_internal_key(address)
    state._destroyed_accounts[-1].add(internal_address)
    state._dirty_storage[-1].pop(internal_address, None)
    state._dirty_accounts[-1][internal_address] = None


def clear_destroyed_account(state: State, internal_address: Bytes) -> None:
    """
    Remove every storage key associated to a destroyed account from the
    database.
    """
    cursor = state._tx_stack[-1].cursor()
    cursor.set_range(b"\x01" + internal_address + b"\x00")
    while cursor.key().startswith(b"\x01" + internal_address):
        cursor.delete()
    cursor.set_range(b"\x02" + internal_address + b"\x00")
    while cursor.key().startswith(b"\x02" + internal_address):
        cursor.delete()


def get_account_debug(state: State, key: Bytes) -> Bytes:
    """
    Treats the `State` as an unsecured `Trie[Bytes, Bytes]`. It exists
    exclusively to test the trie implementation.
    """
    internal_key = bytes_to_nibble_list(key)
    for cache in reversed(state._dirty_accounts):
        if internal_key in cache:
            return cache[internal_key]  # type: ignore
    return state._tx_stack[-1].get(b"\x01" + internal_key)


def set_account_debug(
    state: State, key: Bytes, account: Optional[Bytes]
) -> None:
    """
    Treats the `State` as an unsecured `Trie[Bytes, Bytes]`. It exists
    exclusively to test the trie implementation.
    """
    internal_key = bytes_to_nibble_list(key)
    state._dirty_accounts[-1][internal_key] = account  # type: ignore
    if account is None:
        state._dirty_accounts[-1][internal_key] = None
    else:
        state._dirty_accounts[-1][internal_key] = account  # type: ignore


def make_node(
    state: State, node_key: Bytes, value: Node, cursor: Any
) -> rlp.RLP:
    """
    Given a node, get its `RLP` representation. This function calculates the
    storage root if the node is an `Account`.
    """
    if isinstance(value, Account):
        account_storage_root = _storage_root(state, node_key, cursor)
        return rlp.encode_account(value, account_storage_root)
    elif isinstance(value, Bytes):
        return value
    else:
        assert value is not None
        return rlp.encode(value)


def write_internal_node(
    cursor: Any, trie_prefix: Bytes, key: Bytes, node: Optional[InternalNode]
) -> None:
    """
    Write an internal node into the database.
    """
    if node is None:
        if cursor.set_key(b"\x02" + trie_prefix + key):
            cursor.delete()
    else:
        cursor.put(
            b"\x02" + trie_prefix + key,
            encode_internal_node_nohash(node),
        )


def state_root(
    state: State,
) -> Root:
    """
    Calculate the state root.
    """
    for internal_address, account in state._dirty_accounts[-1].items():
        if account is None:
            state._tx_stack[-1].delete(b"\x01" + internal_address)
        elif isinstance(account, Bytes):  # Testing only
            state._tx_stack[-1].put(
                b"\x01" + internal_address,
                account,
            )
        elif isinstance(account, Account):
            state._tx_stack[-1].put(
                b"\x01" + internal_address,
                rlp.encode([account.nonce, account.balance, account.code]),
            )
        else:
            raise Exception(
                f"Invalid object of type {type(account)} stored in state"
            )
    root_node = walk(
        state,
        b"",
        b"",
        list(sorted(state._dirty_accounts[-1].items(), reverse=True)),
        state._tx_stack[-1].cursor(),
    )
    write_internal_node(state._tx_stack[-1].cursor(), b"", b"", root_node)
    state._dirty_accounts[-1] = {}
    if root_node is None:
        return EMPTY_TRIE_ROOT
    else:
        root = encode_internal_node(root_node)
        if isinstance(root, Bytes):
            return Root(root)
        else:
            return crypto.keccak256(rlp.encode(root))


def storage_root(state: State, address: Bytes) -> None:
    """
    Calculate the storage root.
    """
    _storage_root(
        state, get_internal_key(address), state._tx_stack[-1].cursor()
    )


def _storage_root(state: State, internal_address: Bytes, cursor: Any) -> Root:
    """
    Calculate the storage root.
    """
    if internal_address in state._destroyed_accounts:
        clear_destroyed_account(state, internal_address)
    storage_prefix = internal_address + b"\x00"
    dirty_storage = state._dirty_storage[-1].pop(internal_address, {}).items()
    for key, value in dirty_storage:
        if value is None:
            state._tx_stack[-1].delete(
                b"\x01" + internal_address + b"\x00" + internal_address
            )
        else:
            state._tx_stack[-1].put(
                b"\x01" + internal_address + b"\x00" + internal_address,
                rlp.encode(value),
            )
    root_node = walk(
        state,
        storage_prefix,
        b"",
        list(sorted(dirty_storage, reverse=True)),
        cursor,
    )
    write_internal_node(cursor, storage_prefix, b"", root_node)
    if root_node is None:
        return EMPTY_TRIE_ROOT
    else:
        root = encode_internal_node(root_node)
        if isinstance(root, Bytes):
            return Root(root)
        else:
            return crypto.keccak256(rlp.encode(root))


def walk(
    state: State,
    trie_prefix: Bytes,
    node_key: Bytes,
    dirty_list: List[Tuple[Bytes, Node]],
    cursor: Any,
) -> Optional[InternalNode]:
    """
    Visit the internal node at `node_key` and update all its subnodes as
    required by `dirty_list`.

    This function returns the new value of the visited node, but does not write
    it to the database.
    """
    res = cursor.get(b"\x02" + trie_prefix + node_key)
    if res is None:
        current_node = None
    else:
        current_node = decode_to_internal_node(res)
    while dirty_list and dirty_list[-1][0].startswith(node_key):
        if current_node is None:
            current_node = walk_empty(
                state, trie_prefix, node_key, dirty_list, cursor
            )
        elif isinstance(current_node, LeafNode):
            current_node = walk_leaf(
                state,
                trie_prefix,
                node_key,
                current_node,
                dirty_list,
                cursor,
            )
        elif isinstance(current_node, ExtensionNode):
            current_node = walk_extension(
                state,
                trie_prefix,
                node_key,
                current_node,
                dirty_list,
                cursor,
            )
        elif isinstance(current_node, BranchNode):
            current_node = walk_branch(
                state,
                trie_prefix,
                node_key,
                dirty_list,
                cursor,
            )
        else:
            assert False  # Invalid internal node type
    return current_node


def walk_empty(
    state: State,
    trie_prefix: Bytes,
    node_key: Bytes,
    dirty_list: List[Tuple[Bytes, Node]],
    cursor: Any,
) -> Optional[InternalNode]:
    """
    Consume the last element of `dirty_list` and create a `LeafNode` pointing
    to it at `node_key`.

    This function returns the new value of the visited node, but does not write
    it to the database.
    """
    key, value = dirty_list.pop()
    if value is not None:
        return LeafNode(
            key[len(node_key) :], make_node(state, key, value, cursor)
        )
    else:
        return None


def walk_leaf(
    state: State,
    trie_prefix: Bytes,
    node_key: Bytes,
    leaf_node: LeafNode,
    dirty_list: List[Tuple[Bytes, Node]],
    cursor: Any,
) -> Optional[InternalNode]:
    """
    Consume the last element of `dirty_list` and update the `LeafNode` at
    `node_key`, potentially turning it into `ExtensionNode` -> `BranchNode`
    -> `LeafNode`.

    This function returns the new value of the visited node, but does not write
    it to the database.
    """
    key, value = dirty_list[-1]
    if key[len(node_key) :] == leaf_node.rest_of_key:
        dirty_list.pop()
        if value is None:
            return None
        else:
            return LeafNode(
                leaf_node.rest_of_key,
                make_node(state, key, value, cursor),
            )
    else:
        prefix_length = common_prefix_length(
            leaf_node.rest_of_key, key[len(node_key) :]
        )
        prefix = leaf_node.rest_of_key[:prefix_length]
        assert (
            len(leaf_node.rest_of_key) != prefix_length
        )  # Keys must be same length
        write_internal_node(
            cursor,
            trie_prefix,
            node_key + leaf_node.rest_of_key[: prefix_length + 1],
            LeafNode(
                leaf_node.rest_of_key[prefix_length + 1 :],
                leaf_node.value,
            ),
        )
        current_node = walk_branch(
            state, trie_prefix, node_key + prefix, dirty_list, cursor
        )
        if prefix_length != 0:
            return make_extension_node(
                state,
                trie_prefix,
                node_key,
                node_key + prefix,
                current_node,
                cursor,
            )
        else:
            return current_node


def walk_extension(
    state: State,
    trie_prefix: Bytes,
    node_key: Bytes,
    extension_node: ExtensionNode,
    dirty_list: List[Tuple[Bytes, Node]],
    cursor: Any,
) -> Optional[InternalNode]:
    """
    Consume the last element of `dirty_list` and update the `ExtensionNode` at
    `node_key`, potentially turning it into `ExtensionNode` -> `BranchNode`
    -> `ExtensionNode`.

    This function returns the new value of the visited node, but does not write
    it to the database.
    """
    key, value = dirty_list[-1]
    if key[len(node_key) :].startswith(extension_node.key_segment):
        target_node = walk(
            state,
            trie_prefix,
            node_key + extension_node.key_segment,
            dirty_list,
            cursor,
        )
        return make_extension_node(
            state,
            trie_prefix,
            node_key,
            node_key + extension_node.key_segment,
            target_node,
            cursor,
        )
    prefix_length = common_prefix_length(
        extension_node.key_segment, key[len(node_key) :]
    )
    prefix = extension_node.key_segment[:prefix_length]
    if prefix_length != len(extension_node.key_segment) - 1:
        write_internal_node(
            cursor,
            trie_prefix,
            node_key + extension_node.key_segment[: prefix_length + 1],
            ExtensionNode(
                extension_node.key_segment[prefix_length + 1 :],
                extension_node.subnode,
            ),
        )
    node = walk_branch(
        state, trie_prefix, node_key + prefix, dirty_list, cursor
    )
    if prefix_length != 0:
        return make_extension_node(
            state, trie_prefix, node_key, node_key + prefix, node, cursor
        )
    else:
        return node


def walk_branch(
    state: State,
    trie_prefix: Bytes,
    node_key: Bytes,
    dirty_list: List[Tuple[Bytes, Node]],
    cursor: Any,
) -> Optional[InternalNode]:
    """
    Make a `BranchNode` at `node_key` and consume all elements of `dirty_list`
    that are under it.

    This function returns the new value of the visited node, but does not write
    it to the database.
    """
    assert dirty_list[-1][0] != node_key  # All keys must be the same length

    subnodes = []
    for i in range(16):
        subnode = walk(
            state,
            trie_prefix,
            node_key + bytes([i]),
            dirty_list,
            cursor,
        )
        write_internal_node(
            cursor, trie_prefix, node_key + bytes([i]), subnode
        )
        subnodes.append(subnode)

    number_of_subnodes = 16 - subnodes.count(None)

    if number_of_subnodes == 0:
        return None
    elif number_of_subnodes == 1:
        for i in range(16):
            if subnodes[i] is not None:
                subnode_index = i
                subnode = subnodes[i]
                break
        return make_extension_node(
            state,
            trie_prefix,
            node_key,
            node_key + bytes([subnode_index]),
            subnode,
            cursor,
        )
    else:
        encoded_subnodes = [
            encode_internal_node(subnode) for subnode in subnodes
        ]
        return BranchNode(encoded_subnodes, b"")


def make_extension_node(
    state: State,
    trie_prefix: Bytes,
    node_key: Bytes,
    target_key: Bytes,
    target_node: Optional[InternalNode],
    cursor: Any,
) -> Optional[InternalNode]:
    """
    Make an extension node at `node_key` pointing at `target_key`. This
    function will correctly replace `ExtensionNode -> LeafNode` with `LeafNode`
    and `ExtensionNode -> ExtensionNode` with `ExtensionNode`.

    This function returns the new value of the visited node, but does not write
    it to the database.
    """
    assert node_key != target_key
    if target_node is None:
        write_internal_node(cursor, trie_prefix, target_key, None)
        return None
    elif isinstance(target_node, LeafNode):
        write_internal_node(cursor, trie_prefix, target_key, None)
        return LeafNode(
            target_key[len(node_key) :] + target_node.rest_of_key,
            target_node.value,
        )
    elif isinstance(target_node, ExtensionNode):
        write_internal_node(cursor, trie_prefix, target_key, None)
        return ExtensionNode(
            target_key[len(node_key) :] + target_node.key_segment,
            target_node.subnode,
        )
    elif isinstance(target_node, BranchNode):
        write_internal_node(cursor, trie_prefix, target_key, target_node)
        return ExtensionNode(
            target_key[len(node_key) :], encode_internal_node(target_node)
        )
    else:
        assert False  # Invalid internal node type
