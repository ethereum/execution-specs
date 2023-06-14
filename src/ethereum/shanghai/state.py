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

There is a distinction between an account that does not exist and
`EMPTY_ACCOUNT`.
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set, Tuple

from ethereum.base_types import U256, Bytes, Uint, modify
from ethereum.utils.ensure import ensure

from .fork_types import EMPTY_ACCOUNT, Account, Address, Root, Withdrawal
from .trie import EMPTY_TRIE_ROOT, Trie, copy_trie, root, trie_get, trie_set


@dataclass
class State:
    """
    Contains all information that is preserved between transactions.
    """

    _main_trie: Trie[Address, Optional[Account]] = field(
        default_factory=lambda: Trie(secured=True, default=None)
    )
    _storage_tries: Dict[Address, Trie[Bytes, U256]] = field(
        default_factory=dict
    )
    _snapshots: List[
        Tuple[
            Trie[Address, Optional[Account]], Dict[Address, Trie[Bytes, U256]]
        ]
    ] = field(default_factory=list)
    _created_accounts: Set[Address] = field(default_factory=set)


def close_state(state: State) -> None:
    """
    Free resources held by the state. Used by optimized implementations to
    release file descriptors.
    """
    del state._main_trie
    del state._storage_tries
    del state._snapshots
    del state._created_accounts


def begin_transaction(state: State) -> None:
    """
    Start a state transaction.

    Transactions are entirely implicit and can be nested. It is not possible to
    calculate the state root during a transaction.

    Parameters
    ----------
    state : State
        The state.
    """
    state._snapshots.append(
        (
            copy_trie(state._main_trie),
            {k: copy_trie(t) for (k, t) in state._storage_tries.items()},
        )
    )


def commit_transaction(state: State) -> None:
    """
    Commit a state transaction.

    Parameters
    ----------
    state : State
        The state.
    """
    state._snapshots.pop()
    if not state._snapshots:
        state._created_accounts.clear()


def rollback_transaction(state: State) -> None:
    """
    Rollback a state transaction, resetting the state to the point when the
    corresponding `start_transaction()` call was made.

    Parameters
    ----------
    state : State
        The state.
    """
    state._main_trie, state._storage_tries = state._snapshots.pop()
    if not state._snapshots:
        state._created_accounts.clear()


def get_account(state: State, address: Address) -> Account:
    """
    Get the `Account` object at an address. Returns `EMPTY_ACCOUNT` if there
    is no account at the address.

    Use `get_account_optional()` if you care about the difference between a
    non-existent account and `EMPTY_ACCOUNT`.

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
    account = get_account_optional(state, address)
    if isinstance(account, Account):
        return account
    else:
        return EMPTY_ACCOUNT


def get_account_optional(state: State, address: Address) -> Optional[Account]:
    """
    Get the `Account` object at an address. Returns `None` (rather than
    `EMPTY_ACCOUNT`) if there is no account at the address.

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
    return account


