"""
Utility Functions For Numeric Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Numeric operations specific utility functions used in this application.
"""
from ethereum.base_types import Uint


def get_sign(value: int) -> int:
    """
    Determines the sign of a number.

    Parameters
    ----------
    value :
        The value whose sign is to be determined.

    Returns
    -------
    sign : `int`
        The sign of the number (-1 or 0 or 1).
        The return value is based on math signum function.
    """
    if value < 0:
        return -1
    elif value == 0:
        return 0
    else:
        return 1


def ceil32(value: Uint) -> Uint:
    """
    Converts a unsigned integer to the next closest multiple of 32.

    Parameters
    ----------
    value :
        The value whose ceil32 is to be calculated.

    Returns
    -------
    ceil32 : `ethereum.base_types.U256`
        The same value if it's a perfect multiple of 32
        else it returns the smallest multiple of 32
        that is greater than `value`.
    """
    ceiling = Uint(32)
    remainder = value % ceiling
    if remainder == Uint(0):
        return value
    else:
        return value + ceiling - remainder
