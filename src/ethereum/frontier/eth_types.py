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
from typing import Dict, Optional, Tuple

from ..base_types import (
    U256,
    Bytes,
    Bytes8,
    Bytes20,
    Bytes32,
    Bytes256,
    Uint,
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


EMPTY_ACCOUNT = Account(
    nonce=Uint(0),
    balance=U256(0),
    code=bytearray(),
)


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
