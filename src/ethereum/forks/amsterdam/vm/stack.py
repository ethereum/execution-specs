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

    Return n with 17 <= n <= 235.

    Parameters
    ----------
    x : int
        The immediate byte value (0-90 or 128-255).

    Returns
    -------
    int
        The stack index n, where 17 <= n <= 235.

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

    return U8((int(x) + 145) % 256)


def decode_pair(x: U8) -> Tuple[U8, U8]:
    """
    Decode the immediate byte for EXCHANGE to get two stack indices.

    Return (n, m) with 1 <= n <= 14 and n < m <= 30 - n.

    Parameters
    ----------
    x : int
        The immediate byte value (0-81 or 128-255).

    Returns
    -------
    Tuple[int, int]
        The two stack indices (n, m), where
        1 <= n <= 14 and n < m <= 30 - n.

    Raises
    ------
    InvalidParameter
        If x is in the forbidden range (81 < x < 128 or x > 255).

    """
    if not (U8(0) <= x <= U8(81) or U8(128) <= x <= U8(255)):
        raise InvalidParameter(
            f"EXCHANGE immediate byte {x} is in the forbidden "
            "range 82 <= x <= 127\n"
            "Valid range: 0 <= x <= 81 or 128 <= x <= 255"
        )

    k = U8(int(x) ^ 143)
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
