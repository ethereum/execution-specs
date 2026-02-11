"""
State.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

The state contains all information that is preserved between transactions.

It consists of a main account trie and storage tries for each contract.

There is a distinction between an account that does not exist and
`EMPTY_ACCOUNT`.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ethereum_types.bytes import Bytes32
from ethereum_types.numeric import U256

from ethereum.state import Account, Address, InternalNode, Root

from .trie import EMPTY_TRIE_ROOT, Trie, copy_trie, root, trie_get, trie_set


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
    ) -> Tuple[Root, List[InternalNode]]:
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


def apply_changes_to_state(
    state: State,
    account_changes: Dict[Address, Optional[Account]],
    storage_changes: Dict[Address, Dict[Bytes32, U256]],
) -> None:
    """
    Apply block-level diffs to the ``State`` for the next block.

    Parameters
    ----------
    state :
        The state to update.
    account_changes :
        Account changes to apply.
    storage_changes :
        Storage changes to apply.

    """
    for address, account in account_changes.items():
        trie_set(state._main_trie, address, account)

    for address, slots in storage_changes.items():
        trie = state._storage_tries.get(address)
        if trie is None:
            trie = Trie(secured=True, default=U256(0))
            state._storage_tries[address] = trie
        for key, value in slots.items():
            trie_set(trie, key, value)
        if trie._data == {}:
            del state._storage_tries[address]


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
