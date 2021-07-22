"""
Ethereum Virtual Machine (EVM)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

The abstract computer which runs the code stored in an
`eth1spec.eth_types.Account`.
"""

from dataclasses import dataclass
from typing import List, Set

from ethereum.base_types import U256, Uint
from ethereum.crypto import Hash32

from ..eth_types import Address, State

__all__ = ("Environment", "Evm")


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
    gas_price: U256
    time: U256
    difficulty: Uint
    state: State


@dataclass
class Evm:
    """The internal state of the virtual machine."""

    pc: Uint
    stack: List[U256]
    memory: bytearray
    code: bytes
    gas_left: U256
    current: Address
    caller: Address
    data: bytes
    value: U256
    depth: Uint
    env: Environment
    valid_jump_destinations: Set[Uint]
    refund_counter: Uint
    running: bool
