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
from ethereum.base_types import U256, Bytes, Uint
from ethereum.utils.numeric import ceil32

from .. import Evm
from ..gas import (
    GAS_BASE,
    GAS_COPY,
    GAS_VERY_LOW,
    calculate_gas_extend_memory,
    charge_gas,
)
from ..memory import memory_read_bytes, memory_write
from ..stack import pop, push


def mstore(evm: Evm) -> None:
    """
    Stores a word to memory.
    This also expands the memory, if the memory is
    insufficient to store the word.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    start_position = pop(evm.stack)
    value = pop(evm.stack).to_be_bytes32()

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(start_position, U256(len(value)))]
    )

    charge_gas(evm, GAS_VERY_LOW + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    memory_write(evm.memory, start_position, value)

    # PROGRAM COUNTER
    evm.pc += 1


def mstore8(evm: Evm) -> None:
    """
    Stores a byte to memory.
    This also expands the memory, if the memory is
    insufficient to store the word.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    start_position = pop(evm.stack)
    value = pop(evm.stack)

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(start_position, U256(1))]
    )

    charge_gas(evm, GAS_VERY_LOW + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    normalized_bytes_value = Bytes([value & 0xFF])
    memory_write(evm.memory, start_position, normalized_bytes_value)

    # PROGRAM COUNTER
    evm.pc += 1


def mload(evm: Evm) -> None:
    """
    Load word from memory.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    start_position = pop(evm.stack)

    # GAS
    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(start_position, U256(32))]
    )
    charge_gas(evm, GAS_VERY_LOW + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    value = U256.from_be_bytes(
        memory_read_bytes(evm.memory, start_position, U256(32))
    )
    push(evm.stack, value)

    # PROGRAM COUNTER
    evm.pc += 1


def msize(evm: Evm) -> None:
    """
    Push the size of active memory in bytes onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_BASE)

    # OPERATION
    push(evm.stack, U256(len(evm.memory)))

    # PROGRAM COUNTER
    evm.pc += 1


def mcopy(evm: Evm) -> None:
    """
    Copy the bytes in memory from one location to another.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    destination = pop(evm.stack)
    source = pop(evm.stack)
    length = pop(evm.stack)

    # GAS
    words = ceil32(Uint(length)) // 32
    copy_gas_cost = GAS_COPY * words

    extend_memory = calculate_gas_extend_memory(
        evm.memory, [(source, length), (destination, length)]
    )
    charge_gas(evm, GAS_VERY_LOW + copy_gas_cost + extend_memory.cost)

    # OPERATION
    evm.memory += b"\x00" * extend_memory.expand_by
    value = memory_read_bytes(evm.memory, source, length)
    memory_write(evm.memory, destination, value)

    # PROGRAM COUNTER
    evm.pc += 1
