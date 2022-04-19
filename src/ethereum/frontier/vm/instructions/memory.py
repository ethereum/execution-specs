"""
Ethereum Virtual Machine (EVM) Memory Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM Memory instructions.
"""
from typing import List

from ethereum.base_types import U8_MAX_VALUE, U256

from .. import Evm
from ..gas import GAS_BASE, GAS_VERY_LOW, subtract_gas
from ..memory import memory_read_bytes, memory_write, touch_memory
from ..operation import Operation, static_gas


def gas_mstore(
    evm: Evm, stack: List[U256], value: U256, start_position: U256
) -> None:
    """
    Stores a word to memory.
    This also expands the memory, if the memory is
    insufficient to store the word.
    """
    subtract_gas(evm, GAS_VERY_LOW)
    touch_memory(evm, start_position, U256(32))


def do_mstore(
    evm: Evm, stack: List[U256], value: U256, start_position: U256
) -> None:
    """
    Stores a word to memory.
    This also expands the memory, if the memory is
    insufficient to store the word.
    """
    memory_write(evm, start_position, value.to_be_bytes32())


mstore = Operation(gas_mstore, do_mstore, 2, 0)


def gas_mstore8(
    evm: Evm, stack: List[U256], value: U256, start_position: U256
) -> None:
    """
    Stores a byte to memory.
    This also expands the memory, if the memory is
    insufficient to store the word.
    """
    subtract_gas(evm, GAS_VERY_LOW)
    touch_memory(evm, start_position, U256(1))


def do_mstore8(
    evm: Evm, stack: List[U256], value: U256, start_position: U256
) -> None:
    """
    Stores a byte to memory.
    This also expands the memory, if the memory is
    insufficient to store the word.
    """
    # make sure that value doesn't exceed 1 byte
    normalized_bytes_value = (value & U8_MAX_VALUE).to_bytes(1, "big")
    memory_write(evm, start_position, normalized_bytes_value)


mstore8 = Operation(gas_mstore8, do_mstore8, 2, 0)


def gas_mload(evm: Evm, stack: List[U256], start_position: U256) -> None:
    """
    Load word from memory.
    """
    subtract_gas(evm, GAS_VERY_LOW)
    touch_memory(evm, start_position, U256(32))


def do_mload(evm: Evm, stack: List[U256], start_position: U256) -> U256:
    """
    Load word from memory.
    """
    return U256.from_be_bytes(memory_read_bytes(evm, start_position, U256(32)))


mload = Operation(gas_mload, do_mload, 1, 1)


def do_msize(evm: Evm, stack: List[U256]) -> U256:
    """
    Push the size of active memory in bytes onto the stack.
    """
    return U256(len(evm.memory))


msize = Operation(static_gas(GAS_BASE), do_msize, 0, 1)
