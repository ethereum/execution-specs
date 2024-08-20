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
from py_ecc.optimized_bls12_381.optimized_curve import FQ as OPTIMIZED_FQ
from py_ecc.optimized_bls12_381.optimized_curve import FQ2 as OPTIMIZED_FQ2
from py_ecc.typing import Point2D

from ethereum.base_types import U256, Bytes

from ....vm.memory import buffer_read
from ...exceptions import InvalidParameter

P = FQ.field_modulus

K_DISCOUNT = [
    1200,
    888,
    764,
    641,
    594,
    547,
    500,
    453,
    438,
    423,
    408,
    394,
    379,
    364,
    349,
    334,
    330,
    326,
    322,
    318,
    314,
    310,
    306,
    302,
    298,
    294,
    289,
    285,
    281,
    277,
    273,
    269,
    268,
    266,
    265,
    263,
    262,
    260,
    259,
    257,
    256,
    254,
    253,
    251,
    250,
    248,
    247,
    245,
    244,
    242,
    241,
    239,
    238,
    236,
    235,
    233,
    232,
    231,
    229,
    228,
    226,
    225,
    223,
    222,
    221,
    220,
    219,
    219,
    218,
    217,
    216,
    216,
    215,
    214,
    213,
    213,
    212,
    211,
    211,
    210,
    209,
    208,
    208,
    207,
    206,
    205,
    205,
    204,
    203,
    202,
    202,
    201,
    200,
    199,
    199,
    198,
    197,
    196,
    196,
    195,
    194,
    193,
    193,
    192,
    191,
    191,
    190,
    189,
    188,
    188,
    187,
    186,
    185,
    185,
    184,
    183,
    182,
    182,
    181,
    180,
    179,
    179,
    178,
    177,
    176,
    176,
    175,
    174,
]

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
    if len(data) != 128:
        raise InvalidParameter("Input should be 128 bytes long")

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
    if len(data) != 160:
        InvalidParameter("Input should be 160 bytes long")

    p = bytes_to_G1(buffer_read(data, U256(0), U256(128)))
    if multiply(p, curve_order) is not None:
        raise InvalidParameter("Sub-group check failed.")

    m = int.from_bytes(buffer_read(data, U256(128), U256(32)), "big")

    return p, m


def bytes_to_FQ(
    data: Bytes, optimized: bool = False
) -> Union[FQ, OPTIMIZED_FQ]:
    """
    Decode 64 bytes to a FQ element.

    Parameters
    ----------
    data :
        The bytes data to decode.
    optimized :
        Whether to use the optimized FQ implementation.

    Returns
    -------
    fq : Union[FQ, OPTIMIZED_FQ]
        The FQ element.

    Raises
    ------
    InvalidParameter
        If the field element is invalid.
    """
    if len(data) != 64:
        raise InvalidParameter("FQ should be 64 bytes long")

    c = int.from_bytes(data[:64], "big")

    if c >= P:
        raise InvalidParameter("Invalid field element")

    if optimized:
        return OPTIMIZED_FQ(c)
    else:
        return FQ(c)


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
    fq2 : Union[FQ2, OPTIMIZED_FQ2]
        The FQ2 element.

    Raises
    ------
    InvalidParameter
        If the field element is invalid.
    """
    if len(data) != 128:
        raise InvalidParameter("FQ2 input should be 128 bytes long")
    c_0 = int.from_bytes(data[:64], "big")
    c_1 = int.from_bytes(data[64:], "big")

    if c_0 >= P:
        raise InvalidParameter("Invalid field element")
    if c_1 >= P:
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
    if len(data) != 256:
        raise InvalidParameter("G2 should be 256 bytes long")

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
    if len(data) != 288:
        InvalidParameter("Input should be 288 bytes long")

    p = bytes_to_G2(buffer_read(data, U256(0), U256(256)))
    if multiply(p, curve_order) is not None:
        raise InvalidParameter("Sub-group check failed.")

    m = int.from_bytes(buffer_read(data, U256(256), U256(32)), "big")

    return p, m
