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
from ethereum.base_types import U8_MAX_VALUE, U256

from .. import Evm
from ..gas import GAS_BASE, GAS_VERY_LOW, subtract_gas
from ..memory import memory_read_bytes, memory_write, touch_memory
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

    Raises
    ------
    :py:class:`~ethereum.frontier.vm.error.StackUnderflowError`
        If `len(stack)` is less than `2`.
    :py:class:`~ethereum.frontier.vm.error.OutOfGasError`
        If `evm.gas_left` is less than
        `3` + gas needed to extend memeory.
    """
    start_position = pop(evm.stack)
    value = pop(evm.stack).to_be_bytes32()

    subtract_gas(evm, GAS_VERY_LOW)
    touch_memory(evm, start_position, U256(len(value)))

    memory_write(evm, start_position, value)

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

    Raises
    ------
    :py:class:`~ethereum.frontier.vm.error.StackUnderflowError`
        If `len(stack)` is less than `2`.
    :py:class:`~ethereum.frontier.vm.error.OutOfGasError`
        If `evm.gas_left` is less than
        `3` + gas needed to extend memory.
    """
    # convert to Uint as start_position + size_to_extend can overflow.
    start_position = pop(evm.stack)
    value = pop(evm.stack)
    # make sure that value doesn't exceed 1 byte
    normalized_bytes_value = (value & U8_MAX_VALUE).to_bytes(1, "big")

    subtract_gas(evm, GAS_VERY_LOW)
    touch_memory(evm, start_position, U256(1))

    memory_write(evm, start_position, normalized_bytes_value)

    evm.pc += 1


def mload(evm: Evm) -> None:
    """
    Load word from memory.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.frontier.vm.error.StackUnderflowError`
        If `len(stack)` is less than `1`.
    :py:class:`~ethereum.frontier.vm.error.OutOfGasError`
        If `evm.gas_left` is less than
        `3` + gas needed to extend memory.
    """
    # convert to Uint as start_position + size_to_extend can overflow.
    start_position = pop(evm.stack)
    subtract_gas(evm, GAS_VERY_LOW)
    touch_memory(evm, start_position, U256(32))

    # extend memory and subtract gas for allocating 32 bytes of memory
    value = U256.from_be_bytes(
        memory_read_bytes(evm, start_position, U256(32))
    )
    push(evm.stack, value)

    evm.pc += 1


def msize(evm: Evm) -> None:
    """
    Push the size of active memory in bytes onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.frontier.vm.error.OutOfGasError`
        If `evm.gas_left` is less than `2`
    """
    subtract_gas(evm, GAS_BASE)
    memory_size = U256(len(evm.memory))
    push(evm.stack, memory_size)

    evm.pc += 1
