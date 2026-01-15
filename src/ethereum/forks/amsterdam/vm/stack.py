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

from ethereum_types.numeric import U256

from .exceptions import (
    InvalidParameter,
    StackOverflowError,
    StackUnderflowError,
)


def decode_single(x: int) -> int:
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
        If x is in the forbidden range (90 < x < 128).

    """
    if not (0 <= x <= 90 or 128 <= x <= 255):
        raise InvalidParameter
    if x <= 90:
        return x + 17
    else:
        return x - 20


def decode_pair(x: int) -> Tuple[int, int]:
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
        If x is in the forbidden range (79 < x < 128).

    """
    if not (0 <= x <= 79 or 128 <= x <= 255):
        raise InvalidParameter
    k = x if x <= 79 else x - 48
    q, r = divmod(k, 16)
    if q < r:
        return q + 1, r + 1
    else:
        return r + 1, 29 - q


def encode_single(n: int) -> int:
    """
    Encode a stack index to the immediate byte for DUPN/SWAPN.

    Parameters
    ----------
    n : int
        The stack index (17-235).

    Returns
    -------
    int
        The immediate byte value.

    """
    assert 17 <= n <= 235
    if n <= 107:
        return n - 17
    else:
        return n + 20


def encode_pair(n: int, m: int) -> int:
    """
    Encode two stack indices to the immediate byte for EXCHANGE.

    Parameters
    ----------
    n : int
        The first stack index (1-13).
    m : int
        The second stack index (must be > n, up to 29, and n + m <= 30).

    Returns
    -------
    int
        The immediate byte value.

    """
    assert 1 <= n <= 13 and n < m <= 29 and n + m <= 30
    if m <= 16:
        q, r = n - 1, m - 1
    else:
        q, r = 29 - m, n - 1
    k = 16 * q + r
    return k if k <= 79 else k + 48


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
