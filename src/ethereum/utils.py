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
    value : `int`
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
