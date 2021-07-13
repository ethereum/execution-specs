"""
Ethereum Virtual Machine (EVM) Memory Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM memory instructions.
"""

from ethereum.base_types import U256, Uint
from ethereum.utils import get_ceil32

from .. import Evm
from ..gas import GAS_BASE, GAS_VERY_LOW, subtract_gas
from ..memory import expand_memory
from ..stack import pop, push

MAX_BYTE_VALUE = 0xFF


def mload(evm: Evm) -> None:
    """
    Load word (32 bytes) from memory and push it onto the stack.

    This also expands the memory, incase the memory is insufficient to access
    the word's memory location.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `1`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)

    # Converting memory_start_index to Uint and memory_end_index can
    # overflow U256.
    memory_start_index = Uint(pop(evm.stack))
    required_memory_size = memory_start_index + 32

    if len(evm.memory) < required_memory_size:
        # The required memory indices are not present. Hence we need to
        # expand the memory and reduce the corresponding gas for that.
        expand_memory(evm, memory_size=get_ceil32(required_memory_size))

    word = evm.memory[memory_start_index : memory_start_index + 32]
    push(evm.stack, U256.from_be_bytes(word))


def mstore(evm: Evm) -> None:
    """
    Save word (32 bytes) to memory.

    This also expands the memory in multiples of words, if the memory is
    insufficient to store the word.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)

    # Converting memory_start_index to Uint and memory_end_index can
    # overflow U256.
    memory_start_index = Uint(pop(evm.stack))
    required_memory_size = memory_start_index + 32
    word = pop(evm.stack).to_be_bytes32()

    if len(evm.memory) < required_memory_size:
        # The required memory indices are not present. Hence we need to
        # expand the memory and reduce the corresponding gas for that.
        expand_memory(evm, memory_size=get_ceil32(required_memory_size))

    evm.memory[memory_start_index : memory_start_index + 32] = word


def mstore8(evm: Evm) -> None:
    """
    Save a byte to memory.

    This also expands the memory, if the memory is insufficient to store
    the byte.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)

    # The index in memory at which the byte would be written.
    memory_index = Uint(pop(evm.stack))
    required_memory_size = memory_index + 1
    # Obtain the least significant byte from the word.
    byte = pop(evm.stack) & MAX_BYTE_VALUE

    if len(evm.memory) < required_memory_size:
        # The required memory indices are not present. Hence we need to
        # expand the memory and reduce the corresponding gas for that.
        expand_memory(evm, memory_size=get_ceil32(required_memory_size))

    evm.memory[memory_index] = byte


def msize(evm: Evm) -> None:
    """
    Get the size of active memory in bytes. Also pushes this onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    OutOfGasError
        If `evm.gas_left` is less than `2`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_BASE)
    push(evm.stack, U256(len(evm.memory)))
