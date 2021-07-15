"""
Ethereum Virtual Machine (EVM) Gas
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

EVM gas constants and calculators.
"""
from ethereum.base_types import U256, Uint
from ethereum.utils import ceil32

from .error import OutOfGasError

GAS_EXT = U256(20)
GAS_JUMPDEST = U256(1)
GAS_BASE = U256(2)
GAS_VERY_LOW = U256(3)
GAS_SLOAD = U256(50)
GAS_STORAGE_SET = U256(20000)
GAS_STORAGE_UPDATE = U256(5000)
GAS_STORAGE_CLEAR_REFUND = U256(15000)
GAS_LOW = U256(5)
GAS_MID = U256(8)
GAS_HIGH = U256(10)
GAS_EXPONENTIATION = U256(10)
GAS_MEMORY = U256(3)
GAS_KECCAK256 = U256(30)
GAS_KECCAK256_WORD = U256(6)
GAS_COPY = U256(3)


def subtract_gas(gas_left: U256, amount: U256) -> U256:
    """
    Subtracts `amount` from `gas_left`.

    Parameters
    ----------
    gas_left :
        The amount of gas left in the current frame.
    amount :
        The amount of gas the current operation requires.

    Raises
    ------
    OutOfGasError
        If `gas_left` is less than `amount`.
    """
    if gas_left < amount:
        raise OutOfGasError

    return gas_left - amount


def calculate_memory_gas_cost(size_in_bytes: Uint) -> U256:
    """
    Calculates the gas cost for allocating memory
    to the smallest multiple of 32 bytes,
    such that the allocated size is at least as big as the given size.

    Parameters
    ----------
    size_in_bytes :
        The size of the data in bytes.

    Returns
    -------
    total_gas_cost : `ethereum.base_types.U256`
        The gas cost for storing data in memory.
    """
    size_in_words = ceil32(size_in_bytes) // 32
    linear_cost = size_in_words * GAS_MEMORY
    quadratic_cost = size_in_words ** 2 // 512
    total_gas_cost = linear_cost + quadratic_cost
    return U256(total_gas_cost)


def calculate_gas_extend_memory(
    memory: bytearray, start_position: Uint, size: U256
) -> U256:
    """
    Calculates the gas amount to extend memory

    Parameters
    ----------
    memory :
        Memory contents of the EVM.
    start_position :
        Starting pointer to the memory.
    size:
        Amount of bytes by which the memory needs to be extended.

    Returns
    -------
    to_be_paid : `ethereum.base_types.U256`
        returns `0` if size=0 or if the
        size after extending memory is less than the size before extending
        else it returns the amount that needs to be paid for extendinng memory.
    """
    if size == 0:
        return U256(0)
    memory_size = Uint(len(memory))
    before_size = ceil32(memory_size)
    after_size = ceil32(start_position + size)
    if after_size <= before_size:
        return U256(0)
    already_paid = calculate_memory_gas_cost(before_size)
    total_cost = calculate_memory_gas_cost(after_size)
    to_be_paid = total_cost - already_paid
    return to_be_paid
