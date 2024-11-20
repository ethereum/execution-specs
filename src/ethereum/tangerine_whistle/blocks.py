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
from typing import Annotated, Tuple, Union

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U256, Uint
from typing_extensions import TypeAlias

from ethereum.dao_fork import blocks as previous_blocks
from ethereum.exceptions import InvalidBlock

from ..crypto.hash import Hash32
from .fork_types import Address, Bloom, Root
from .transactions import Transaction


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


AnyHeader: TypeAlias = Union[previous_blocks.AnyHeader, Header]
"""
Represents all headers that may have appeared in the blockchain before or in
the current fork.
"""


def decode_header(raw_header: rlp.Simple) -> AnyHeader:
    """
    Convert `raw_header` from raw sequences and bytes to a structured block
    header.

    Checks `raw_header` against this fork's `FORK_CRITERIA`, and if it belongs
    to this fork, decodes it accordingly. If not, this function forwards to the
    preceding fork where the process is repeated.
    """
    from . import FORK_CRITERIA

    # First, ensure that `raw_header` is not `bytes` (and is therefore a
    # sequence.)
    if isinstance(raw_header, bytes):
        raise InvalidBlock("header is bytes, expected sequence")

    # Next, extract the block number and timestamp (which are always at index 8
    # and 11 respectively.)
    raw_number = raw_header[8]
    if not isinstance(raw_number, bytes):
        raise InvalidBlock("header number is sequence, expected bytes")
    number = Uint.from_be_bytes(raw_number)

    raw_timestamp = raw_header[11]
    if not isinstance(raw_timestamp, bytes):
        raise InvalidBlock("header timestamp is sequence, expected bytes")
    timestamp = U256.from_be_bytes(raw_timestamp)

    # Finally, check if this header belongs to this fork.
    if FORK_CRITERIA.check(number, timestamp):
        return rlp.deserialize_to(Header, raw_header)

    # If it doesn't, forward to the preceding fork.
    return previous_blocks.decode_header(raw_header)


@slotted_freezable
@dataclass
class Block:
    """
    A complete block.
    """

    header: Header
    transactions: Tuple[Transaction, ...]
    ommers: Tuple[Annotated[AnyHeader, rlp.With(decode_header)], ...]


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

    post_state: Root
    cumulative_gas_used: Uint
    bloom: Bloom
    logs: Tuple[Log, ...]
