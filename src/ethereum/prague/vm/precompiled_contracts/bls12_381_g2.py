"""
Ethereum Virtual Machine (EVM) BLS12 381 G2 CONTRACTS
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Implementation of pre-compiles in G2 (curve over base prime field).
"""
from typing import Tuple

from py_ecc.bls12_381.bls12_381_curve import (
    FQ2,
    add,
    b2,
    curve_order,
    is_on_curve,
    multiply,
)
from py_ecc.typing import Point2D

from ethereum.base_types import U256, Bytes, Uint

from ...vm import Evm
from ...vm.gas import charge_gas
from ...vm.memory import buffer_read
from ..exceptions import InvalidParameter

P = FQ2.field_modulus
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


def bytes_to_FQ2(data: Bytes) -> FQ2:
    """
    Decode 128 bytes to a FQ2 element.

    Parameters
    ----------
    data :
        The bytes data to decode.

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

    if c_0 >= P:
        raise InvalidParameter("Invalid field element")
    if c_1 >= P:
        raise InvalidParameter("Invalid field element")

    return FQ2((c_0, c_1))


def bytes_to_G2(data: Bytes) -> Point2D:
    """
    Decode 256 bytes to a G2 point.

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


def bls12_g2_add(evm: Evm) -> None:
    """
    The bls12_381 G2 point addition precompile.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    InvalidParameter
        If the input length is invalid.
    """
    data = evm.message.data
    if len(data) != 512:
        raise InvalidParameter("Invalid Input Length")

    # GAS
    charge_gas(evm, Uint(800))

    # OPERATION
    p1 = bytes_to_G2(buffer_read(data, U256(0), U256(256)))
    p2 = bytes_to_G2(buffer_read(data, U256(256), U256(256)))

    result = add(p1, p2)

    evm.output = G2_to_bytes(result)


def bls12_g2_multiply(evm: Evm) -> None:
    """
    The bls12_381 G2 multiplication precompile.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    InvalidParameter
        If the input length is invalid.
    """
    data = evm.message.data
    if len(data) != 288:
        raise InvalidParameter("Invalid Input Length")

    # GAS
    charge_gas(evm, Uint(45000))

    # OPERATION
    p, m = decode_G2_scalar_pair(data)
    result = multiply(p, m)

    evm.output = G2_to_bytes(result)


def bls12_g2_msm(evm: Evm) -> None:
    """
    The bls12_381 G2 multi-scalar multiplication precompile.
    Note: This uses the naive approach to multi-scalar multiplication
    which is not suitably optimized for production clients. Clients are
    required to implement a more efficient algorithm such as the Pippenger
    algorithm.

    Parameters
    ----------
    evm :
        The current EVM frame.

    Raises
    ------
    InvalidParameter
        If the input length is invalid.
    """
    data = evm.message.data
    if len(data) == 0 or len(data) % 288 != 0:
        raise InvalidParameter("Invalid Input Length")

    # GAS
    k = len(data) // 288
    if k <= 128:
        discount = K_DISCOUNT[k]
    else:
        discount = MAX_DISCOUNT

    gas_cost = Uint(k * 45000 * discount // MULTIPLIER)
    charge_gas(evm, gas_cost)

    # OPERATION
    for i in range(k):
        start_index = i * 288
        end_index = start_index + 288

        p, m = decode_G2_scalar_pair(data[start_index:end_index])
        product = multiply(p, m)

        if i == 0:
            result = product
        else:
            result = add(result, product)

    evm.output = G2_to_bytes(result)
