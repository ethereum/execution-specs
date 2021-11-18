"""
Ethereum Virtual Machine (EVM) Stack
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the stack operators for the EVM.
"""

from typing import List

from ethereum.base_types import U256

from .error import StackOverflowError, StackUnderflowError


def pop(stack: List[U256]) -> U256:
    """
    Pops the top item off of `stack`.

    Parameters
    ----------
    stack :
        EVM stack.

    Returns
    -------
    value : `U256`
        The top element on the stack.

    Raises
    ------
    ethereum.homestead.vm.error.StackUnderflowError
        If `stack` is empty.
    """
    if len(stack) == 0:
        raise StackUnderflowError

    return stack.pop()


def push(stack: List[U256], value: U256) -> None:
    """
    Pushes `value` onto `stack`.

    Parameters
    ----------
    stack :
        EVM stack.

    value :
        Item to be pushed onto `stack`.

    Raises
    ------
    ethereum.homestead.vm.error.StackOverflowError
        If `len(stack)` is `1024`.
    """
    if len(stack) == 1024:
        raise StackOverflowError

    return stack.append(value)
