"""
Optimized State
^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This module contains functions can be monkey patched into the fork's `state`
module to use an optimized database backed state.
"""
import logging
from dataclasses import dataclass
from importlib import import_module
from typing import Any, ClassVar, Dict, List, Optional, Set, cast

try:
    import rust_pyspec_glue
except ImportError as e:
    # Add a message, but keep it an ImportError.
    raise e from Exception(
        "Install with `pip install 'ethereum[optimized]'` to enable this "
        "package"
    )

from ethereum.base_types import U256, Bytes, Bytes20, Uint
from ethereum.crypto.hash import Hash32

Address = Bytes20
Root = Hash32
Account_ = Any


class UnmodifiedType:
    """
    Sentinel type to represent a value that hasn't been modified.
    """

    pass


Unmodified = UnmodifiedType()


def get_optimized_state_patches(fork: str) -> Dict[str, Any]:
    """
    Get a dictionary of functions/objects to be monkey patched into the state
    to make it optimized.
    """
    mod = cast(Any, import_module("ethereum." + fork + ".fork_types"))
    Account = mod.Account

    @dataclass
    class State:
        """
        The State, backed by a LMDB database.

        When created with `State()` store the db in a temporary directory. When
        created with `State(path)` open or create the db located at `path`.
        """

        default_path: ClassVar[Optional[str]] = None

        db: Any
        dirty_accounts: Dict[Address, Optional[Account_]]
        dirty_storage: Dict[Address, Dict[Bytes, U256]]
        destroyed_accounts: Set[Address]
        tx_restore_points: List[int]
        journal: List[Any]
        created_accounts: Set[Address]

        def __init__(self, path: Optional[str] = None) -> None:
            logging.info("using optimized state db at %s", path)

            if path is None:
                path = State.default_path

            self.db = rust_pyspec_glue.DB(path)
            self.dirty_accounts = {}
            self.dirty_storage = {}
            self.destroyed_accounts = set()
            self.tx_restore_points = []
            self.journal = []
            self.created_accounts = set()
            self.db.begin_mutable()

        def __eq__(self, other: object) -> bool:
            """
            Test for equality by comparing state roots.
            """
            if not isinstance(other, State):
                return NotImplemented
            return state_root(self) == state_root(other)

        def __enter__(self) -> "State":
            """Support with statements"""
            return self

        def __exit__(self, *args: Any) -> None:
            """Support with statements"""
            close_state(self)

    def close_state(state: State) -> None:
        """Close a state, releasing all resources it holds"""
        state.db.close()
        state.db = None
        del state.dirty_accounts
        del state.dirty_storage
        del state.destroyed_accounts
        del state.journal
        del state.created_accounts

    def get_metadata(state: State, key: Bytes) -> Optional[Bytes]:
        """Get a piece of metadata"""
        return state.db.get_metadata(key)

    def set_metadata(state: State, key: Bytes, value: Bytes) -> None:
        """Set a piece of metadata"""
        return state.db.set_metadata(key, value)

    def begin_db_transaction(state: State) -> None:
        """
        Start a database transaction. A transaction is automatically started
        when a `State` is created. Nesting of DB transactions is not supported
        (unlike non-db transactions).

        No operations are supported when not in a transaction.
        """
        state.db.begin_mutable()
        state.tx_restore_points = []
        state.journal = []

    def commit_db_transaction(state: State) -> None:
        """
        Commit the current database transaction.
        """
        if state.tx_restore_points:
            raise Exception("In a non-db transaction")
        flush(state)
        state.db.commit_mutable()

    def state_root(state: State) -> Root:
        """
        See `state`.
        """
        if state.tx_restore_points:
            raise Exception("In a non-db transaction")
        flush(state)
        return state.db.state_root()

    def storage_root(state: State, address: Address) -> Root:
        """
        See `state`.
        """
        if state.tx_restore_points:
            raise Exception("In a non-db transaction")
        flush(state)
        return state.db.storage_root(address)

    def flush(state: State) -> None:
        """
        Send everything in the internal caches to the Rust layer.
        """
        if state.tx_restore_points:
            raise Exception("In a non-db transaction")
        for address in state.destroyed_accounts:
            state.db.destroy_storage(address)
        for address, account in state.dirty_accounts.items():
            state.db.set_account(address, account)
        for address, storage in state.dirty_storage.items():
            for key, value in storage.items():
                state.db.set_storage(address, key, value)
        state.destroyed_accounts = set()
        state.dirty_accounts.clear()
        state.dirty_storage.clear()

    def rollback_db_transaction(state: State) -> None:
        """
        Rollback the current database transaction.
        """
        if state.tx_restore_points:
            raise Exception("In a non-db transaction")
        state.db.rollback_mutable()
        state.dirty_accounts.clear()
        state.dirty_storage.clear()
        state.destroyed_accounts = set()

    def begin_transaction(state: State) -> None:
        """
        See `state`.
        """
        if not state.tx_restore_points:
            flush(state)
        state.tx_restore_points.append(len(state.journal))

    def commit_transaction(state: State) -> None:
        """
        See `state`.
        """
        state.tx_restore_points.pop()
        if not state.tx_restore_points:
            state.journal.clear()
            state.created_accounts.clear()
            flush(state)

    def rollback_transaction(state: State) -> None:
        """
        See `state`.
        """
        restore_point = state.tx_restore_points.pop()
        while len(state.journal) > restore_point:
            item = state.journal.pop()
            if len(item) == 3:
                # Revert a storage key write
                if item[2] is Unmodified:
                    del state.dirty_storage[item[0]][item[1]]
                else:
                    state.dirty_storage[item[0]][item[1]] = item[2]
            elif type(item[1]) is dict:
                # Restore storage that was destroyed by `destroy_storage()`
                state.destroyed_accounts.remove(item[0])
                state.dirty_storage[item[0]] = item[1]
            else:
                # Revert a change to an account
                if item[1] is Unmodified:
                    del state.dirty_accounts[item[0]]
                else:
                    state.dirty_accounts[item[0]] = item[1]

        if not state.tx_restore_points:
            state.created_accounts.clear()

    def get_storage(state: State, address: Address, key: Bytes) -> U256:
        """
        See `state`.
        """
        if (
            address in state.dirty_storage
            and key in state.dirty_storage[address]
        ):
            return state.dirty_storage[address][key]

        if address in state.destroyed_accounts:
            return U256(0)
        else:
            return U256(state.db.get_storage(address, key))

    def get_storage_original(
        state: State, address: Address, key: Bytes
    ) -> U256:
        """
        See `state`.
        """
        if address in state.created_accounts:
            return U256(0)
        else:
            return U256(state.db.get_storage(address, key))

    def set_storage(
        state: State, address: Address, key: Bytes, value: U256
    ) -> None:
        """
        See `state`.
        """
        if address not in state.dirty_accounts:
            state.dirty_accounts[address] = get_account_optional(
                state, address
            )
        if address not in state.dirty_storage:
            state.dirty_storage[address] = {}
        if key not in state.dirty_storage[address]:
            state.journal.append((address, key, Unmodified))
        else:
            state.journal.append(
                (address, key, state.dirty_storage[address][key])
            )
        state.dirty_storage[address][key] = value

    def get_account_optional(
        state: State, address: Address
    ) -> Optional[Account_]:
        """
        See `state`.
        """
        if address in state.dirty_accounts:
            return state.dirty_accounts[address]
        account = state.db.get_account_optional(address)
        if account is not None:
            return Account(Uint(account[0]), U256(account[1]), account[2])
        else:
            return None

    def set_account(
        state: State, address: Address, account: Optional[Account_]
    ) -> None:
        """
        See `state`.
        """
        if address not in state.dirty_accounts:
            state.journal.append((address, Unmodified))
        if address in state.dirty_accounts:
            state.journal.append((address, state.dirty_accounts[address]))
        state.dirty_accounts[address] = account

    def destroy_storage(state: State, address: Address) -> None:
        """
        See `state`.
        """
        state.journal.append((address, state.dirty_storage.pop(address, {})))
        state.destroyed_accounts.add(address)
        set_account(state, address, get_account_optional(state, address))

    def mark_account_created(state: State, address: Address) -> None:
        """
        See `state`.
        """
        state.created_accounts.add(address)

    return locals()
