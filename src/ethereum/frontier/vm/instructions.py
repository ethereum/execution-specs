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


from functools import partial

from ethereum.base_types import U255_CEIL_VALUE, U256, U256_CEIL_VALUE, Uint
from ethereum.utils import get_sign

from . import Evm
from .gas import (
    GAS_EXPONENTIATION,
    GAS_LOW,
    GAS_MID,
    GAS_STORAGE_CLEAR_REFUND,
    GAS_STORAGE_SET,
    GAS_STORAGE_UPDATE,
    GAS_VERY_LOW,
    subtract_gas,
)
from .stack import pop, push


def stop(evm: Evm) -> None:
    """
    Stop further execution of EVM code.

    Parameters
    ----------
    evm :
        The current EVM frame.
    """
    evm.running = False


#
# Arithmetic Operations
#


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
    result = x.wrapping_add(y)

    push(evm.stack, result)


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
        If `evm.gas_left` is less than `GAS_VERY_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)

    x = pop(evm.stack)
    y = pop(evm.stack)
    result = x.wrapping_sub(y)

    push(evm.stack, result)


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
        If `evm.gas_left` is less than `GAS_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_LOW)

    x = pop(evm.stack)
    y = pop(evm.stack)
    result = x.wrapping_mul(y)

    push(evm.stack, result)


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
        If `evm.gas_left` is less than `GAS_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_LOW)

    dividend = pop(evm.stack)
    divisor = pop(evm.stack)
    if divisor == 0:
        quotient = U256(0)
    else:
        quotient = dividend // divisor

    push(evm.stack, quotient)


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
        If `evm.gas_left` is less than `GAS_LOW`.
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
        If `evm.gas_left` is less than `GAS_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_LOW)

    x = pop(evm.stack)
    y = pop(evm.stack)
    if y == 0:
        remainder = U256(0)
    else:
        remainder = x % y

    push(evm.stack, remainder)


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
        If `evm.gas_left` is less than `GAS_LOW`.
    """
    evm.gas_left = subtract_gas(evm.gas_left, GAS_LOW)

    x = pop(evm.stack).to_signed()
    y = pop(evm.stack).to_signed()

    if y == 0:
        remainder = 0
    else:
        remainder = get_sign(x) * (abs(x) % abs(y))

    push(evm.stack, U256.from_signed(remainder))


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
        If `evm.gas_left` is less than `GAS_MID`.
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
        If `evm.gas_left` is less than `GAS_MID`.
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
    OutOfGasError
        If `evm.gas_left` is less than `GAS_MID`.
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
        If `evm.gas_left` is less than `GAS_LOW`.
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
        value_bytes = value_bytes[len(value_bytes) - 1 - byte_num :]
        sign_bit = value_bytes[0] >> 7
        if sign_bit == 0:
            result = U256.from_be_bytes(value_bytes)
        else:
            num_bytes_prepend = 32 - (byte_num + 1)
            result = U256.from_be_bytes(
                bytearray([0xFF] * num_bytes_prepend) + value_bytes
            )

    push(evm.stack, result)


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
        # Deletes a k-v pair from dict if key is present, else does nothing
        evm.env.state[evm.current].storage.pop(key, None)
    else:
        evm.env.state[evm.current].storage[key] = new_value


def push_n(evm: Evm, num_bytes: int) -> None:
    """
    Pushes a N-byte immediate onto the stack.

    Parameters
    ----------
    evm :
        The current EVM frame.

    num_bytes : `int`
        The number of immediate bytes to be read from the code and pushed to
        the stack.

    Raises
    ------
    StackOverflowError
        If `len(stack)` is equals `1024`.
    OutOfGasError
        If `evm.gas_left` is less than `GAS_VERY_LOW`.
    """
    assert evm.pc + num_bytes < len(evm.code)
    evm.gas_left = subtract_gas(evm.gas_left, GAS_VERY_LOW)

    data_to_push = U256.from_be_bytes(
        evm.code[evm.pc + 1 : evm.pc + num_bytes + 1]
    )
    push(evm.stack, data_to_push)

    evm.pc += num_bytes


push1 = partial(push_n, num_bytes=1)
push2 = partial(push_n, num_bytes=2)
push3 = partial(push_n, num_bytes=3)
push4 = partial(push_n, num_bytes=4)
push5 = partial(push_n, num_bytes=5)
push6 = partial(push_n, num_bytes=6)
push7 = partial(push_n, num_bytes=7)
push8 = partial(push_n, num_bytes=8)
push9 = partial(push_n, num_bytes=9)
push10 = partial(push_n, num_bytes=10)
push11 = partial(push_n, num_bytes=11)
push12 = partial(push_n, num_bytes=12)
push13 = partial(push_n, num_bytes=13)
push14 = partial(push_n, num_bytes=14)
push15 = partial(push_n, num_bytes=15)
push16 = partial(push_n, num_bytes=16)
push17 = partial(push_n, num_bytes=17)
push18 = partial(push_n, num_bytes=18)
push19 = partial(push_n, num_bytes=19)
push20 = partial(push_n, num_bytes=20)
push21 = partial(push_n, num_bytes=21)
push22 = partial(push_n, num_bytes=22)
push23 = partial(push_n, num_bytes=23)
push24 = partial(push_n, num_bytes=24)
push25 = partial(push_n, num_bytes=25)
push26 = partial(push_n, num_bytes=26)
push27 = partial(push_n, num_bytes=27)
push28 = partial(push_n, num_bytes=28)
push29 = partial(push_n, num_bytes=29)
push30 = partial(push_n, num_bytes=30)
push31 = partial(push_n, num_bytes=31)
push32 = partial(push_n, num_bytes=32)
