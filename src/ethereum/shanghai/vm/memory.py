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
from ethereum.utils.byte import right_pad_zero_bytes
from ethereum.utils.numeric import ceil32

from ...base_types import U256, Bytes, Uint
from . import Evm
from .gas import calculate_gas_extend_memory, charge_gas


def extend_memory(evm: Evm, start_position: U256, size: U256) -> None:
    """
    Extends the size of the memory and
    substracts the gas amount to extend memory.

    Parameters
    ----------
    evm :
        The current Evm.
    start_position :
        Starting pointer to the memory.
    size :
        Amount of bytes by which the memory needs to be extended.
    """
    charge_gas(
        evm, calculate_gas_extend_memory(evm.memory, start_position, size)
    )
    if size == 0:
        return
    memory_size = Uint(len(evm.memory))
    before_size = ceil32(memory_size)
    after_size = ceil32(Uint(start_position) + Uint(size))
    if after_size <= before_size:
        return
    size_to_extend = after_size - memory_size
    evm.memory += b"\x00" * size_to_extend


def memory_write(
    memory: bytearray, start_position: U256, value: Bytes
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
    memory[start_position : Uint(start_position) + len(value)] = value


def memory_read_bytes(
    memory: bytearray, start_position: U256, size: U256
) -> bytearray:
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
    return memory[start_position : Uint(start_position) + Uint(size)]


def buffer_read(buffer: Bytes, start_position: U256, size: U256) -> Bytes:
    """
    Read bytes from a buffer. Padding with zeros if neccesary.

    Parameters
    ----------
    buffer :
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
    return right_pad_zero_bytes(
        buffer[start_position : Uint(start_position) + Uint(size)], size
    )
