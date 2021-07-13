"""
Ethereum Virtual Machine (EVM) Memory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

EVM memory operations.
"""
from ethereum.frontier.vm import Evm
from ethereum.utils import ceil32

from ...base_types import U256, Bytes, Uint
from .gas import calculate_memory_gas_cost, subtract_gas


def extend_memory_and_subtract_gas(
    evm: Evm, start_position: Uint, size: U256
) -> None:
    """
    Extends the size of the memory and
    substracts the gas amount to extend memory.

    Parameters
    ----------
    evm :
        The current EVM frame.
    start_position :
        Starting pointer to the memory.
    size :
        Amount of bytes by which the memory needs to be extended.
    """
    if size == 0:
        return None
    memory = evm.memory
    memory_size = Uint(len(memory))
    before_size = ceil32(memory_size)
    after_size = ceil32(start_position + size)
    if after_size <= before_size:
        return None
    already_paid = calculate_memory_gas_cost(before_size)
    total_cost = calculate_memory_gas_cost(after_size)
    to_be_paid = total_cost - already_paid
    evm.gas_left = subtract_gas(evm.gas_left, to_be_paid)
    size_to_extend = after_size - memory_size
    memory += b"\x00" * size_to_extend


def memory_write(
    memory: bytearray, start_position: Uint, value: Bytes
) -> None:
    """
    Writes to memory.

    Parameters
    ----------
    memory :
        Memory contents of the EVM.
    start_position :
        Starting pointer to the memory.
    value :
        Data to write to memory.
    """
    for idx, byte in enumerate(value):
        memory[start_position + idx] = byte


def memory_read_bytes(
    memory: bytearray, start_position: Uint, size: U256
) -> Bytes:
    """
    Read bytes from memory.

    Parameters
    ----------
    memory :
        Memory contents of the EVM.
    start_position :
        Starting pointer to the memory.
    size :
        Size of the data that needs to be read from `start_position`.

    Returns
    -------
    data_bytes :
        Data read from memory.
    """
    return Bytes(memory[start_position : start_position + size])
