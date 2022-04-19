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

from typing import List

from ethereum.base_types import U255_CEIL_VALUE, U256, U256_CEIL_VALUE
from ethereum.utils.numeric import get_sign

from .. import Evm
from ..gas import (
    GAS_EXPONENTIATION,
    GAS_EXPONENTIATION_PER_BYTE,
    GAS_LOW,
    GAS_MID,
    GAS_VERY_LOW,
    subtract_gas,
)
from ..operation import Operation, static_gas


def do_add(evm: Evm, stack: List[U256], y: U256, x: U256) -> U256:
    """
    Adds the top two elements of the stack together, and pushes the result back
    on the stack.
    """
    return x.wrapping_add(y)


add = Operation(static_gas(GAS_VERY_LOW), do_add, 2, 1)


def do_sub(evm: Evm, stack: List[U256], y: U256, x: U256) -> U256:
    """
    Subtracts the top two elements of the stack, and pushes the result back
    on the stack.
    """
    return x.wrapping_sub(y)


sub = Operation(static_gas(GAS_VERY_LOW), do_sub, 2, 1)


def do_mul(evm: Evm, stack: List[U256], y: U256, x: U256) -> U256:
    """
    Multiply the top two elements of the stack, and pushes the result back
    on the stack.
    """
    return x.wrapping_mul(y)


mul = Operation(static_gas(GAS_LOW), do_mul, 2, 1)


def do_div(evm: Evm, stack: List[U256], divisor: U256, dividend: U256) -> U256:
    """
    Integer division of the top two elements of the stack. Pushes the result
    back on the stack.
    """
    if divisor == 0:
        return U256(0)
    else:
        return dividend // divisor


div = Operation(static_gas(GAS_LOW), do_div, 2, 1)


def do_sdiv(
    evm: Evm,
    stack: List[U256],
    divisor_u256: U256,
    dividend_u256: U256,
) -> U256:
    """
    Signed integer division of the top two elements of the stack. Pushes the
    result back on the stack.
    """
    dividend, divisor = dividend_u256.to_signed(), divisor_u256.to_signed()
    if divisor == 0:
        return U256(0)
    elif dividend == -U255_CEIL_VALUE and divisor == -1:
        return U256.from_signed(-U255_CEIL_VALUE)
    else:
        sign = get_sign(dividend) * get_sign(divisor)
        return U256.from_signed(sign * (abs(dividend) // abs(divisor)))


sdiv = Operation(static_gas(GAS_LOW), do_sdiv, 2, 1)


def do_mod(evm: Evm, stack: List[U256], y: U256, x: U256) -> U256:
    """
    Modulo remainder of the top two elements of the stack. Pushes the result
    back on the stack.
    """
    if y == 0:
        return U256(0)
    else:
        return x % y


mod = Operation(static_gas(GAS_LOW), do_mod, 2, 1)


def do_smod(evm: Evm, stack: List[U256], y: U256, x: U256) -> U256:
    """
    Signed modulo remainder of the top two elements of the stack. Pushes the
    result back on the stack.
    """
    if y == 0:
        return U256(0)
    else:
        remainder = get_sign(x.to_signed()) * (
            abs(x.to_signed()) % abs(y.to_signed())
        )

    return U256.from_signed(remainder)


smod = Operation(static_gas(GAS_LOW), do_smod, 2, 1)


def do_addmod(evm: Evm, stack: List[U256], z: U256, y: U256, x: U256) -> U256:
    """
    Modulo addition of the top 2 elements with the 3rd element. Pushes the
    result back on the stack.
    """
    if z == 0:
        return U256(0)
    else:
        return U256((int(x) + int(y)) % int(z))


addmod = Operation(static_gas(GAS_MID), do_addmod, 3, 1)


def do_mulmod(evm: Evm, stack: List[U256], z: U256, y: U256, x: U256) -> U256:
    """
    Modulo multiplication of the top 2 elements with the 3rd element. Pushes
    the result back on the stack.
    """
    if z == 0:
        return U256(0)
    else:
        return U256((int(x) * int(y)) % int(z))


mulmod = Operation(static_gas(GAS_MID), do_mulmod, 3, 1)


def gas_exp(evm: Evm, stack: List[U256], exponent: U256, base: U256) -> None:
    """
    Exponential operation of the top 2 elements. Pushes the result back on
    the stack.
    """
    gas_used = GAS_EXPONENTIATION
    if exponent != 0:
        # This is equivalent to 1 + floor(log(y, 256)). But in python the log
        # function is inaccurate leading to wrong results.
        exponent_bits = exponent.bit_length()
        exponent_bytes = (exponent_bits + 7) // 8
        gas_used += GAS_EXPONENTIATION_PER_BYTE * exponent_bytes
    subtract_gas(evm, gas_used)


def do_exp(evm: Evm, stack: List[U256], exponent: U256, base: U256) -> U256:
    """
    Exponential operation of the top 2 elements. Pushes the result back on
    the stack.
    """
    return U256(pow(base, exponent, U256_CEIL_VALUE))


exp = Operation(gas_exp, do_exp, 2, 1)


def do_signextend(
    evm: Evm, stack: List[U256], value: U256, byte_num: U256
) -> U256:
    """
    Sign extend operation. In other words, extend a signed number which
    fits in N bytes to 32 bytes.
    """
    if byte_num > 31:
        # Can't extend any further
        return value
    else:
        # U256(0).to_be_bytes() gives b'' instead b'\x00'. # noqa: SC100
        value_bytes = bytes(value.to_be_bytes32())
        # Now among the obtained value bytes, consider only
        # N `least significant bytes`, where N is `byte_num + 1`.
        value_bytes = value_bytes[31 - int(byte_num) :]
        sign_bit = value_bytes[0] >> 7
        if sign_bit == 0:
            return U256.from_be_bytes(value_bytes)
        else:
            num_bytes_prepend = 32 - (byte_num + 1)
            return U256.from_be_bytes(
                bytearray([0xFF] * num_bytes_prepend) + value_bytes
            )


signextend = Operation(static_gas(GAS_LOW), do_signextend, 2, 1)
