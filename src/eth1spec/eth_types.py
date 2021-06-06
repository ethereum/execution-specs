"""
# Ethereum Base Types
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from .number import Uint

Bytes = bytes
Bytes64 = Bytes
Bytes32 = Bytes
Bytes20 = Bytes
Bytes8 = Bytes
Hash32 = Bytes
Root = Bytes
Hash64 = Bytes64
Address = Bytes20
U256 = Uint

Storage = Dict[Bytes32, Bytes32]
Bloom = Bytes32

TX_BASE_COST = 21000
TX_DATA_COST_PER_NON_ZERO = 68
TX_DATA_COST_PER_ZERO = 4


@dataclass
class Transaction:
    """
    Atomic operation performed on the block chain.
    """

    nonce: Uint
    gas_price: Uint
    gas: Uint
    to: Optional[Address]
    value: Uint
    data: Bytes
    v: Uint
    r: Uint
    s: Uint


@dataclass
class Account:
    """
    State associated with an address.
    """

    nonce: Uint
    balance: Uint
    code: bytes
    storage: Storage


@dataclass
class Header:
    """
    Header portion of a block on the chain.
    """

    parent: Hash32
    ommers: Hash32
    coinbase: Address
    state_root: Root
    transactions_root: Root
    receipt_root: Root
    bloom: Bloom
    difficulty: Uint
    number: Uint
    gas_limit: Uint
    gas_used: Uint
    time: Uint
    extra: Bytes
    mix_digest: Bytes32
    nonce: Bytes8


@dataclass
class Block:
    """
    A complete block.
    """

    header: Header
    transactions: List[Transaction]
    ommers: List[Header]


@dataclass
class Log:
    """
    Data record produced during the execution of a transaction.
    """

    address: Address
    topics: List[Hash32]
    data: bytes


@dataclass
class Receipt:
    """
    Result of a transaction.
    """

    post_state: Root
    cumulative_gas_used: Uint
    bloom: Bloom
    logs: List[Log]


State = Dict[Address, Account]
