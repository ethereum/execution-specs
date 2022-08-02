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
from ..gas import GAS_BASE, GAS_VERY_LOW, charge_gas
from ..memory import extend_memory, memory_read_bytes, memory_write
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
    :py:class:`~ethereum.frontier.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `2`.
    :py:class:`~ethereum.frontier.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than
        `3` + gas needed to extend memeory.
    """
    # STACK
    start_position = pop(evm.stack)
    value = pop(evm.stack).to_be_bytes32()

    # GAS
    extend_memory(evm, start_position, U256(len(value)))
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
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

    Raises
    ------
    :py:class:`~ethereum.frontier.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `2`.
    :py:class:`~ethereum.frontier.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than
        `3` + gas needed to extend memory.
    """
    # STACK
    start_position = pop(evm.stack)
    value = pop(evm.stack)

    # GAS
    extend_memory(evm, start_position, U256(1))
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    normalized_bytes_value = (value & U8_MAX_VALUE).to_bytes(1, "big")
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

    Raises
    ------
    :py:class:`~ethereum.frontier.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `1`.
    :py:class:`~ethereum.frontier.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than
        `3` + gas needed to extend memory.
    """
    # STACK
    start_position = pop(evm.stack)

    # GAS
    extend_memory(evm, start_position, U256(32))
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
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

    Raises
    ------
    :py:class:`~ethereum.frontier.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `2`
    """
    # STACK
    pass

    # GAS
    charge_gas(evm, GAS_BASE)

    # OPERATION
    push(evm.stack, U256(len(evm.memory)))

    # PROGRAM COUNTER
    evm.pc += 1
