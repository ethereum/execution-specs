"""
Transactions are atomic units of work created externally to Ethereum and
submitted to be executed. If Ethereum is viewed as a state machine,
transactions are the events that move between states.
"""
from dataclasses import dataclass
from typing import Union

from ..base_types import U256, Bytes, Bytes0, Uint, slotted_freezable
from .fork_types import Address

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
