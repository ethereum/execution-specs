"""
Ethereum Virtual Machine (EVM)
------------------------------

The abstract computer which runs the code stored in an
`eth1spec.eth_types.Account`.
"""

from dataclasses import dataclass
from typing import List

from ..eth_types import U256, Address, Hash32, State, Uint


@dataclass
class Environment:
    """
    Items external to the virtual machine itself, provided by the environment.
    """

    caller: Address
    block_hashes: List[Hash32]
    origin: Address
    coinbase: Address
    number: Uint
    gas_limit: Uint
    gas_price: Uint
    time: Uint
    difficulty: Uint
    state: State


@dataclass
class Evm:
    """The internal state of the virtual machine."""

    pc: Uint
    stack: List[U256]
    memory: bytes
    code: bytes
    gas_left: Uint
    current: Address
    caller: Address
    data: bytes
    value: Uint
    depth: Uint
    env: Environment
