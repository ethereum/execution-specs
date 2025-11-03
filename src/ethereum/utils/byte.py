"""
Utility Functions For Byte Strings.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Byte specific utility functions used in this specification.
"""

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import FixedUnsigned, Uint


def left_pad_zero_bytes(
    value: Bytes, size: int | FixedUnsigned | Uint
) -> Bytes:
    """
    Left pad zeroes to `value` if its length is less than the given `size`.

    Parameters
    ----------
    value :
        The byte string that needs to be padded.
    size :
        The number of bytes that need to be padded.

    Returns
    -------
    left_padded_value: `ethereum.base_types.Bytes`
        left padded byte string of given `size`.

    """
    return value.rjust(int(size), b"\x00")


def right_pad_zero_bytes(
    value: Bytes, size: int | FixedUnsigned | Uint
) -> Bytes:
    """
    Right pad zeroes to `value` if its length is less than the given `size`.

    Parameters
    ----------
    value :
        The byte string that needs to be padded.
    size :
        The number of bytes that need to be padded.

    Returns
    -------
    right_padded_value: `ethereum.base_types.Bytes`
        right padded byte string of given `size`.

    """
    return value.ljust(int(size), b"\x00")


def count_bytes(data: Bytes) -> tuple[int, int]:
    """
    Count the number of zero and non-zero bytes in the given data.

    Parameters
    ----------
    data :
        The byte string to count bytes in.

    Returns
    -------
    (zero_bytes, nonzero_bytes) : tuple[int, int]
        A tuple containing the count of zero bytes and non-zero bytes.
    """
    zero_bytes = 0
    nonzero_bytes = 0
    
    for byte in data:
        if byte == 0:
            zero_bytes += 1
        else:
            nonzero_bytes += 1
    
    return zero_bytes, nonzero_bytes
