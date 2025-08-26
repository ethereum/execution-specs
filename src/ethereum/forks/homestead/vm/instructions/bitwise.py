"""
Ethereum Virtual Machine (EVM) Bitwise Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM bitwise instructions.
"""

from ethereum_types.numeric import U256, Uint

from .. import Evm
from ..gas import GAS_VERY_LOW, charge_gas
from ..stack import pop, push


def bitwise_and(evm: Evm) -> None:
    """
    Bitwise AND operation of the top 2 elements of the stack. Pushes the
    result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = pop(evm.stack)
    y = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    push(evm.stack, x & y)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def bitwise_or(evm: Evm) -> None:
    """
    Bitwise OR operation of the top 2 elements of the stack. Pushes the
    result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = pop(evm.stack)
    y = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    push(evm.stack, x | y)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def bitwise_xor(evm: Evm) -> None:
    """
    Bitwise XOR operation of the top 2 elements of the stack. Pushes the
    result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = pop(evm.stack)
    y = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    push(evm.stack, x ^ y)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def bitwise_not(evm: Evm) -> None:
    """
    Bitwise NOT operation of the top element of the stack. Pushes the
    result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    x = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    push(evm.stack, ~x)

    # PROGRAM COUNTER
    evm.pc += Uint(1)


def get_byte(evm: Evm) -> None:
    """
    For a word (defined by next top element of the stack), retrieve the
    Nth byte (0-indexed and defined by top element of stack) from the
    left (most significant) to right (least significant).

    Parameters
    ----------
    evm :
        The current EVM frame.

    """
    # STACK
    byte_index = pop(evm.stack)
    word = pop(evm.stack)

    # GAS
    charge_gas(evm, GAS_VERY_LOW)

    # OPERATION
    if byte_index >= U256(32):
        result = U256(0)
    else:
        extra_bytes_to_right = U256(31) - byte_index
        # Remove the extra bytes in the right
        word = word >> (extra_bytes_to_right * U256(8))
        # Remove the extra bytes in the left
        word = word & U256(0xFF)
        result = word

    push(evm.stack, result)

    # PROGRAM COUNTER
    evm.pc += Uint(1)
