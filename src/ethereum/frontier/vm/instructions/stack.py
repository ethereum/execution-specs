"""
Ethereum Virtual Machine (EVM) Stack Instructions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementations of the EVM stack related instructions.
"""

from functools import partial
from typing import List

from ethereum.base_types import U256
from ethereum.utils.ensure import ensure

from .. import Evm
from ..error import StackUnderflowError
from ..gas import GAS_BASE, GAS_VERY_LOW
from ..operation import Operation, static_gas


def do_pop(evm: Evm, stack: List[U256], _x: U256) -> None:
    """
    Remove item from stack.
    """
    pass


pop = Operation(static_gas(GAS_BASE), do_pop, 1, 0)


def do_push(n: int, evm: Evm, stack: List[U256]) -> U256:
    """
    Push an `n` byte intermediate onto the stack.
    """
    return U256.from_be_bytes(evm.code[evm.pc - n : evm.pc])


def push_n(n: int) -> Operation:
    """
    Push an `n` byte intermediate onto the stack.
    """
    return Operation(
        static_gas(GAS_VERY_LOW), partial(do_push, n), 0, 1, n + 1
    )


def do_dup(item_number: int, evm: Evm, stack: List[U256]) -> U256:
    """
    Duplicate the Nth stack item (from top of the stack) to the top of stack.
    """
    ensure(item_number <= len(stack), StackUnderflowError)
    return stack[-item_number]


def dup_n(item_number: int) -> Operation:
    """
    Duplicate the Nth stack item (from top of the stack) to the top of stack.
    """
    return Operation(
        static_gas(GAS_VERY_LOW), partial(do_dup, item_number), 0, 1
    )


def do_swap_n(item_number: int, evm: Evm, stack: List[U256]) -> None:
    """
    Swap the top and the `item_number` element of the stack, where
    the top of the stack is position zero.

    If `item_number` is zero, this function does nothing (which should not be
    possible, since there is no `SWAP0` instruction).
    """
    ensure(item_number < len(stack), StackUnderflowError)
    stack[-1], stack[-item_number - 1] = (
        stack[-item_number - 1],
        stack[-1],
    )


def swap_n(item_number: int) -> Operation:
    """
    Swap the top and the `item_number` element of the stack, where
    the top of the stack is position zero.

    If `item_number` is zero, this function does nothing (which should not be
    possible, since there is no `SWAP0` instruction).
    """
    return Operation(
        static_gas(GAS_VERY_LOW), partial(do_swap_n, item_number), 0, 0
    )
