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

from ethereum.base_types import U256, U256_CEIL_VALUE

from .. import Evm
from ..gas import GAS_VERY_LOW, subtract_gas
from ..stack import pop, push


def bitwise_and(evm: Evm) -> None:
    """
    Bitwise AND operation of the top 2 elements of the stack. Pushes the
    result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.berlin.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `2`.
    :py:class:`~ethereum.berlin.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `GAS_VERY_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)
    x = pop(evm.stack)
    y = pop(evm.stack)
    push(evm.stack, x & y)

    evm.pc += 1


def bitwise_or(evm: Evm) -> None:
    """
    Bitwise OR operation of the top 2 elements of the stack. Pushes the
    result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.berlin.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `2`.
    :py:class:`~ethereum.berlin.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `GAS_VERY_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)
    x = pop(evm.stack)
    y = pop(evm.stack)
    push(evm.stack, x | y)

    evm.pc += 1


def bitwise_xor(evm: Evm) -> None:
    """
    Bitwise XOR operation of the top 2 elements of the stack. Pushes the
    result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.berlin.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `2`.
    :py:class:`~ethereum.berlin.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `GAS_VERY_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)
    x = pop(evm.stack)
    y = pop(evm.stack)
    push(evm.stack, x ^ y)

    evm.pc += 1


def bitwise_not(evm: Evm) -> None:
    """
    Bitwise NOT operation of the top element of the stack. Pushes the
    result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.berlin.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `1`.
    :py:class:`~ethereum.berlin.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `GAS_VERY_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)
    x = pop(evm.stack)
    push(evm.stack, ~x)

    evm.pc += 1


def get_byte(evm: Evm) -> None:
    """
    For a word (defined by next top element of the stack), retrieve the
    Nth byte (0-indexed and defined by top element of stack) from the
    left (most significant) to right (least significant).

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    :py:class:`~ethereum.berlin.vm.exceptions.StackUnderflowError`
        If `len(stack)` is less than `2`.
    :py:class:`~ethereum.berlin.vm.exceptions.OutOfGasError`
        If `evm.gas_left` is less than `GAS_VERY_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)
    # 0-indexed from left (most significant) to right (least significant)
    # in "Big Endian" representation.
    byte_index = pop(evm.stack)
    word = pop(evm.stack)

    if byte_index >= 32:
        result = U256(0)
    else:
        extra_bytes_to_right = 31 - byte_index
        # Remove the extra bytes in the right
        word = word >> (extra_bytes_to_right * 8)
        # Remove the extra bytes in the left
        word = word & 0xFF
        result = U256(word)

    push(evm.stack, result)

    evm.pc += 1


def bitwise_shl(evm: Evm) -> None:
    """
    Logical shift left (SHL) operation of the top 2 elements of the stack.
    Pushes the result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)
    shift = pop(evm.stack)
    value = pop(evm.stack)

    evm.pc += 1
    shifted_value = 0
    if shift < 256:
        shifted_value = (value << shift) % U256_CEIL_VALUE

    push(evm.stack, U256(shifted_value))


def bitwise_shr(evm: Evm) -> None:
    """
    Logical shift right (SHR) operation of the top 2 elements of the stack.
    Pushes the result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)
    shift = pop(evm.stack)
    value = pop(evm.stack)

    evm.pc += 1
    shifted_value = U256(0)
    if shift < 256:
        shifted_value = value >> shift

    push(evm.stack, shifted_value)


def bitwise_sar(evm: Evm) -> None:
    """
    Arithmetic shift right (SAR) operation of the top 2 elements of the stack.
    Pushes the result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)
    shift = pop(evm.stack)
    value = pop(evm.stack)

    signed_value = value.to_signed()

    evm.pc += 1
    if shift < 256:
        shifted_value = signed_value >> shift
    elif signed_value >= 0:
        shifted_value = 0
    else:
        shifted_value = U256.MAX_VALUE

    push(evm.stack, U256.from_signed(shifted_value))
