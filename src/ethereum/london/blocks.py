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
from typing import Optional, Tuple, Union

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U256, Uint
from typing_extensions import TypeAlias

from ethereum.berlin import blocks as previous_blocks

from ..crypto.hash import Hash32
from .fork_types import Address, Bloom, Root
from .transactions import (
    AccessListTransaction,
    FeeMarketTransaction,
    LegacyTransaction,
    Transaction,
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
    base_fee_per_gas: Uint


AnyHeader: TypeAlias = Union[previous_blocks.AnyHeader, Header]
"""
Represents all headers that may have appeared in the blockchain before or in
the current fork.
"""


@slotted_freezable
@dataclass
class Block:
    """
    A complete block.
    """

    header: Header
    transactions: Tuple[Union[Bytes, LegacyTransaction], ...]
    ommers: Tuple[Header, ...]


AnyBlock: TypeAlias = Union[previous_blocks.AnyBlock, Block]
"""
Represents all blocks that may have appeared in the blockchain before or in the
current fork.
"""


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
    else:
        return receipt


def decode_receipt(receipt: Union[Bytes, Receipt]) -> Receipt:
    """
    Decodes a receipt.
    """
    if isinstance(receipt, Bytes):
        assert receipt[0] in (1, 2)
        return rlp.decode_to(Receipt, receipt[1:])
    else:
        return receipt


def header_base_fee_per_gas(header: AnyHeader) -> Optional[Uint]:
    """
    Returns the `base_fee_per_gas` of the given header, or `None` for headers
    without that field.
    """
    if isinstance(header, Header):
        return header.base_fee_per_gas
    return None
