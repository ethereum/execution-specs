
from dataclasses import dataclass
from typing import Tuple, Union

from .. import rlp
from ..base_types import (
    U64,
    U256,
    Bytes,
    Bytes0,
    Bytes8,
    Bytes20,
    Bytes32,
    Bytes256,
    Uint,
    slotted_freezable,
)
from ..crypto.hash import Hash32
from ..exceptions import InvalidBlock

Address = Bytes20
Root = Hash32

Bloom = Bytes256

TX_BASE_COST = 21000
TX_DATA_COST_PER_NON_ZERO = 16
TX_DATA_COST_PER_ZERO = 4
TX_CREATE_COST = 32000
TX_ACCESS_LIST_ADDRESS_COST = 2400
TX_ACCESS_LIST_STORAGE_KEY_COST = 1900


@slotted_freezable
@dataclass
class LegacyTransaction:
    """
    Atomic operation performed on the block chain.
    """

    nonce: U256
    gas_price: Uint
    gas: Uint
    to: Union[Bytes0, Address]
    value: U256
    data: Bytes
    v: U256
    r: U256
    s: U256


@slotted_freezable
@dataclass
class AccessListTransaction:
    """
    The transaction type added in EIP-2930 to support access lists.
    """

    chain_id: U64
    nonce: U256
    gas_price: Uint
    gas: Uint
    to: Union[Bytes0, Address]
    value: U256
    data: Bytes
    access_list: Tuple[Tuple[Address, Tuple[Bytes32, ...]], ...]
    y_parity: U256
    r: U256
    s: U256


@slotted_freezable
@dataclass
class FeeMarketTransaction:
    """
    The transaction type added in EIP-1559.
    """

    chain_id: U64
    nonce: U256
    max_priority_fee_per_gas: Uint
    max_fee_per_gas: Uint
    gas: Uint
    to: Union[Bytes0, Address]
    value: U256
    data: Bytes
    access_list: Tuple[Tuple[Address, Tuple[Bytes32, ...]], ...]
    y_parity: U256
    r: U256
    s: U256


Transaction = Union[
    LegacyTransaction, AccessListTransaction, FeeMarketTransaction
]


def encode_transaction(tx: Transaction) -> Union[LegacyTransaction, Bytes]:
    """
    Encode a transaction. Needed because non-legacy transactions aren't RLP.
    """
    if isinstance(tx, LegacyTransaction):
        return tx
    elif isinstance(tx, AccessListTransaction):
        return b"\x01" + rlp.encode(tx)
    elif isinstance(tx, FeeMarketTransaction):
        return b"\x02" + rlp.encode(tx)
    else:
        raise Exception(f"Unable to encode transaction of type {type(tx)}")


def decode_transaction(tx: Union[LegacyTransaction, Bytes]) -> Transaction:
    """
    Decode a transaction. Needed because non-legacy transactions aren't RLP.
    """
    if isinstance(tx, Bytes):
        if tx[0] == 1:
            return rlp.decode_to(AccessListTransaction, tx[1:])
        elif tx[0] == 2:
            return rlp.decode_to(FeeMarketTransaction, tx[1:])
        else:
            raise InvalidBlock
    else:
        return tx

