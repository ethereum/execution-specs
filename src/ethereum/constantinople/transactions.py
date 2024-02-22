
from dataclasses import dataclass
from typing import Union

from .. import rlp
from ..base_types import (
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
from ..crypto.hash import Hash32, keccak256

Address = Bytes20


TX_BASE_COST = 21000
TX_DATA_COST_PER_NON_ZERO = 68
TX_DATA_COST_PER_ZERO = 4
TX_CREATE_COST = 32000


@slotted_freezable
@dataclass
class Transaction:
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

