from dataclasses import dataclass
from typing import Dict, List, Optional

Bytes = bytes
Bytes32 = bytes
Bytes20 = bytes
Bytes8 = bytes
Root = Bytes32
Hash32 = Bytes32
Address = Bytes20
U256 = int
Uint = int

Storage = Dict[Bytes32, Bytes32]
Bloom = Bytes32

TX_BASE_COST = 21000
TX_DATA_COST_PER_NON_ZERO = 68
TX_DATA_COST_PER_ZERO = 4


@dataclass
class Transaction:
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
    nonce: Uint
    balance: Uint
    code: bytes
    storage: Storage


@dataclass
class Header:
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
    header: Header
    transactions: List[Transaction]
    ommers: List[Header]


@dataclass
class Log:
    address: Address
    topics: List[Hash32]
    data: bytes


@dataclass
class Receipt:
    post_state: Root
    cumulative_gas_used: Uint
    bloom: Bloom
    logs: List[Log]


State = Dict[Address, Account]
