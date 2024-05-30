"""
BLS12 381 Precompile
^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Precompile for BLS12-381 curve operations.
"""
from typing import Tuple, Union

from py_ecc.bls12_381.bls12_381_curve import (
    FQ,
    FQ2,
    b,
    b2,
    curve_order,
    is_on_curve,
    multiply,
)
from py_ecc.optimized_bls12_381.optimized_curve import FQ2 as OPTIMIZED_FQ2
from py_ecc.typing import Point2D

from ethereum.base_types import U256, Bytes

from ....vm.memory import buffer_read
from ...exceptions import InvalidParameter

P = FQ.field_modulus
P2 = FQ2.field_modulus

K_DISCOUNT = {
    1: 1200,
    2: 888,
    3: 764,
    4: 641,
    5: 594,
    6: 547,
    7: 500,
    8: 453,
    9: 438,
    10: 423,
    11: 408,
    12: 394,
    13: 379,
    14: 364,
    15: 349,
    16: 334,
    17: 330,
    18: 326,
    19: 322,
    20: 318,
    21: 314,
    22: 310,
    23: 306,
    24: 302,
    25: 298,
    26: 294,
    27: 289,
    28: 285,
    29: 281,
    30: 277,
    31: 273,
    32: 269,
    33: 268,
    34: 266,
    35: 265,
    36: 263,
    37: 262,
    38: 260,
    39: 259,
    40: 257,
    41: 256,
    42: 254,
    43: 253,
    44: 251,
    45: 250,
    46: 248,
    47: 247,
    48: 245,
    49: 244,
    50: 242,
    51: 241,
    52: 239,
    53: 238,
    54: 236,
    55: 235,
    56: 233,
    57: 232,
    58: 231,
    59: 229,
    60: 228,
    61: 226,
    62: 225,
    63: 223,
    64: 222,
    65: 221,
    66: 220,
    67: 219,
    68: 219,
    69: 218,
    70: 217,
    71: 216,
    72: 216,
    73: 215,
    74: 214,
    75: 213,
    76: 213,
    77: 212,
    78: 211,
    79: 211,
    80: 210,
    81: 209,
    82: 208,
    83: 208,
    84: 207,
    85: 206,
    86: 205,
    87: 205,
    88: 204,
    89: 203,
    90: 202,
    91: 202,
    92: 201,
    93: 200,
    94: 199,
    95: 199,
    96: 198,
    97: 197,
    98: 196,
    99: 196,
    100: 195,
    101: 194,
    102: 193,
    103: 193,
    104: 192,
    105: 191,
    106: 191,
    107: 190,
    108: 189,
    109: 188,
    110: 188,
    111: 187,
    112: 186,
    113: 185,
    114: 185,
    115: 184,
    116: 183,
    117: 182,
    118: 182,
    119: 181,
    120: 180,
    121: 179,
    122: 179,
    123: 178,
    124: 177,
    125: 176,
    126: 176,
    127: 175,
    128: 174,
}

MAX_DISCOUNT = 174
MULTIPLIER = 1000


def bytes_to_G1(data: Bytes) -> Point2D:
    """
    Decode 128 bytes to a G1 point. Does not perform sub-group check.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Point2D
        The G1 point.

    Raises
    ------
    InvalidParameter
        Either a field element is invalid or the point is not on the curve.
    """
    assert len(data) == 128
    x = int.from_bytes(data[:64], "big")
    y = int.from_bytes(data[64:], "big")

    if x >= P:
        raise InvalidParameter("Invalid field element")
    if y >= P:
        raise InvalidParameter("Invalid field element")

    if x == 0 and y == 0:
        return None

    point = (FQ(x), FQ(y))

    # Check if the point is on the curve
    if not is_on_curve(point, b):
        raise InvalidParameter("Point is not on curve")

    return point


