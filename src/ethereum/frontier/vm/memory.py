"""
Ethereum Virtual Machine (EVM) Memory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the EVM memory expansion related operations.
"""

from typing import cast

from ethereum.base_types import U256

from . import Evm
from .gas import GAS_MEMORY, subtract_gas


def get_words(memory_size: int) -> int:
    """
    Obtain the number of words (32 bytes) which is present in the memory,
    based on the memory size. Memory size is the number of bytes present in
    memory.

    If the memory size is not a perfect multiple of 32 bytes, then the number
    of words in memory is considered as the ceil32 of memory size.

    Parameters
    ----------
    memory_size :
        Number of bytes present in memory.

    Returns
    -------
    num_words :
        The number of words present in memory.
    """
    if memory_size % 32 == 0:
        return memory_size // 32

    return 1 + (memory_size // 32)


def calculate_memory_cost(memory_size: int) -> int:
    """
    Calculate the gas cost for expanding the memory from 0 bytes to a
    particular size in bytes.

    Parameters
    ----------
    memory_size :
        Number of bytes present in memory.

    Returns
    -------
    gas_cost :
        The cost of gas in expanding the memory from 0 to the preferred size.
    """
    memory_size_as_words = get_words(memory_size)

    linear_gas_cost = GAS_MEMORY * memory_size_as_words
    quadratic_gas_cost = (memory_size_as_words ** 2) // 512
    return linear_gas_cost + quadratic_gas_cost


def expand_memory(evm: Evm, memory_size: int) -> None:
    """
    Expand the memory from the current size to the given size.
    Here memory size is defined as the number of bytes in memory.
    This function also calculates and deducts the gas involved for the
    memory expansion.

    Parameters
    ----------
    evm :
        The current EVM frame.
    memory_size :
        The required memory size to which the memory is to be expanded.
    """
    # The existing memory cost would have already been paid.
    existing_memory_cost = calculate_memory_cost(len(evm.memory))
    expanded_memory_cost = calculate_memory_cost(memory_size)
    expansion_gas_cost = expanded_memory_cost - existing_memory_cost

    evm.gas_left = subtract_gas(evm.gas_left, cast(U256, expansion_gas_cost))

    bytes_to_add_to_memory = memory_size - len(evm.memory)
    evm.memory += b"\x00" * bytes_to_add_to_memory
