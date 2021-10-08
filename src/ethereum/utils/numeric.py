"""
Utility Functions For Numeric Operations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Numeric operations specific utility functions used in this specification.
"""
from typing import Sequence, Tuple

from ethereum.base_types import Uint, Uint32


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


def is_prime(number: int) -> bool:
    """
    Checks if `number` is a prime number.

    Parameters
    ----------
    number :
        The number to check for primality.

    Returns
    -------
    is_number_prime : `bool`
        Boolean indicating if `number` is prime or not.
    """
    if number <= 1:
        return False

    # number ** 0.5 is faster than math.sqrt(number)
    for x in range(2, int(number ** 0.5) + 1):
        # Return False if number is divisible by x
        if number % x == 0:
            return False

    return True


def le_bytes_to_uint32_sequence(data: bytes) -> Tuple[Uint32, ...]:
    """
    Convert little endian byte stream `data` to a little endian Uint32
    sequence i.e., the first Uint32 number of the sequence is the least
    significant Uint32 number.

    Parameters
    ----------
    data :
        The byte stream (little endian) which is to be converted to a Uint32
        stream.

    Returns
    -------
    uint32_sequence : `Tuple[Uint32, ...]`
        Sequence of Uint32 numbers obtained from the little endian byte
        stream.
    """
    sequence = []
    for i in range(0, len(data), 4):
        sequence.append(Uint32.from_le_bytes(data[i : i + 4]))

    return tuple(sequence)


def le_uint32_sequence_to_bytes(sequence: Sequence[Uint32]) -> bytes:
    r"""
    Obtain little endian byte stream from a little endian Uint32 sequence
    i.e., the first Uint32 number of the sequence is the least significant
    Uint32 number.

    Note - In this conversion, the most significant byte (byte at the end of
    the little endian stream) may have leading zeroes. This function doesn't
    take care of removing these leading zeroes as shown in below example.

    >>> le_uint32_sequence_to_bytes([Uint32(8)])
    b'\x08\x00\x00\x00'


    Parameters
    ----------
    sequence :
        The Uint32 stream (little endian) which is to be converted to a
        little endian byte stream.

    Returns
    -------
    result : `bytes`
        The byte stream obtained from the little endian Uint32 stream.
    """
    result_bytes = b""
    for item in sequence:
        result_bytes += item.to_le_bytes4()

    return result_bytes


def le_uint32_sequence_to_uint(sequence: Sequence[Uint32]) -> Uint:
    """
    Obtain Uint from a Uint32 sequence assuming that this sequence is little
    endian i.e., the first Uint32 number of the sequence is the least
    significant Uint32 number.

    Parameters
    ----------
    sequence :
        The Uint32 stream (little endian) which is to be converted to a Uint.

    Returns
    -------
    value : `Uint`
        The Uint number obtained from the conversion of the little endian
        Uint32 stream.
    """
    sequence_as_bytes = le_uint32_sequence_to_bytes(sequence)
    return Uint.from_le_bytes(sequence_as_bytes)
