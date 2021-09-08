"""
Optimized State
^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

This module contains functions can be monkey patched into
`ethereum.frontier.state` to make it use the optimized trie.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, cast

import ethereum.frontier.state
from ethereum.base_types import U256, Bytes
from ethereum.frontier.eth_types import Account, Address
from ethereum.frontier.state import state_root

from .trie import Trie, get_internal_key, trie_get, trie_set


@dataclass
class State:
    """
    Contains all information that is preserved between transactions.
    """

    _main_trie: Trie[Optional[Account]] = field(
        default_factory=lambda: Trie(secured=True, default=None)
    )
    _storage_tries: Dict[Address, Trie[U256]] = field(default_factory=dict)

    def __eq__(self, other: object) -> bool:
        """
        Test for equality by comparing state roots.
        """
        if type(self) != type(other):
            return NotImplemented
        return state_root(
            cast(ethereum.frontier.state.State, self)
        ) == state_root(cast(ethereum.frontier.state.State, other))


def set_storage(
    state: State, address: Address, key: Bytes, value: U256
) -> None:
    """
    Set a value at a storage key on an account. Setting to `U256(0)` deletes
    the key.

    Parameters
    ----------
    state: `State`
        The state
    address : `Address`
        Address of the account.
    key : `Bytes`
        Key to set.
    value : `U256`
        Value to set at the key.
    """
    assert trie_get(state._main_trie, address) is not None
    internal_address = get_internal_key(state._main_trie, address)
    trie = state._storage_tries.get(internal_address)
    if trie is None:
        trie = Trie(secured=True, default=U256(0))
        state._storage_tries[internal_address] = trie
    trie_set(trie, key, value)
    state._main_trie._dirty_set.add(internal_address)
    if trie._data == {}:
        del state._storage_tries[internal_address]


def get_storage(state: State, address: Address, key: Bytes) -> U256:
    """
    Get a value at a storage key on an account. Returns `U256(0)` if the
    storage key has not been set previously.

    Parameters
    ----------
    state: `State`
        The state
    address : `Address`
        Address of the account.
    key : `Bytes`
        Key to lookup.

    Returns
    -------
    value : `U256`
        Value at the key.
    """
    internal_address = get_internal_key(state._main_trie, address)
    trie = state._storage_tries.get(internal_address)
    if trie is None:
        return U256(0)

    value = trie_get(trie, key)

    assert isinstance(value, U256)
    return value
