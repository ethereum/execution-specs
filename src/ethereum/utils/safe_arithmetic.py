"""
Safe Arithmetic for U256 Integer Type
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Safe arithmetic utility functions for U256 integer type.
"""
from typing import Optional, Type, Union

from ethereum_types.numeric import U256, Uint


def u256_safe_add(
    *numbers: Union[U256, Uint],
    exception_type: Optional[Type[BaseException]] = None
) -> U256:
    """
    Adds together the given sequence of numbers. If the total sum of the
    numbers exceeds `U256.MAX_VALUE` then an exception is raised.
    If `exception_type` = None then the exception raised defaults to the one
    raised by `U256` when `U256.value > U256.MAX_VALUE`
    else `exception_type` is raised.

    Parameters
    ----------
    numbers :
        The sequence of numbers that need to be added together.

    exception_type:
        The exception that needs to be raised if the sum of the `numbers`
        exceeds `U256.MAX_VALUE`.

    Returns
    -------
    result : `ethereum.base_types.U256`
        The sum of the given sequence of numbers if the total is less than
        `U256.MAX_VALUE` else an exception is raised.
        If `exception_type` = None then the exception raised defaults to the
        one raised by `U256` when `U256.value > U256.MAX_VALUE`
        else `exception_type` is raised.
    """
    try:
        return U256(sum(int(n) for n in numbers))
    except ValueError as e:
        if exception_type:
            raise exception_type from e
        else:
            raise e


def u256_safe_multiply(
    *numbers: Union[U256, Uint],
    exception_type: Optional[Type[BaseException]] = None
) -> U256:
    """
    Multiplies together the given sequence of numbers. If the net product of
    the numbers exceeds `U256.MAX_VALUE` then an exception is raised.
    If `exception_type` = None then the exception raised defaults to the one
    raised by `U256` when `U256.value > U256.MAX_VALUE` else
    `exception_type` is raised.

    Parameters
    ----------
    numbers :
        The sequence of numbers that need to be multiplies together.

    exception_type:
        The exception that needs to be raised if the sum of the `numbers`
        exceeds `U256.MAX_VALUE`.

    Returns
    -------
    result : `ethereum.base_types.U256`
        The multiplication product of the given sequence of numbers if the
        net product  is less than `U256.MAX_VALUE` else an exception is raised.
        If `exception_type` = None then the exception raised defaults to the
        one raised by `U256` when `U256.value > U256.MAX_VALUE`
        else `exception_type` is raised.
    """
    result = Uint(numbers[0])
    try:
        for number in numbers[1:]:
            result *= Uint(number)
        return U256(result)
    except ValueError as e:
        if exception_type:
            raise exception_type from e
        else:
            raise e
