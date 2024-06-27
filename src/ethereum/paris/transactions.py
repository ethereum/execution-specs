"""
Transactions are atomic units of work created externally to Ethereum and
submitted to be executed. If Ethereum is viewed as a state machine,
transactions are the events that move between states.
"""
from dataclasses import dataclass
from typing import Tuple, Union

from .. import rlp
from ..base_types import (
    U64,
    U256,
    Bytes,
    Bytes0,
    Bytes32,
    Uint,
    slotted_freezable,
)
from ..exceptions import InvalidBlock
from .fork_types import Address

TX_BASE_COST = 21000
TX_DATA_COST_PER_NON_ZERO = 16
TX_DATA_COST_PER_ZERO = 4
TX_CREATE_COST = 32000
TX_ACCESS_LIST_ADDRESS_COST = 2400
TX_ACCESS_LIST_STORAGE_KEY_COST = 1900


@slotted_freezable
@dataclass
class Access:
    account: Address
    slots: Tuple[Bytes32, ...]


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
    access_list: Tuple[Access, ...]
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
    access_list: Tuple[Access, ...]
    y_parity: U256
    r: U256
    s: U256


Transaction = Union[
    LegacyTransaction, AccessListTransaction, FeeMarketTransaction
]


# Helper function to handle the RLP encoding of the Access class instances.
def encode_access_list(
        access_list: Tuple[Access, ...]
) -> Tuple[Tuple[Address, Tuple[Bytes32, ...]], ...]:
    """
    Encode the Access list for RLP encoding.
    """
    return tuple((access.account, access.slots) for access in access_list)


# Helper function to handle the RLP decoding of the Access class instances.
def decode_access_list(
        encoded_access_list: Tuple[Tuple[Address, Tuple[Bytes32, ...]], ...]
) -> Tuple[Access, ...]:
    """
    Decode the Access list from RLP encoding.
    """
    return tuple(
        Access(account=encoded[0], slots=encoded[1]
               ) for encoded in encoded_access_list)


def encode_transaction(tx: Transaction) -> Union[LegacyTransaction, Bytes]:
    """
    Encode a transaction. Needed because non-legacy transactions aren't RLP.
    """
    if isinstance(tx, LegacyTransaction):
        return tx
    elif isinstance(tx, AccessListTransaction):
        encoded_access_list = encode_access_list(tx.access_list)
        return b"\x01" + rlp.encode(tx._replace(
            access_list=encoded_access_list))
    elif isinstance(tx, FeeMarketTransaction):
        encoded_access_list = encode_access_list(tx.access_list)
        return b"\x02" + rlp.encode(tx._replace(
            access_list=encoded_access_list))
    else:
        raise Exception(f"Unable to encode transaction of type {type(tx)}")


def decode_transaction(tx: Union[LegacyTransaction, Bytes]) -> Transaction:
    """
    Decode a transaction. Needed because non-legacy transactions aren't RLP.
    """
    if isinstance(tx, Bytes):
        if tx[0] == 1:
            decoded_tx = rlp.decode_to(AccessListTransaction, tx[1:])
            decoded_access_list = decode_access_list(decoded_tx.access_list)
            return decoded_tx._replace(access_list=decoded_access_list)
        elif tx[0] == 2:
            decoded_tx = rlp.decode_to(FeeMarketTransaction, tx[1:])
            decoded_access_list = decode_access_list(decoded_tx.access_list)
            return decoded_tx._replace(access_list=decoded_access_list)
        else:
            raise InvalidBlock
    else:
        return tx
