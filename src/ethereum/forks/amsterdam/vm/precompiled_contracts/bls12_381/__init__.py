"""
BLS12 381 Precompile.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Precompile for BLS12-381 curve operations.
"""

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import Uint

from ...exceptions import InvalidParameter

ZERO_PAD = b"\x00" * 16


def unpad_fp(data: Bytes) -> Bytes:
    """
    Remove the 16-byte zero padding from a 64-byte field element.

    Parameters
    ----------
    data :
        The 64-byte big-endian padded field element.

    Returns
    -------
    raw : Bytes
        The 48-byte unpadded field element.

    Raises
    ------
    InvalidParameter
        If the leading 16 bytes are not zero.

    """
    if data[:16] != ZERO_PAD:
        raise InvalidParameter("Invalid field element")
    return data[16:]


def unpad_g1(data: Bytes) -> bytes:
    """
    Strip padding from a 128-byte G1 encoding to 96 raw bytes.

    Parameters
    ----------
    data :
        The 128-byte padded G1 point.

    Returns
    -------
    raw : bytes
        The 96-byte unpadded G1 point.

    Raises
    ------
    InvalidParameter
        If the padding is invalid.

    """
    x = unpad_fp(data[:64])
    y = unpad_fp(data[64:])
    return bytes(x + y)


def unpad_g2(data: Bytes) -> bytes:
    """
    Strip padding from a 256-byte G2 encoding to 192 raw bytes.

    Parameters
    ----------
    data :
        The 256-byte padded G2 point.

    Returns
    -------
    raw : bytes
        The 192-byte unpadded G2 point.

    Raises
    ------
    InvalidParameter
        If the padding is invalid.

    """
    c0_x = unpad_fp(data[:64])
    c1_x = unpad_fp(data[64:128])
    c0_y = unpad_fp(data[128:192])
    c1_y = unpad_fp(data[192:256])
    return bytes(c0_x + c1_x + c0_y + c1_y)


def pad_g1(raw: bytes) -> Bytes:
    """
    Add 16-byte zero padding to a 96-byte G1 point.

    Parameters
    ----------
    raw :
        The 96-byte raw G1 point.

    Returns
    -------
    padded : Bytes
        The 128-byte padded G1 point.

    """
    x = raw[:48]
    y = raw[48:]
    return ZERO_PAD + x + ZERO_PAD + y


def pad_g2(raw: bytes) -> Bytes:
    """
    Add 16-byte zero padding to a 192-byte G2 point.

    Parameters
    ----------
    raw :
        The 192-byte raw G2 point.

    Returns
    -------
    padded : Bytes
        The 256-byte padded G2 point.

    """
    c0_x = raw[:48]
    c1_x = raw[48:96]
    c0_y = raw[96:144]
    c1_y = raw[144:]
    return (
        ZERO_PAD + c0_x + ZERO_PAD + c1_x + ZERO_PAD + c0_y + ZERO_PAD + c1_y
    )


G1_K_DISCOUNT = [
    1000,
    949,
    848,
    797,
    764,
    750,
    738,
    728,
    719,
    712,
    705,
    698,
    692,
    687,
    682,
    677,
    673,
    669,
    665,
    661,
    658,
    654,
    651,
    648,
    645,
    642,
    640,
    637,
    635,
    632,
    630,
    627,
    625,
    623,
    621,
    619,
    617,
    615,
    613,
    611,
    609,
    608,
    606,
    604,
    603,
    601,
    599,
    598,
    596,
    595,
    593,
    592,
    591,
    589,
    588,
    586,
    585,
    584,
    582,
    581,
    580,
    579,
    577,
    576,
    575,
    574,
    573,
    572,
    570,
    569,
    568,
    567,
    566,
    565,
    564,
    563,
    562,
    561,
    560,
    559,
    558,
    557,
    556,
    555,
    554,
    553,
    552,
    551,
    550,
    549,
    548,
    547,
    547,
    546,
    545,
    544,
    543,
    542,
    541,
    540,
    540,
    539,
    538,
    537,
    536,
    536,
    535,
    534,
    533,
    532,
    532,
    531,
    530,
    529,
    528,
    528,
    527,
    526,
    525,
    525,
    524,
    523,
    522,
    522,
    521,
    520,
    520,
    519,
]

G2_K_DISCOUNT = [
    1000,
    1000,
    923,
    884,
    855,
    832,
    812,
    796,
    782,
    770,
    759,
    749,
    740,
    732,
    724,
    717,
    711,
    704,
    699,
    693,
    688,
    683,
    679,
    674,
    670,
    666,
    663,
    659,
    655,
    652,
    649,
    646,
    643,
    640,
    637,
    634,
    632,
    629,
    627,
    624,
    622,
    620,
    618,
    615,
    613,
    611,
    609,
    607,
    606,
    604,
    602,
    600,
    598,
    597,
    595,
    593,
    592,
    590,
    589,
    587,
    586,
    584,
    583,
    582,
    580,
    579,
    578,
    576,
    575,
    574,
    573,
    571,
    570,
    569,
    568,
    567,
    566,
    565,
    563,
    562,
    561,
    560,
    559,
    558,
    557,
    556,
    555,
    554,
    553,
    552,
    552,
    551,
    550,
    549,
    548,
    547,
    546,
    545,
    545,
    544,
    543,
    542,
    541,
    541,
    540,
    539,
    538,
    537,
    537,
    536,
    535,
    535,
    534,
    533,
    532,
    532,
    531,
    530,
    530,
    529,
    528,
    528,
    527,
    526,
    526,
    525,
    524,
    524,
]

G1_MAX_DISCOUNT = 519
G2_MAX_DISCOUNT = 524
MULTIPLIER = Uint(1000)
