"""
Ethereum Types
^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Types re-used throughout the specification, which are specific to Ethereum.
"""

from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from ..base_types import (
    U256,
    Bytes,
    Bytes8,
    Bytes20,
    Bytes32,
    Bytes256,
    Uint,
    modify,
    slotted_freezable,
)
from ..crypto import Hash32

Address = Bytes20
Root = Bytes

Storage = Dict[Bytes32, U256]
Bloom = Bytes256

TX_BASE_COST = 21000
TX_DATA_COST_PER_NON_ZERO = 68
TX_DATA_COST_PER_ZERO = 4


@slotted_freezable
@dataclass
class Transaction:
    """
    Atomic operation performed on the block chain.
    """

    nonce: U256
    gas_price: U256
    gas: U256
    to: Optional[Address]
    value: U256
    data: Bytes
    v: U256
    r: U256
    s: U256


@slotted_freezable
@dataclass
class Account:
    """
    State associated with an address.
    """

    nonce: Uint
    balance: U256
    code: bytes
    storage: Storage


@slotted_freezable
@dataclass
class Header:
    """
    Header portion of a block on the chain.
    """

    parent_hash: Hash32
    ommers_hash: Hash32
    coinbase: Address
    state_root: Root
    transactions_root: Root
    receipt_root: Root
    bloom: Bloom
    difficulty: Uint
    number: Uint
    gas_limit: Uint
    gas_used: Uint
    timestamp: U256
    extra_data: Bytes
    mix_digest: Bytes32
    nonce: Bytes8


@slotted_freezable
@dataclass
class Block:
    """
    A complete block.
    """

    header: Header
    transactions: Tuple[Transaction, ...]
    ommers: Tuple[Header, ...]


@slotted_freezable
@dataclass
class Log:
    """
    Data record produced during the execution of a transaction.
    """

    address: Address
    topics: Tuple[Hash32, ...]
    data: bytes


@slotted_freezable
@dataclass
class Receipt:
    """
    Result of a transaction.
    """

    post_state: Root
    cumulative_gas_used: Uint
    bloom: Bloom
    logs: Tuple[Log, ...]


State = Dict[Address, Account]


def initialize_account(state: State, address: Address) -> None:
    """
    Initialize an address in the state with an empty account.
    """
    state[address] = Account(
        nonce=Uint(0),
        balance=U256(0),
        code=bytearray(),
        storage={},
    )


def get_account(state: State, address: Address) -> Account:
    """
    Obtain the account corresponding to the address from the state.

    If the (address, account) pair is not yet present in the state, then a
    default account would be returned.

    In any case, this function will not modify the state. If you need to
    modify the state, use `modify_state` function which will automatically
    take care of initializing the account in the state if the corresponding
    address doesn't exist in the state.
    """
    if address in state:
        return state[address]

    return Account(
        nonce=Uint(0),
        balance=U256(0),
        code=bytearray(),
        storage={},
    )


def is_account_empty(state: State, address: Address) -> bool:
    """
    Check if an account corresponding to an address is an empty account.
    """
    account = state[address]
    return (
        account.nonce == Uint(0)
        and account.balance == U256(0)
        and account.code == bytearray()
        and account.storage == {}
    )


def modify_state(
    state: State, address: Address, f: Callable[[Account], None]
) -> None:
    """
    Modify an `Account` in the `State`.

    This will also initialize an account if the passed address is not present
    in the state yet.
    """
    if address not in state:
        initialize_account(state, address)

    state[address] = modify(state[address], f)

    # Remove empty accounts from the state
    if is_account_empty(state, address):
        state.pop(address)


def increment_nonce(state: State, address: Address) -> None:
    """
    Increase nonce for an account corresponding to an address.

    This will also initialize an account if the passed address is not present
    in the state yet.
    """

    def inc_nonce(account: Account) -> None:
        account.nonce += 1

    modify_state(state, address, inc_nonce)


def move_ether(
    state: State,
    sender_address: Address,
    recipient_address: Address,
    amount: U256,
) -> None:
    """
    Move funds between accounts.

    This will also initialize an account if the passed address is not present
    in the state yet.
    """

    def reduce_sender_balance(sender: Account) -> None:
        assert sender.balance >= amount
        sender.balance -= amount

    def increase_recipient_balance(recipient: Account) -> None:
        recipient.balance += amount

    modify_state(state, sender_address, reduce_sender_balance)
    modify_state(state, recipient_address, increase_recipient_balance)


def add_ether(state: State, address: Address, amount: U256) -> None:
    """
    Add ether to an account.

    This will also initialize an account if the passed address is not present
    in the state yet.
    """

    def increase_balance(account: Account) -> None:
        account.balance += amount

    modify_state(state, address, increase_balance)


def set_storage_key(
    state: State, address: Address, key: Bytes32, value: U256
) -> None:
    """
    Set the key-value pair in the storage of the account corresponding to
    the given address.

    This will also initialize an account if the passed address is not present
    in the state yet.
    """
    if address not in state:
        initialize_account(state, address)

    state[address].storage[key] = value


def delete_storage_key(state: State, address: Address, key: Bytes32) -> None:
    """
    Delete the key-value pair from the storage of the account corresponding
    to the given address.
    """
    # NOTE: This function will throw an error if you are trying to delete
    # from the storage of a non-existent account.
    # TODO: Check if the above assumption is correct.

    state[address].storage.pop(key, None)
