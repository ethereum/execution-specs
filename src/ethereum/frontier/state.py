"""
State
^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

The state contains all information that is preserved between transactions.

It consists of a main account trie and storage tries for each contract.
"""
from dataclasses import dataclass, field
from typing import Callable, Dict

from ethereum.base_types import U256, Bytes, modify

from .eth_types import EMPTY_ACCOUNT, Account, Address, Root
from .trie import EMPTY_TRIE_ROOT, Trie, root, trie_get, trie_set


@dataclass
class State:
    """
    Contains all information that is preserved between transactions.
    """

    _main_trie: Trie[Account] = field(
        default_factory=lambda: Trie(secured=True, default=EMPTY_ACCOUNT)
    )
    _storage_tries: Dict[Address, Trie[U256]] = field(default_factory=dict)


def get_account(state: State, address: Address) -> Account:
    """
    Get the `Account` object at an address. Returns `EMPTY_ACCOUNT` if there
    is no account at the address.

    Parameters
    ----------
    state: `State`
        The state
    address : `Address`
        Address to lookup.

    Returns
    -------
    account : `Account`
        Account at address.
    """
    account = trie_get(state._main_trie, address)
    assert isinstance(account, Account)
    return account


def set_account(state: State, address: Address, account: Account) -> None:
    """
    Set the `Account` object at an address. Setting to `EMPTY_ACCOUNT` deletes
    the account (but not its storage, see `destroy_account()`).

    Parameters
    ----------
    state: `State`
        The state
    address : `Address`
        Address to set.
    account : `Account`
        Account to set at address.
    """
    trie_set(state._main_trie, address, account)


def destroy_account(state: State, address: Address) -> None:
    """
    Completely remove the account at `address` and all of its storage.

    This function is made available exclusively for the `SELFDESTRUCT`
    opcode. It is expected that `SELFDESTRUCT` will be disabled in a future
    hardfork and this function will be removed.

    Parameters
    ----------
    state: `State`
        The state
    address : `Address`
        Address of account to destroy.
    """
    del state._storage_tries[address]
    set_account(state, address, EMPTY_ACCOUNT)


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
    trie = state._storage_tries.get(address)
    if trie is None:
        return U256(0)

    value = trie_get(trie, key)

    assert isinstance(value, U256)
    return value


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
    trie = state._storage_tries.get(address)
    if trie is None:
        trie = Trie(secured=True, default=U256(0))
        state._storage_tries[address] = trie
    trie_set(trie, key, value)
    if trie._data == {}:
        del state._storage_tries[address]


def storage_root(state: State, address: Address) -> Bytes:
    """
    Calculate the storage root of an account.

    Parameters
    ----------
    state: `State`
        The state
    address : `Address`
        Address of the account.

    Returns
    -------
    root : `Bytes`
        Storage root of the account.
    """
    if address in state._storage_tries:
        return root(state._storage_tries[address])
    else:
        return EMPTY_TRIE_ROOT


def state_root(state: State) -> Bytes:
    """
    Calculate the state root.

    Parameters
    ----------
    state: `State`
        The state

    Returns
    -------
    root : `Bytes`
        The state root.
    """

    def get_storage_root(address: Address) -> Root:
        return storage_root(state, address)

    return root(state._main_trie, get_storage_root=get_storage_root)


def modify_state(
    state: State, address: Address, f: Callable[[Account], None]
) -> None:
    """
    Modify an `Account` in the `State`.
    """
    set_account(state, address, modify(get_account(state, address), f))


def move_ether(
    state: State,
    sender_address: Address,
    recipient_address: Address,
    amount: U256,
) -> None:
    """
    Move funds between accounts.
    """

    def reduce_sender_balance(sender: Account) -> None:
        assert sender.balance >= amount
        sender.balance -= amount

    def increase_recipient_balance(recipient: Account) -> None:
        recipient.balance += amount

    modify_state(state, sender_address, reduce_sender_balance)
    modify_state(state, recipient_address, increase_recipient_balance)
