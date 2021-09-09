"""
Utility Functions For Byte Strings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Byte specific utility functions used in this specification.
"""
from ethereum.base_types import Bytes


def left_pad_zero_bytes(value: Bytes, size: int) -> Bytes:
    """
    Left pad zeroes to `value` if it's length is less than the given `size`.

    Parameters
    ----------
    value :
        The byte string that needs to be padded.
    size :
        The number of bytes that need that need to be padded.

    Returns
    -------
    left_padded_value: `ethereum.base_types.Bytes`
        left padded byte string of given `size`.
    """
    return value.rjust(size, b"\x00")


def right_pad_zero_bytes(value: Bytes, size: int) -> Bytes:
    """
    Right pad zeroes to `value` if it's length is less than the given `size`.

    Parameters
    ----------
    value :
        The byte string that needs to be padded.
    size :
        The number of bytes that need that need to be padded.

    Returns
    -------
    right_padded_value: `ethereum.base_types.Bytes`
        right padded byte string of given `size`.
    """
    return value.ljust(size, b"\x00")
