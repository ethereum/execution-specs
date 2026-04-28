"""
Shared state types and the `PreState` protocol used by the state transition
function.

The `PreState` protocol specifies the operations that any pre-execution state
provider must support, allowing multiple backing implementations (in-memory
`dict`, on-disk database, witness, etc.).

The `State` class is the in-memory implementation of `PreState`. It consists
of a main account trie and storage tries for each contract.

There is a distinction between an account that does not exist and
`EMPTY_ACCOUNT`.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Tuple

from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.merkle_patricia_trie import (
    EMPTY_TRIE_ROOT,
    InternalNode,
    Trie,
    copy_trie,
    root,
    trie_get,
    trie_set,
)

Address = Bytes20
Root = Hash32

EMPTY_CODE_HASH = keccak256(b"")


@slotted_freezable
@dataclass
class Account:
    """
    State associated with an address.
    """

    nonce: Uint
    balance: U256
    code_hash: Hash32


EMPTY_ACCOUNT = Account(
    nonce=Uint(0),
    balance=U256(0),
    code_hash=EMPTY_CODE_HASH,
)


@dataclass
class BlockDiff:
    """
    State changes produced by executing a block.
    """

    account_changes: Dict[Address, Optional[Account]]
    """Per-address account diffs produced by execution."""

    storage_changes: Dict[Address, Dict[Bytes32, U256]]
    """Per-address storage diffs produced by execution."""

    code_changes: Dict[Hash32, Bytes]
    """New bytecodes (keyed by code hash) introduced by execution."""


class PreState(Protocol):
    """
    Protocol for providing pre-execution state.

    Specify the operations that any pre-state provider (dict, database,
    witness, etc.) must support for the EELS state transition.
    """

    def get_account_optional(self, address: Address) -> Optional[Account]:
        """
        Get the account at an address.

        Return ``None`` if there is no account at the address.
        """
        ...

    def get_storage(self, address: Address, key: Bytes32) -> U256:
        """
        Get a storage value.

        Return ``U256(0)`` if the key has not been set.
        """
        ...

    def get_code(self, code_hash: Hash32) -> Bytes:
        """
        Get the bytecode for a given code hash.

        Return ``b""`` for ``EMPTY_CODE_HASH``.
        """
        ...

    def account_has_storage(self, address: Address) -> bool:
        """
        Check whether an account has any storage.

        Only needed for EIP-7610.
        """
        ...

    def compute_state_root_and_trie_changes(
        self,
        account_changes: Dict[Address, Optional[Account]],
        storage_changes: Dict[Address, Dict[Bytes32, U256]],
    ) -> Tuple[Root, List["InternalNode"]]:
        """
        Compute the state root after applying changes to the pre-state.

        Return the new state root together with the internal trie nodes
        that were created or modified.
        """
        ...


@dataclass
class State:
    """
    Contains all information that is preserved between transactions.
    """

    _main_trie: Trie[Address, Optional[Account]] = field(
        default_factory=lambda: Trie(secured=True, default=None)
    )
    _storage_tries: Dict[Address, Trie[Bytes32, U256]] = field(
        default_factory=dict
    )
    _code_store: Dict[Hash32, Bytes] = field(
        default_factory=dict, compare=False
    )

    def get_code(self, code_hash: Hash32) -> Bytes:
        """
        Get the bytecode for a given code hash.

        Return ``b""`` for ``EMPTY_CODE_HASH``.
        """
        if code_hash == EMPTY_CODE_HASH:
            return b""
        return self._code_store[code_hash]

    def get_account_optional(self, address: Address) -> Optional[Account]:
        """
        Get the account at an address.

        Return ``None`` if there is no account at the address.
        """
        return trie_get(self._main_trie, address)

    def get_storage(self, address: Address, key: Bytes32) -> U256:
        """
        Get a storage value.

        Return ``U256(0)`` if the key has not been set.
        """
        trie = self._storage_tries.get(address)
        if trie is None:
            return U256(0)

        value = trie_get(trie, key)

        assert isinstance(value, U256)
        return value

    def account_has_storage(self, address: Address) -> bool:
        """
        Check whether an account has any storage.

        Only needed for EIP-7610.
        """
        return address in self._storage_tries

    def compute_state_root_and_trie_changes(
        self,
        account_changes: Dict[Address, Optional[Account]],
        storage_changes: Dict[Address, Dict[Bytes32, U256]],
    ) -> Tuple[Root, List["InternalNode"]]:
        """
        Compute the state root after applying changes to the pre-state.

        Return the new state root together with the internal trie nodes
        that were created or modified.
        """
        main_trie = copy_trie(self._main_trie)
        storage_tries = {
            k: copy_trie(v) for k, v in self._storage_tries.items()
        }

        for address, account in account_changes.items():
            trie_set(main_trie, address, account)

        for address, slots in storage_changes.items():
            trie = storage_tries.get(address)
            if trie is None:
                trie = Trie(secured=True, default=U256(0))
                storage_tries[address] = trie
            for key, value in slots.items():
                trie_set(trie, key, value)
            if trie._data == {}:
                del storage_tries[address]

        def get_storage_root(addr: Address) -> Root:
            if addr in storage_tries:
                return root(storage_tries[addr])
            return EMPTY_TRIE_ROOT

        state_root_value = root(main_trie, get_storage_root=get_storage_root)

        return state_root_value, []


def close_state(state: State) -> None:
    """
    Free resources held by the state. Used by optimized implementations to
    release file descriptors.
    """
    del state._main_trie
    del state._storage_tries
    del state._code_store


def apply_changes_to_state(state: State, diff: BlockDiff) -> None:
    """
    Apply block-level diff to the ``State`` for the next block.

    Parameters
    ----------
    state :
        The state to update.
    diff :
        Account, storage, and code changes to apply.

    """
    for address, account in diff.account_changes.items():
        trie_set(state._main_trie, address, account)

    for address, slots in diff.storage_changes.items():
        trie = state._storage_tries.get(address)
        if trie is None:
            trie = Trie(secured=True, default=U256(0))
            state._storage_tries[address] = trie
        for key, value in slots.items():
            trie_set(trie, key, value)
        if trie._data == {}:
            del state._storage_tries[address]

    state._code_store.update(diff.code_changes)


def store_code(state: State, code: Bytes) -> Hash32:
    """
    Store bytecode in ``State``.
    """
    code_hash = keccak256(code)
    if code_hash != EMPTY_CODE_HASH:
        state._code_store[code_hash] = code
    return code_hash


def set_account(
    state: State,
    address: Address,
    account: Optional[Account],
) -> None:
    """
    Set an account in a ``State``.

    Setting to ``None`` deletes the account.
    """
    trie_set(state._main_trie, address, account)


def set_storage(
    state: State,
    address: Address,
    key: Bytes32,
    value: U256,
) -> None:
    """
    Set a storage value in a ``State``.

    Setting to ``U256(0)`` deletes the key.
    """
    assert trie_get(state._main_trie, address) is not None

    trie = state._storage_tries.get(address)
    if trie is None:
        trie = Trie(secured=True, default=U256(0))
        state._storage_tries[address] = trie
    trie_set(trie, key, value)
    if trie._data == {}:
        del state._storage_tries[address]


def state_root(state: State) -> Root:
    """
    Compute the state root of the current state.
    """
    root_value, _ = state.compute_state_root_and_trie_changes({}, {})
    return root_value
