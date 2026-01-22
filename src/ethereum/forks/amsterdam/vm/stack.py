"""
Ethereum Virtual Machine (EVM) Stack.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of the stack operators for the EVM.
"""

from typing import List, Tuple

from ethereum_types.numeric import U8, U256

from .exceptions import (
    InvalidParameter,
    StackOverflowError,
    StackUnderflowError,
)


def decode_single(x: U8) -> U8:
    """
    Decode the immediate byte for DUPN/SWAPN to get the stack index.

    Parameters
    ----------
    x : int
        The immediate byte value (0-90 or 128-255).

    Returns
    -------
    int
        The stack index (17-235).

    Raises
    ------
    InvalidParameter
        If x is in the forbidden range (90 < x < 128 or x > 255).

    """
    if not (U8(0) <= x <= U8(90) or U8(128) <= x <= U8(255)):
        raise InvalidParameter(
            f"DUPN/SWAPN immediate byte {x} is out of range. "
            "Valid range: 0 <= x <= 90 or 128 <= x <= 255"
        )

    if x <= U8(90):
        return x + U8(17)
    else:
        return x - U8(20)


def decode_pair(x: U8) -> Tuple[U8, U8]:
    """
    Decode the immediate byte for EXCHANGE to get two stack indices.

    Parameters
    ----------
    x : int
        The immediate byte value (0-79 or 128-255).

    Returns
    -------
    Tuple[int, int]
        The two stack indices (n, m).

    Raises
    ------
    InvalidParameter
        If x is in the forbidden range (79 < x < 128 or x > 255).

    """
    if not (U8(0) <= x <= U8(79) or U8(128) <= x <= U8(255)):
        raise InvalidParameter(
            f"EXCHANGE immediate byte {x} is in the forbidden "
            "range 80 <= x <= 127\n"
            "Valid range: 0 <= x <= 79 or 128 <= x <= 255"
        )

    k = x if x <= U8(79) else x - U8(48)
    q, r = divmod(k, U8(16))
    if q < r:
        return q + U8(1), r + U8(1)
    else:
        return r + U8(1), U8(29) - q


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

    """
    if len(stack) == 1024:
        raise StackOverflowError

    return stack.append(value)
