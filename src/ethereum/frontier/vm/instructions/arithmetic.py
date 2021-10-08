"""
Ethereum Virtual Machine (EVM) Arithmetic Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM Arithmetic instructions.
"""

from ethereum.base_types import U255_CEIL_VALUE, U256, U256_CEIL_VALUE, Uint
from ethereum.utils.numeric import get_sign

from .. import Evm
from ..gas import (
    GAS_EXPONENTIATION,
    GAS_LOW,
    GAS_MID,
    GAS_VERY_LOW,
    subtract_gas,
)
from ..stack import pop, push


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
        If `evm.gas_left` is less than `3`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)

    x = pop(evm.stack)
    y = pop(evm.stack)
    result = x.wrapping_add(y)

    push(evm.stack, result)

    evm.pc += 1


def sub(evm: Evm) -> None:
    """
    Subtracts the top two elements of the stack, and pushes the result back
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
        If `evm.gas_left` is less than `3`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)

    x = pop(evm.stack)
    y = pop(evm.stack)
    result = x.wrapping_sub(y)

    push(evm.stack, result)

    evm.pc += 1


def mul(evm: Evm) -> None:
    """
    Multiply the top two elements of the stack, and pushes the result back
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
        If `evm.gas_left` is less than `5`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_LOW)

    x = pop(evm.stack)
    y = pop(evm.stack)
    result = x.wrapping_mul(y)

    push(evm.stack, result)

    evm.pc += 1


def div(evm: Evm) -> None:
    """
    Integer division of the top two elements of the stack. Pushes the result
    back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    OutOfGasError
        If `evm.gas_left` is less than `5`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_LOW)

    dividend = pop(evm.stack)
    divisor = pop(evm.stack)
    if divisor == 0:
        quotient = U256(0)
    else:
        quotient = dividend // divisor

    push(evm.stack, quotient)

    evm.pc += 1


def sdiv(evm: Evm) -> None:
    """
    Signed integer division of the top two elements of the stack. Pushes the
    result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    OutOfGasError
        If `evm.gas_left` is less than `5`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_LOW)

    dividend = pop(evm.stack).to_signed()
    divisor = pop(evm.stack).to_signed()

    if divisor == 0:
        quotient = 0
    elif dividend == -U255_CEIL_VALUE and divisor == -1:
        quotient = -U255_CEIL_VALUE
    else:
        sign = get_sign(dividend * divisor)
        quotient = sign * (abs(dividend) // abs(divisor))

    push(evm.stack, U256.from_signed(quotient))

    evm.pc += 1


def mod(evm: Evm) -> None:
    """
    Modulo remainder of the top two elements of the stack. Pushes the result
    back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    OutOfGasError
        If `evm.gas_left` is less than `5`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_LOW)

    x = pop(evm.stack)
    y = pop(evm.stack)
    if y == 0:
        remainder = U256(0)
    else:
        remainder = x % y

    push(evm.stack, remainder)

    evm.pc += 1


def smod(evm: Evm) -> None:
    """
    Signed modulo remainder of the top two elements of the stack. Pushes the
    result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    OutOfGasError
        If `evm.gas_left` is less than `5`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_LOW)

    x = pop(evm.stack).to_signed()
    y = pop(evm.stack).to_signed()

    if y == 0:
        remainder = 0
    else:
        remainder = get_sign(x) * (abs(x) % abs(y))

    push(evm.stack, U256.from_signed(remainder))

    evm.pc += 1


def addmod(evm: Evm) -> None:
    """
    Modulo addition of the top 2 elements with the 3rd element. Pushes the
    result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `3`.
    OutOfGasError
        If `evm.gas_left` is less than `8`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_MID)

    x = Uint(pop(evm.stack))
    y = Uint(pop(evm.stack))
    z = Uint(pop(evm.stack))

    if z == 0:
        result = U256(0)
    else:
        result = U256((x + y) % z)

    push(evm.stack, result)

    evm.pc += 1


def mulmod(evm: Evm) -> None:
    """
    Modulo multiplication of the top 2 elements with the 3rd element. Pushes
    the result back on the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `3`.
    OutOfGasError
        If `evm.gas_left` is less than `8`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_MID)

    x = Uint(pop(evm.stack))
    y = Uint(pop(evm.stack))
    z = Uint(pop(evm.stack))

    if z == 0:
        result = U256(0)
    else:
        result = U256((x * y) % z)

    push(evm.stack, result)

    evm.pc += 1


def exp(evm: Evm) -> None:
    """
    Exponential operation of the top 2 elements. Pushes the result back on
    the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    """
    base = Uint(pop(evm.stack))
    exponent = Uint(pop(evm.stack))

    gas_used = GAS_EXPONENTIATION
    if exponent != 0:
        # This is equivalent to 1 + floor(log(y, 256)). But in python the log
        # function is inaccurate leading to wrong results.
        exponent_bits = exponent.bit_length()
        exponent_bytes = (exponent_bits + 7) // 8
        gas_used += GAS_EXPONENTIATION * exponent_bytes
    evm.gas_left = subtract_gas(evm.gas_left, gas_used)

    result = U256(pow(base, exponent, U256_CEIL_VALUE))

    push(evm.stack, result)

    evm.pc += 1


def signextend(evm: Evm) -> None:
    """
    Sign extend operation. In other words, extend a signed number which
    fits in N bytes to 32 bytes.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    StackUnderflowError
        If `len(stack)` is less than `2`.
    OutOfGasError
        If `evm.gas_left` is less than `5`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_LOW)

    # byte_num would be 0-indexed when inserted to the stack.
    byte_num = pop(evm.stack)
    value = pop(evm.stack)

    if byte_num > 31:
        # Can't extend any further
        result = value
    else:
        # U256(0).to_be_bytes() gives b'' instead b'\x00'. # noqa: SC100
        value_bytes = value.to_be_bytes() or b"\x00"

        # Now among the obtained value bytes, consider only
        # N `least significant bytes`, where N is `byte_num + 1`.
        value_bytes = value_bytes[len(value_bytes) - 1 - int(byte_num) :]
        sign_bit = value_bytes[0] >> 7
        if sign_bit == 0:
            result = U256.from_be_bytes(value_bytes)
        else:
            num_bytes_prepend = 32 - (byte_num + 1)
            result = U256.from_be_bytes(
                bytearray([0xFF] * num_bytes_prepend) + value_bytes
            )

    push(evm.stack, result)

    evm.pc += 1