def G1_to_bytes(point: Point2D) -> Bytes:
    """
    Encode a G1 point to 128 bytes.

    Parameters
    ----------
    point :
        The G1 point to encode.

    Returns
    -------
    data : Bytes
        The encoded data.
    """
    if point is None:
        return b"\x00" * 128

    x, y = point

    x_bytes = int(x).to_bytes(64, "big")
    y_bytes = int(y).to_bytes(64, "big")

    return x_bytes + y_bytes


def decode_G1_scalar_pair(data: Bytes) -> Tuple[Point2D, int]:
    """
    Decode 160 bytes to a G1 point and a scalar.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Tuple[Point2D, int]
        The G1 point and the scalar.

    Raises
    ------
    InvalidParameter
        If the sub-group check failed.
    """
    assert len(data) == 160
    p = bytes_to_G1(buffer_read(data, U256(0), U256(128)))
    if multiply(p, curve_order) is not None:
        raise InvalidParameter("Sub-group check failed.")

    m = int.from_bytes(buffer_read(data, U256(128), U256(32)), "big")

    return p, m


def bytes_to_FQ2(
    data: Bytes, optimized: bool = False
) -> Union[FQ2, OPTIMIZED_FQ2]:
    """
    Decode 128 bytes to a FQ2 element.

    Parameters
    ----------
    data :
        The bytes data to decode.
    optimized :
        Whether to use the optimized FQ2 implementation.

    Returns
    -------
    fq2 : FQ2
        The FQ2 element.

    Raises
    ------
    InvalidParameter
        If the field element is invalid.
    """
    assert len(data) == 128
    c_0 = int.from_bytes(data[:64], "big")
    c_1 = int.from_bytes(data[64:], "big")

    if c_0 >= P2:
        raise InvalidParameter("Invalid field element")
    if c_1 >= P2:
        raise InvalidParameter("Invalid field element")

    if optimized:
        return OPTIMIZED_FQ2((c_0, c_1))
    else:
        return FQ2((c_0, c_1))


def bytes_to_G2(data: Bytes) -> Point2D:
    """
    Decode 256 bytes to a G2 point. Does not perform sub-group check.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Point2D
        The G2 point.

    Raises
    ------
    InvalidParameter
        Either a field element is invalid or the point is not on the curve.
    """
    assert len(data) == 256

    x = bytes_to_FQ2(data[:128])
    y = bytes_to_FQ2(data[128:])

    assert isinstance(x, FQ2) and isinstance(y, FQ2)
    if x == FQ2((0, 0)) and y == FQ2((0, 0)):
        return None

    point = (x, y)

    # Check if the point is on the curve
    if not is_on_curve(point, b2):
        raise InvalidParameter("Point is not on curve")

    return point


def FQ2_to_bytes(fq2: FQ2) -> Bytes:
    """
    Encode a FQ2 point to 128 bytes.

    Parameters
    ----------
    fq2 :
        The FQ2 point to encode.

    Returns
    -------
    data : Bytes
        The encoded data.
    """
    c_0, c_1 = fq2.coeffs
    return int(c_0).to_bytes(64, "big") + int(c_1).to_bytes(64, "big")


def G2_to_bytes(point: Point2D) -> Bytes:
    """
    Encode a G2 point to 256 bytes.

    Parameters
    ----------
    point :
        The G2 point to encode.

    Returns
    -------
    data : Bytes
        The encoded data.
    """
    if point is None:
        return b"\x00" * 256

    x, y = point

    return FQ2_to_bytes(x) + FQ2_to_bytes(y)


def decode_G2_scalar_pair(data: Bytes) -> Tuple[Point2D, int]:
    """
    Decode 288 bytes to a G2 point and a scalar.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Tuple[Point2D, int]
        The G2 point and the scalar.

    Raises
    ------
    InvalidParameter
        If the sub-group check failed.
    """
    assert len(data) == 288
    p = bytes_to_G2(buffer_read(data, U256(0), U256(256)))
    if multiply(p, curve_order) is not None:
        raise InvalidParameter("Sub-group check failed.")

    m = int.from_bytes(buffer_read(data, U256(256), U256(32)), "big")

    return p, m
