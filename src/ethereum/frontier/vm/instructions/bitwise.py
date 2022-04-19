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
from typing import List

from ethereum.base_types import U256

from .. import Evm
from ..gas import GAS_VERY_LOW
from ..operation import Operation, static_gas


def do_bitwise_and(evm: Evm, stack: List[U256], y: U256, x: U256) -> U256:
    """
    Bitwise AND operation of the top 2 elements of the stack. Pushes the
    result back on the stack.
    """
    return x & y


bitwise_and = Operation(static_gas(GAS_VERY_LOW), do_bitwise_and, 2, 1)


def do_bitwise_or(evm: Evm, stack: List[U256], y: U256, x: U256) -> U256:
    """
    Bitwise OR operation of the top 2 elements of the stack. Pushes the
    result back on the stack.
    """
    return x | y


bitwise_or = Operation(static_gas(GAS_VERY_LOW), do_bitwise_or, 2, 1)


def do_bitwise_xor(evm: Evm, stack: List[U256], y: U256, x: U256) -> U256:
    """
    Bitwise XOR operation of the top 2 elements of the stack. Pushes the
    result back on the stack.
    """
    return x ^ y


bitwise_xor = Operation(static_gas(GAS_VERY_LOW), do_bitwise_xor, 2, 1)


def do_bitwise_not(evm: Evm, stack: List[U256], x: U256) -> U256:
    """
    Bitwise NOT operation of the top element of the stack. Pushes the
    result back on the stack.
    """
    return ~x


bitwise_not = Operation(static_gas(GAS_VERY_LOW), do_bitwise_not, 1, 1)


def do_get_byte(
    evm: Evm, stack: List[U256], word: U256, byte_index: U256
) -> U256:
    """
    For a word (defined by next top element of the stack), retrieve the
    Nth byte (0-indexed and defined by top element of stack) from the
    left (most significant) to right (least significant).
    """
    if byte_index >= 32:
        return U256(0)
    else:
        extra_bytes_to_right = 31 - byte_index
        # Remove the extra bytes in the right
        word = word >> (extra_bytes_to_right * 8)
        # Remove the extra bytes in the left
        word = word & 0xFF
        return U256(word)


get_byte = Operation(static_gas(GAS_VERY_LOW), do_get_byte, 2, 1)