def set_account(
    state: State, address: Address, account: Optional[Account]
) -> None:
    """
    Set the `Account` object at an address. Setting to `None` deletes
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
    destroy_storage(state, address)
    set_account(state, address, None)


def destroy_storage(state: State, address: Address) -> None:
    """
    Completely remove the storage at `address`.

    Parameters
    ----------
    state: `State`
        The state
    address : `Address`
        Address of account whose storage is to be deleted.
    """
    if address in state._storage_tries:
        del state._storage_tries[address]


def mark_account_created(state: State, address: Address) -> None:
    """
    Mark an account as having been created in the current transaction.
    This information is used by `get_storage_original()` to handle an obscure
    edgecase.

    The marker is not removed even if the account creation reverts. Since the
    account cannot have had code prior to its creation and can't call
    `get_storage_original()`, this is harmless.

    Parameters
    ----------
    state: `State`
        The state
    address : `Address`
        Address of the account that has been created.
    """
    state._created_accounts.add(address)


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
    assert trie_get(state._main_trie, address) is not None

    trie = state._storage_tries.get(address)
    if trie is None:
        trie = Trie(secured=True, default=U256(0))
        state._storage_tries[address] = trie
    trie_set(trie, key, value)
    if trie._data == {}:
        del state._storage_tries[address]


def storage_root(state: State, address: Address) -> Root:
    """
    Calculate the storage root of an account.

    Parameters
    ----------
    state:
        The state
    address :
        Address of the account.

    Returns
    -------
    root : `Root`
        Storage root of the account.
    """
    assert not state._snapshots
    if address in state._storage_tries:
        return root(state._storage_tries[address])
    else:
        return EMPTY_TRIE_ROOT


def state_root(state: State) -> Root:
    """
    Calculate the state root.

    Parameters
    ----------
    state:
        The current state.

    Returns
    -------
    root : `Root`
        The state root.
    """
    assert not state._snapshots

    def get_storage_root(address: Address) -> Root:
        return storage_root(state, address)

    return root(state._main_trie, get_storage_root=get_storage_root)


def account_exists(state: State, address: Address) -> bool:
    """
    Checks if an account exists in the state trie

    Parameters
    ----------
    state:
        The state
    address:
        Address of the account that needs to be checked.

    Returns
    -------
    account_exists : `bool`
        True if account exists in the state trie, False otherwise
    """
    return get_account_optional(state, address) is not None


def account_has_code_or_nonce(state: State, address: Address) -> bool:
    """
    Checks if an account has non zero nonce or non empty code

    Parameters
    ----------
    state:
        The state
    address:
        Address of the account that needs to be checked.

    Returns
    -------
    has_code_or_nonce : `bool`
        True if if an account has non zero nonce or non empty code,
        False otherwise.
    """
    account = get_account(state, address)
    return account.nonce != Uint(0) or account.code != b""


def is_account_empty(state: State, address: Address) -> bool:
    """
    Checks if an account has zero nonce, empty code and zero balance.

    Parameters
    ----------
    state:
        The state
    address:
        Address of the account that needs to be checked.

    Returns
    -------
    is_empty : `bool`
        True if if an account has zero nonce, empty code and zero balance,
        False otherwise.
    """
    account = get_account(state, address)
    return (
        account.nonce == Uint(0)
        and account.code == b""
        and account.balance == 0
    )


def account_exists_and_is_empty(state: State, address: Address) -> bool:
    """
    Checks if an account exists and has zero nonce, empty code and zero
    balance.

    Parameters
    ----------
    state:
        The state
    address:
        Address of the account that needs to be checked.

    Returns
    -------
    exists_and_is_empty : `bool`
        True if an account exists and has zero nonce, empty code and zero
        balance, False otherwise.
    """
    account = get_account_optional(state, address)
    return (
        account is not None
        and account.nonce == Uint(0)
        and account.code == b""
        and account.balance == 0
    )


def is_account_alive(state: State, address: Address) -> bool:
    """
    Check whether is an account is both in the state and non empty.

    Parameters
    ----------
    state:
        The state
    address:
        Address of the account that needs to be checked.

    Returns
    -------
    is_alive : `bool`
        True if the account is alive.
    """
    account = get_account_optional(state, address)
    if account is None:
        return False
    else:
        return not (
            account.nonce == Uint(0)
            and account.code == b""
            and account.balance == 0
        )


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
        ensure(sender.balance >= amount, AssertionError)
        sender.balance -= amount

    def increase_recipient_balance(recipient: Account) -> None:
        recipient.balance += amount

    modify_state(state, sender_address, reduce_sender_balance)
    modify_state(state, recipient_address, increase_recipient_balance)


def process_withdrawal(
    state: State,
    wd: Withdrawal,
) -> None:
    """
    Increase the balance of the withdrawing account.
    """

    def increase_recipient_balance(recipient: Account) -> None:
        recipient.balance += wd.amount * 10**9

    modify_state(state, wd.address, increase_recipient_balance)


def set_account_balance(state: State, address: Address, amount: U256) -> None:
    """
    Sets the balance of an account.

    Parameters
    ----------
    state:
        The current state.

    address:
        Address of the account whose nonce needs to be incremented.

    amount:
        The amount that needs to set in balance.
    """

    def set_balance(account: Account) -> None:
        account.balance = amount

    modify_state(state, address, set_balance)


def touch_account(state: State, address: Address) -> None:
    """
    Initializes an account to state.

    Parameters
    ----------
    state:
        The current state.

    address:
        The address of the account that need to initialised.
    """
    if not account_exists(state, address):
        set_account(state, address, EMPTY_ACCOUNT)


def increment_nonce(state: State, address: Address) -> None:
    """
    Increments the nonce of an account.

    Parameters
    ----------
    state:
        The current state.

    address:
        Address of the account whose nonce needs to be incremented.
    """

    def increase_nonce(sender: Account) -> None:
        sender.nonce += 1

    modify_state(state, address, increase_nonce)


def set_code(state: State, address: Address, code: Bytes) -> None:
    """
    Sets Account code.

    Parameters
    ----------
    state:
        The current state.

    address:
        Address of the account whose code needs to be update.

    code:
        The bytecode that needs to be set.
    """

    def write_code(sender: Account) -> None:
        sender.code = code

    modify_state(state, address, write_code)


def get_storage_original(state: State, address: Address, key: Bytes) -> U256:
    """
    Get the original value in a storage slot i.e. the value before the current
    transaction began. This function reads the value from the snapshots taken
    before executing the transaction.

    Parameters
    ----------
    state:
        The current state.
    address:
        Address of the account to read the value from.
    key:
        Key of the storage slot.
    """
    # In the transaction where an account is created, its preexisting storage
    # is ignored.
    if address in state._created_accounts:
        return U256(0)

    _, original_trie = state._snapshots[0]
    original_account_trie = original_trie.get(address)

    if original_account_trie is None:
        original_value = U256(0)
    else:
        original_value = trie_get(original_account_trie, key)

    assert isinstance(original_value, U256)

    return original_value
