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
from ethereum.utils import ceil32

from ...base_types import U256, Bytes, Uint


def extend_memory(memory: bytearray, start_position: Uint, size: U256) -> None:
    """
    Extends the size of the memory and
    substracts the gas amount to extend memory.

    Parameters
    ----------
    memory :
        Memory contents of the EVM.
    start_position :
        Starting pointer to the memory.
    size :
        Amount of bytes by which the memory needs to be extended.
    """
    if size == 0:
        return None
    memory_size = Uint(len(memory))
    before_size = ceil32(memory_size)
    after_size = ceil32(start_position + size)
    if after_size <= before_size:
        return None
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
    return memory[start_position : start_position + size]
