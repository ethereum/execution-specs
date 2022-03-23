"""
Optimized State
^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This module contains functions can be monkey patched into
`ethereum.tangerine_whistle.state` to use an optimized database backed state.
"""
import logging
from dataclasses import dataclass
from tempfile import TemporaryDirectory
from typing import Any, ClassVar, Dict, List, Optional, Set, Tuple

from ethereum import rlp
from ethereum.base_types import U256, Bytes, Uint
from ethereum.crypto.hash import keccak256
from ethereum.tangerine_whistle.eth_types import (
    EMPTY_ACCOUNT,
    Account,
    Address,
    Root,
    encode_account,
)
from ethereum.tangerine_whistle.trie import (
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

try:
    import lmdb
except ImportError as e:
    # Add a message, but keep it an ImportError.
    raise e from Exception(
        "Install with `pip install 'ethereum[optimized]'` to enable this "
        "package"
    )

# 0x0 : Metadata
# 0x1 : Accounts and storage
# 0x2 : Internal Nodes

DB_VERSION = b"1"


@dataclass
class State:
    """
    The State, backed by a LMDB database.

    When created with `State()` store the db in a temporary directory. When
    created with `State(path)` open or create the db located at `path`.
    """

    default_path: ClassVar[Optional[str]] = None

    _db: Any
    _current_tx: Any
    _tx_stack: List[Any]
    _dirty_accounts: List[Dict[Address, Optional[Account]]]
    _dirty_storage: List[Dict[Address, Dict[Bytes, Optional[U256]]]]
    _destroyed_accounts: List[Set[Address]]
    _root: Root

    def __init__(self, path: Optional[str] = None) -> None:
        if path is None:
            path = State.default_path

            if path is None:
                # Reference kept so directory won't be deleted until State is
                self._tempdir = TemporaryDirectory()
                path = self._tempdir.name

        logging.info("using optimized state db at %s", path)

        self._db = lmdb.open(path, map_size=2 ** 40)
        self._current_tx = None
        self._tx_stack = []
        self._dirty_accounts = [{}]
        self._dirty_storage = [{}]
        self._destroyed_accounts = [set()]
        begin_db_transaction(self)
        version = get_metadata(self, b"version")
        if version is None:
            if self._db.stat()["entries"] != 0:
                raise Exception("State DB is missing version")
            else:
                set_metadata(self, b"version", DB_VERSION)
        elif version != DB_VERSION:
            raise Exception(
                f"State DB version mismatch"
                f" (expected: {DB_VERSION.decode('ascii')},"
                f" got: {version.decode('ascii')})"
            )

    def __eq__(self, other: object) -> bool:
        """
        Test for equality by comparing state roots.
        """
        if not isinstance(other, State):
            return NotImplemented
        return state_root(self) == state_root(other)

    def __enter__(self) -> "State":
        """Support with statements"""
        # This is actually noop, but call it anyway for correctness
        self._db.__enter__()
        return self

    def __exit__(self, *args: Any) -> bool:
        """Support with statements"""
        return self._db.__exit__(*args)


def close_state(state: State) -> None:
    """Close a state, releasing all resources it holds"""
    state._db.close()
    del state._current_tx
    del state._tx_stack
    del state._dirty_accounts
    del state._dirty_storage
    del state._destroyed_accounts


def get_metadata(state: State, key: Bytes) -> Optional[Bytes]:
    """Get a piece of metadata"""
    return state._current_tx.get(b"\x00" + key)


def set_metadata(state: State, key: Bytes, value: Bytes) -> None:
    """Set a piece of metadata"""
    return state._current_tx.put(b"\x00" + key, value)


def begin_db_transaction(state: State) -> None:
    """
    Start a database transaction. A transaction is automatically started when a
    `State` is created and the entire stack of transactions must be committed
    for any permanent changes to be made to the database.

    Database transactions are more expensive than normal transactions, but the
    state root can be calculated while in them.

    No operations are supported when not in a transaction.
    """
    if state._tx_stack == []:
        state._tx_stack.append(lmdb.Transaction(state._db, write=True))
    elif state._tx_stack[-1] is None:
        raise Exception(
            "Non db transactions cannot have db transactions as children"
        )
    else:
        state_root(state)
        state._tx_stack.append(
            lmdb.Transaction(state._db, parent=state._tx_stack[-1], write=True)
        )
    state._current_tx = state._tx_stack[-1]


def commit_db_transaction(state: State) -> None:
    """
    Commit the current database transaction.
    """
    if state._tx_stack[-1] is None:
        raise Exception("Current transaction is not a db transaction")
    state_root(state)
    state._tx_stack.pop().commit()
    if state._tx_stack != []:
        state._current_tx = state._tx_stack[-1]
    else:
        state._current_tx = None


def rollback_db_transaction(state: State) -> None:
    """
    Rollback the current database transaction.
    """
    if state._tx_stack[-1] is None:
        raise Exception("Current transaction is not a db transaction")
    state._tx_stack.pop().abort()
    state._dirty_accounts = [{}]
    state._dirty_storage = [{}]
    state._destroyed_accounts = [set()]
    if state._tx_stack != []:
        state._current_tx = state._tx_stack[-1]
    else:
        state._current_tx = None


def begin_transaction(state: State) -> None:
    """
    See `ethereum.tangerine_whistle.state`.
    """
    if state._tx_stack == []:
        raise Exception("First transaction must be a db transaction")
    state._tx_stack.append(None)
    state._dirty_accounts.append({})
    state._dirty_storage.append({})
    state._destroyed_accounts.append(set())


def commit_transaction(state: State) -> None:
    """
    See `ethereum.tangerine_whistle.state`.
    """
    if state._tx_stack[-1] is not None:
        raise Exception("Current transaction is a db transaction")
    for (address, account) in state._dirty_accounts.pop().items():
        state._dirty_accounts[-1][address] = account
    state._destroyed_accounts[-2] |= state._destroyed_accounts[-1]
    for address in state._destroyed_accounts.pop():
        state._dirty_storage[-2].pop(address)
    for (address, cache) in state._dirty_storage.pop().items():
        if address not in state._dirty_storage[-1]:
            state._dirty_storage[-1][address] = {}
        for (key, value) in cache.items():
            state._dirty_storage[-1][address][key] = value
    state._tx_stack.pop()


def rollback_transaction(state: State) -> None:
    """
    See `ethereum.tangerine_whistle.state`.
    """
    if state._tx_stack[-1] is not None:
        raise Exception("Current transaction is a db transaction")
    state._tx_stack.pop()
    state._dirty_accounts.pop()
    state._dirty_storage.pop()
    state._destroyed_accounts.pop()


def get_internal_key(key: Bytes) -> Bytes:
    """
    Convert a key to the form used internally inside the trie.
    """
    return bytes_to_nibble_list(keccak256(key))


def get_storage(state: State, address: Address, key: Bytes) -> U256:
    """
    See `ethereum.tangerine_whistle.state`.
    """
    for i in range(len(state._tx_stack) - 1, -1, -1):
        if address in state._dirty_storage[i]:
            if key in state._dirty_storage[i][address]:
                cached_res = state._dirty_storage[i][address][key]
                if cached_res is None:
                    return U256(0)
                else:
                    return cached_res
            if key in state._destroyed_accounts[i]:
                # Higher levels refer to the account prior to destruction
                return U256(0)
    res = state._current_tx.get(b"\x01" + address + b"\x00" + key)
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
    See `ethereum.tangerine_whistle.state`.
    """
    if address not in state._dirty_accounts[-1]:
        state._dirty_accounts[-1][address] = get_account_optional(
            state, address
        )
    if address not in state._dirty_storage[-1]:
        state._dirty_storage[-1][address] = {}
    if value == 0:
        state._dirty_storage[-1][address][key] = None
    else:
        state._dirty_storage[-1][address][key] = value


def get_account_optional(state: State, address: Address) -> Optional[Account]:
    """
    See `ethereum.tangerine_whistle.state`.
    """
    for cache in reversed(state._dirty_accounts):
        if address in cache:
            return cache[address]
    internal_address = get_internal_key(address)
    res = state._current_tx.get(b"\x01" + internal_address)
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
    See `ethereum.tangerine_whistle.state`.
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
    See `ethereum.tangerine_whistle.state`.
    """
    if account is None:
        state._dirty_accounts[-1][address] = None
    else:
        state._dirty_accounts[-1][address] = account


def destroy_account(state: State, address: Address) -> None:
    """
    See `ethereum.tangerine_whistle.state`.
    """
    state._destroyed_accounts[-1].add(address)
    state._dirty_storage[-1].pop(address, None)
    state._dirty_accounts[-1][address] = None


def clear_destroyed_account(state: State, address: Bytes) -> None:
    """
    Remove every storage key associated to a destroyed account from the
    database.
    """
    internal_address = get_internal_key(address)
    cursor = state._current_tx.cursor()
    cursor.set_range(b"\x01" + address + b"\x00")
    while cursor.key().startswith(b"\x01" + address):
        cursor.delete()
    cursor.set_range(b"\x02" + internal_address + b"\x00")
    while cursor.key().startswith(b"\x02" + internal_address):
        cursor.delete()


def make_node(
    state: State, node_key: Bytes, value: Node, cursor: Any
) -> rlp.RLP:
    """
    Given a node, get its `RLP` representation. This function calculates the
    storage root if the node is an `Account`.
    """
    if isinstance(value, Account):
        res = cursor.get(b"\x02" + node_key + b"\x00")
        if res is None:
            account_storage_root = EMPTY_TRIE_ROOT
        else:
            account_storage_root = keccak256(res)
        return encode_account(value, account_storage_root)
    elif isinstance(value, Bytes):
        return value
    else:
        assert value is not None
        return rlp.encode(value)


def write_internal_node(
    cursor: Any,
    trie_prefix: Bytes,
    node_key: Bytes,
    node: Optional[InternalNode],
) -> None:
    """
    Write an internal node into the database.
    """
    if node is None:
        if cursor.set_key(b"\x02" + trie_prefix + node_key):
            cursor.delete()
    else:
        cursor.put(
            b"\x02" + trie_prefix + node_key,
            encode_internal_node_nohash(node),
        )


def state_root(
    state: State,
) -> Root:
    """
    Calculate the state root.
    """
    if state._current_tx is None:
        raise Exception("Cannot compute state root inside non db transaction")
    for address, account in state._dirty_accounts[-1].items():
        internal_address = get_internal_key(address)
        if account is None:
            state._current_tx.delete(b"\x01" + internal_address)
        elif isinstance(account, Bytes):  # Testing only
            state._current_tx.put(
                b"\x01" + internal_address,
                account,
            )
        elif isinstance(account, Account):
            state._current_tx.put(
                b"\x01" + internal_address,
                rlp.encode([account.nonce, account.balance, account.code]),
            )
        else:
            raise Exception(
                f"Invalid object of type {type(account)} stored in state"
            )
    for address in state._destroyed_accounts[-1]:
        clear_destroyed_account(state, address)
    state._destroyed_accounts[-1] = set()
    for address in list(state._dirty_storage[-1]):
        storage_root(state, address)
    dirty_list: List[Tuple[Bytes, Node]] = list(
        sorted(
            (
                (get_internal_key(address), account)
                for address, account in state._dirty_accounts[-1].items()
            ),
            reverse=True,
        )
    )
    root_node = walk(
        state,
        b"",
        b"",
        dirty_list,
        state._current_tx.cursor(),
    )
    write_internal_node(state._current_tx.cursor(), b"", b"", root_node)
    state._dirty_accounts[-1] = {}
    if root_node is None:
        return EMPTY_TRIE_ROOT
    else:
        root = encode_internal_node(root_node)
        if isinstance(root, Bytes):
            return Root(root)
        else:
            return keccak256(rlp.encode(root))


def storage_root(state: State, address: Address) -> Root:
    """
    Calculate the storage root.
    """
    if state._current_tx is None:
        raise Exception(
            "Cannot compute storage root inside non db transaction"
        )
    return _storage_root(state, address, state._current_tx.cursor())


def _storage_root(state: State, address: Address, cursor: Any) -> Root:
    """
    Calculate the storage root.
    """
    dirty_storage = state._dirty_storage[-1].pop(address, {}).items()
    for key, value in dirty_storage:
        if value is None:
            state._current_tx.delete(b"\x01" + address + b"\x00" + key)
        else:
            state._current_tx.put(
                b"\x01" + address + b"\x00" + key,
                rlp.encode(value),
            )

    internal_address = get_internal_key(address)
    storage_prefix = internal_address + b"\x00"
    dirty_list: List[Tuple[Bytes, Node]] = list(
        sorted(
            (
                (get_internal_key(key), account)
                for key, account in dirty_storage
            ),
            reverse=True,
        )
    )
    root_node = walk(
        state,
        storage_prefix,
        b"",
        dirty_list,
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
            return keccak256(rlp.encode(root))


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
                current_node,
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
        new_leaf_node = LeafNode(
            leaf_node.rest_of_key[prefix_length + 1 :],
            leaf_node.value,
        )
        write_internal_node(
            cursor,
            trie_prefix,
            node_key + leaf_node.rest_of_key[: prefix_length + 1],
            LeafNode(
                leaf_node.rest_of_key[prefix_length + 1 :],
                leaf_node.value,
            ),
        )
        current_node = split_branch(
            state,
            trie_prefix,
            node_key + prefix,
            leaf_node.rest_of_key[prefix_length],
            encode_internal_node(new_leaf_node),
            dirty_list,
            cursor,
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
        new_extension_node = ExtensionNode(
            extension_node.key_segment[prefix_length + 1 :],
            extension_node.subnode,
        )
        write_internal_node(
            cursor,
            trie_prefix,
            node_key + extension_node.key_segment[: prefix_length + 1],
            new_extension_node,
        )
        encoded_new_extension_node = encode_internal_node(new_extension_node)
    else:
        encoded_new_extension_node = extension_node.subnode
    node = split_branch(
        state,
        trie_prefix,
        node_key + prefix,
        extension_node.key_segment[prefix_length],
        encoded_new_extension_node,
        dirty_list,
        cursor,
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
    current_node: BranchNode,
    dirty_list: List[Tuple[Bytes, Node]],
    cursor: Any,
) -> Optional[InternalNode]:
    """
    Consume the last element of `dirty_list` and update the `BranchNode` at
    `node_key`, potentially turning it into `ExtensionNode` or a `LeafNode`.

    This function returns the new value of the visited node, but does not write
    it to the database.
    """
    assert dirty_list[-1][0] != node_key  # All keys must be the same length

    # The copy here is probably unnecessary, but the optimization isn't worth
    # the risk.
    encoded_subnodes = current_node.subnodes[:]
    if dirty_list[-1][0].startswith(node_key):
        for i in range(16):
            if (
                dirty_list
                and dirty_list[-1][0].startswith(node_key)
                and dirty_list[-1][0][len(node_key)] == i
            ):
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
                encoded_subnodes[i] = encode_internal_node(subnode)

    number_of_subnodes = 16 - encoded_subnodes.count(b"")

    if number_of_subnodes == 0:
        return None
    elif number_of_subnodes == 1:
        for i in range(16):
            if encoded_subnodes[i] != b"":
                subnode_index = i
                break
        subnode = decode_to_internal_node(
            cursor.get(
                b"\x02" + trie_prefix + node_key + bytes([subnode_index])
            )
        )
        return make_extension_node(
            state,
            trie_prefix,
            node_key,
            node_key + bytes([subnode_index]),
            subnode,
            cursor,
        )
    else:
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


def split_branch(
    state: State,
    trie_prefix: Bytes,
    node_key: Bytes,
    key: int,
    encoded_subnode: rlp.RLP,
    dirty_list: List[Tuple[Bytes, Node]],
    cursor: Any,
) -> Optional[InternalNode]:
    """
    Make a branch node with `encoded_subnode` as its only child and then
    consume all `dirty_list` elements under it.

    This function takes a `encoded_node` to avoid a database read in some
    situations.

    This function returns the new value of the visited node, but does not write
    it to the database.
    """
    encoded_subnodes: List[rlp.RLP] = [b""] * 16
    encoded_subnodes[key] = encoded_subnode
    return walk_branch(
        state,
        trie_prefix,
        node_key,
        BranchNode(encoded_subnodes, b""),
        dirty_list,
        cursor,
    )
