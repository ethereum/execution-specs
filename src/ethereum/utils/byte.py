"""
Utility Functions For Byte Strings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Byte specific utility functions used in this specification.
"""
from typing import Union

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import FixedUnsigned, Uint


def left_pad_zero_bytes(
    value: Bytes, size: Union[int, FixedUnsigned, Uint]
) -> Bytes:
    """
    Left pad zeroes to `value` if its length is less than the given `size`.

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
    return value.rjust(int(size), b"\x00")


def right_pad_zero_bytes(
    value: Bytes, size: Union[int, FixedUnsigned, Uint]
) -> Bytes:
    """
    Right pad zeroes to `value` if its length is less than the given `size`.

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
    return value.ljust(int(size), b"\x00")
