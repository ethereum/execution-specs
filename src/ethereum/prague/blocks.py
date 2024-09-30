"""
A `Block` is a single link in the chain that is Ethereum. Each `Block` contains
a `Header` and zero or more transactions. Each `Header` contains associated
metadata like the block number, parent block hash, and how much gas was
consumed by its transactions.

Together, these blocks form a cryptographically secure journal recording the
history of all state transitions that have happened since the genesis of the
chain.
"""
from dataclasses import dataclass
from typing import Tuple, Union

from .. import rlp
from ..base_types import (
    U64,
    U256,
    Bytes,
    Bytes8,
    Bytes32,
    Uint,
    slotted_freezable,
)
from ..crypto.hash import Hash32
from .fork_types import Address, Bloom, Root
from .transactions import (
    AccessListTransaction,
    BlobTransaction,
    FeeMarketTransaction,
    LegacyTransaction,
    SetCodeTransaction,
    Transaction,
)


@slotted_freezable
@dataclass
class Withdrawal:
    """
    Withdrawals that have been validated on the consensus layer.
    """

    index: U64
    validator_index: U64
    address: Address
    amount: U256


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
    prev_randao: Bytes32
    nonce: Bytes8
    base_fee_per_gas: Uint
    withdrawals_root: Root
    blob_gas_used: U64
    excess_blob_gas: U64
    parent_beacon_block_root: Root
    requests_hash: Hash32


@slotted_freezable
@dataclass
class Block:
    """
    A complete block.
    """

    header: Header
    transactions: Tuple[Union[Bytes, LegacyTransaction], ...]
    ommers: Tuple[Header, ...]
    withdrawals: Tuple[Withdrawal, ...]


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

    succeeded: bool
    cumulative_gas_used: Uint
    bloom: Bloom
    logs: Tuple[Log, ...]


def encode_receipt(tx: Transaction, receipt: Receipt) -> Union[Bytes, Receipt]:
    """
    Encodes a receipt.
    """
    if isinstance(tx, AccessListTransaction):
        return b"\x01" + rlp.encode(receipt)
    elif isinstance(tx, FeeMarketTransaction):
        return b"\x02" + rlp.encode(receipt)
    elif isinstance(tx, BlobTransaction):
        return b"\x03" + rlp.encode(receipt)
    elif isinstance(tx, SetCodeTransaction):
        return b"\x04" + rlp.encode(receipt)
    else:
        return receipt


def decode_receipt(receipt: Union[Bytes, Receipt]) -> Receipt:
    """
    Decodes a receipt.
    """
    if isinstance(receipt, Bytes):
        assert receipt[0] in (1, 2, 3, 4)
        return rlp.decode_to(Receipt, receipt[1:])
    else:
        return receipt
