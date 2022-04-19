"""
Ethereum Virtual Machine (EVM) Comparison Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM Comparison instructions.
"""
from typing import List

from ethereum.base_types import U256

from .. import Evm
from ..gas import GAS_VERY_LOW
from ..operation import Operation, static_gas


def do_less_than(evm: Evm, stack: List[U256], right: U256, left: U256) -> U256:
    """
    Checks if the top element is less than the next top element. Pushes the
    result back on the stack.
    """
    return U256(left < right)


less_than = Operation(static_gas(GAS_VERY_LOW), do_less_than, 2, 1)


def do_signed_less_than(
    evm: Evm, stack: List[U256], right: U256, left: U256
) -> U256:
    """
    Signed less-than comparison.
    """
    return U256(left.to_signed() < right.to_signed())


signed_less_than = Operation(
    static_gas(GAS_VERY_LOW), do_signed_less_than, 2, 1
)


def do_greater_than(
    evm: Evm, stack: List[U256], right: U256, left: U256
) -> U256:
    """
    Checks if the top element is greater than the next top element. Pushes
    the result back on the stack.
    """
    return U256(left > right)


greater_than = Operation(static_gas(GAS_VERY_LOW), do_greater_than, 2, 1)


def do_signed_greater_than(
    evm: Evm, stack: List[U256], right: U256, left: U256
) -> U256:
    """
    Signed greater-than comparison.
    """
    return U256(left.to_signed() > right.to_signed())


signed_greater_than = Operation(
    static_gas(GAS_VERY_LOW), do_signed_greater_than, 2, 1
)


def do_equal(evm: Evm, stack: List[U256], right: U256, left: U256) -> U256:
    """
    Checks if the top element is equal to the next top element. Pushes
    the result back on the stack.
    """
    return U256(left == right)


equal = Operation(static_gas(GAS_VERY_LOW), do_equal, 2, 1)


def do_is_zero(evm: Evm, stack: List[U256], x: U256) -> U256:
    """
    Checks if the top element is equal to 0. Pushes the result back on the
    stack.
    """
    return U256(x == 0)


is_zero = Operation(static_gas(GAS_VERY_LOW), do_is_zero, 1, 1)
