"""
Ethereum Virtual Machine (EVM) Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the instructions understood by the EVM.
"""


from ..base_types import U256
from . import Evm
from .gas import (
    GAS_STORAGE_CLEAR_REFUND,
    GAS_STORAGE_SET,
    GAS_STORAGE_UPDATE,
    GAS_VERY_LOW,
    subtract_gas,
)
from .stack import pop, push


def add(evm: Evm) -> None:
    """
    Adds the top two elements of the stack together, and pushes the result back
    on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    OutOfGasError
        If `evm.gas_left` is less than `GAS_VERY_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)

    x = pop(evm.stack)
    y = pop(evm.stack)

    val = x.wrapping_add(y)

    push(evm.stack, val)


def sstore(evm: Evm) -> None:
    """
    Stores a value at a certain key in the current context's storage.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    OutOfGasError
        If `evm.gas_left` is less than `20000`.
    """
    key = pop(evm.stack).to_be_bytes32()
    new_value = pop(evm.stack)
    current_value = evm.env.state[evm.current].storage.get(key, U256(0))

    # TODO: SSTORE gas usage hasn't been tested yet. Testing this needs
    # other opcodes to be implemented.
    # Calculating the gas needed for the storage
    if new_value != 0 and current_value == 0:
        gas_cost = GAS_STORAGE_SET
    else:
        gas_cost = GAS_STORAGE_UPDATE

    evm.gas_left = subtract_gas(evm.gas_left, gas_cost)

    # TODO: Refund counter hasn't been tested yet. Testing this needs other
    # Opcodes to be implemented
    if new_value == 0 and current_value != 0:
        evm.refund_counter += GAS_STORAGE_CLEAR_REFUND

    if new_value == 0:
        del evm.env.state[evm.current].storage[key]
    else:
        evm.env.state[evm.current].storage[key] = new_value


def push1(evm: Evm) -> None:
    """
    Pushes a one-byte immediate onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackOverflowError
        If `len(stack)` is equals `1024`.
    OutOfGasError
        If `evm.gas_left` is less than `GAS_VERY_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)
    push(evm.stack, U256(evm.code[evm.pc + 1]))
    evm.pc += 1
