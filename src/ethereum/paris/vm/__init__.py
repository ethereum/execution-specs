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
from typing import Dict, List, Optional, Set, Tuple, Union

from ethereum.base_types import U256, Bytes, Bytes0, Bytes32, Uint, Uint64
from ethereum.crypto.hash import Hash32

from ..eth_types import Address, Log
from ..state import State

__all__ = ("Environment", "Evm", "Message")


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
    base_fee_per_gas: Uint
    gas_limit: Uint
    gas_price: U256
    time: U256
    prev_randao: Bytes32
    state: State
    chain_id: Uint64


@dataclass
class Message:
    """
    Items that are used by contract creation or message call.
    """

    caller: Address
    target: Union[Bytes0, Address]
    current_target: Address
    gas: U256
    value: U256
    data: Bytes
    code_address: Optional[Address]
    code: Bytes
    depth: Uint
    should_transfer_value: bool
    is_static: bool
    accessed_addresses: Set[Address]
    accessed_storage_keys: Set[Tuple[Address, Bytes32]]


@dataclass
class Evm:
    """The internal state of the virtual machine."""

    pc: Uint
    stack: List[U256]
    memory: bytearray
    code: Bytes
    gas_left: U256
    env: Environment
    valid_jump_destinations: Set[Uint]
    logs: Tuple[Log, ...]
    refund_counter: int
    running: bool
    message: Message
    output: Bytes
    accounts_to_delete: Dict[Address, Address]
    has_erred: bool
    children: List["Evm"]
    return_data: Bytes
    error: Optional[Exception]
    accessed_addresses: Set[Address]
    accessed_storage_keys: Set[Tuple[Address, Bytes32]]
