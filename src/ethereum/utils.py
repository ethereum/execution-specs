"""
Utility Functions
^^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Utility functions used in this application.
"""


def get_sign(value: int) -> int:
    """
    Determines the sign of a number.

    Parameters
    ----------
    value :
        The value whose sign is to be determined.

    Returns
    -------
    sign :
        The sign of the number (-1 or 0 or 1).
        The return value is based on math signum function.
    """
    if value < 0:
        return -1
    elif value == 0:
        return 0
    else:
        return 1


def get_ceil32(value: int) -> int:
    """
    Get the nearest multiple of 32.

    If the value is already a perfect multiple of 32 then the resut is same
    as the input.

    Parameters
    ----------
    value :
        The value for which we want to obtain the ceil value.

    Returns
    -------
    ceil32 :
        The ceil value which is the nearest multiple of 32.
    """
    return 32 * ((value + 31) // 32)
