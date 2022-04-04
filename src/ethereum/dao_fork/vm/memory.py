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
from ethereum.utils.numeric import ceil32
from ethereum.utils.safe_arithmetic import u256_safe_add

from ...base_types import U256, Bytes, Uint
from . import Evm
from .error import OutOfGasError
from .gas import calculate_memory_gas_cost, subtract_gas


def extend_memory(evm: Evm, new_size: U256) -> None:
    """
    Extend memory to `new_size` and charge the appropriate amount of gas.

    Parameters
    ----------
    evm :
        Current state of the EVM.
    new_size :
        The new size of the memory.
    """
    before_size = Uint(len(evm.memory))
    after_size = ceil32(Uint(new_size))
    if after_size <= before_size:
        return None
    subtract_gas(
        evm,
        calculate_memory_gas_cost(after_size)
        - calculate_memory_gas_cost(before_size),
    )
    evm.memory += b"\x00" * (after_size - before_size)


def touch_memory(evm: Evm, start_position: U256, size: U256) -> None:
    """
    Extend memory as if a read or write at `start_position` of length `size`
    had occured and charge the appropriate amount of gas.

    Parameters
    ----------
    evm :
        Current state of the EVM.
    start_position :
        Starting pointer to the memory.
    size :
        Size of memory.
    """
    if size == 0:
        return
    end_position = u256_safe_add(
        start_position, size, exception_type=OutOfGasError
    )
    if len(evm.memory) < end_position:
        extend_memory(evm, end_position)


def memory_write(evm: Evm, start_position: U256, value: Bytes) -> None:
    """
    Writes to memory. If necessary, extend memory and charge the appropriate
    amount of gas.

    Parameters
    ----------
    evm :
        Current state of the EVM.
    start_position :
        Starting pointer to the memory.
    value :
        Data to write to memory.
    """
    if len(value) == 0:
        return
    end_position = u256_safe_add(
        start_position, U256(len(value)), exception_type=OutOfGasError
    )
    if len(evm.memory) < end_position:
        extend_memory(evm, end_position)
    evm.memory[start_position:end_position] = value


def memory_read_bytes(evm: Evm, start_position: U256, size: U256) -> Bytes:
    """
    Read bytes from memory. If necessary, extend memory and charge the
    appropriate amount of gas.

    Parameters
    ----------
    evm :
        Current state of the Evm.
    start_position :
        Starting pointer to the memory.
    size :
        Size of the data that needs to be read from `start_position`.

    Returns
    -------
    data_bytes :
        Data read from memory.
    """
    if size == 0:
        return Bytes()
    end_position = u256_safe_add(
        start_position, size, exception_type=OutOfGasError
    )
    if len(evm.memory) < end_position:
        extend_memory(evm, end_position)
    return Bytes(evm.memory[start_position:end_position])
