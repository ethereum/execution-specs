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

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint
from py_ecc.optimized_bls12_381.optimized_curve import FQ as OPTIMIZED_FQ
from py_ecc.optimized_bls12_381.optimized_curve import FQ2 as OPTIMIZED_FQ2
from py_ecc.optimized_bls12_381.optimized_curve import FQP as OPTIMIZED_FQP
from py_ecc.optimized_bls12_381.optimized_curve import (
    b,
    b2,
    curve_order,
    is_inf,
    is_on_curve,
)
from py_ecc.optimized_bls12_381.optimized_curve import (
    multiply as bls12_multiply_optimized,
)
from py_ecc.optimized_bls12_381.optimized_curve import normalize
from py_ecc.typing import Optimized_Point3D

from ....vm.memory import buffer_read
from ...exceptions import InvalidParameter

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


def bytes_to_g1(
    data: bytes,
) -> Optimized_Point3D[OPTIMIZED_FQ]:
    """
    Decode 128 bytes to a G1 point. Does not perform sub-group check.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Optimized_Point3D[OPTIMIZED_FQ]
        The G1 point.

    Raises
    ------
    InvalidParameter
        Either a field element is invalid or the point is not on the curve.
    """
    if len(data) != 128:
        raise InvalidParameter("Input should be 128 bytes long")

    x = bytes_to_fq(data[:64])
    y = bytes_to_fq(data[64:])

    if x >= OPTIMIZED_FQ.field_modulus:
        raise InvalidParameter("x >= field modulus")
    if y >= OPTIMIZED_FQ.field_modulus:
        raise InvalidParameter("y >= field modulus")

    z = 0 if (x == 0 and y == 0) else 1
    point = OPTIMIZED_FQ(x), OPTIMIZED_FQ(y), OPTIMIZED_FQ(z)

    if not is_on_curve(point, b):
        raise InvalidParameter("Point is not on curve")

    return point


def g1_to_bytes(
    g1_point: Optimized_Point3D[OPTIMIZED_FQ],
) -> bytes:
    """
    Encode a G1 point to 128 bytes.

    Parameters
    ----------
    g1_point :
        The G1 point to encode.

    Returns
    -------
    data : Bytes
        The encoded data.
    """
    g1_normalized = normalize(g1_point)
    x, y = g1_normalized
    return b"".join([int(x).to_bytes(64, "big"), int(y).to_bytes(64, "big")])


def decode_g1_scalar_pair(
    data: bytes,
) -> Tuple[Optimized_Point3D[OPTIMIZED_FQ], int]:
    """
    Decode 160 bytes to a G1 point and a scalar.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Tuple[Optimized_Point3D[OPTIMIZED_FQ], int]
        The G1 point and the scalar.

    Raises
    ------
    InvalidParameter
        If the sub-group check failed.
    """
    if len(data) != 160:
        InvalidParameter("Input should be 160 bytes long")

    point = bytes_to_g1(data[:128])
    if not is_inf(bls12_multiply_optimized(point, curve_order)):
        raise InvalidParameter("Sub-group check failed.")

    m = int.from_bytes(buffer_read(data, U256(128), U256(32)), "big")

    return point, m


def bytes_to_fq(data: Bytes) -> OPTIMIZED_FQ:
    """
    Decode 64 bytes to a OPTIMIZED_FQ element.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    fq : OPTIMIZED_FQ
        The OPTIMIZED_FQ element.

    Raises
    ------
    InvalidParameter
        If the field element is invalid.
    """
    if len(data) != 64:
        raise InvalidParameter("FQ should be 64 bytes long")

    c = int.from_bytes(data[:64], "big")

    if c >= OPTIMIZED_FQ.field_modulus:
        raise InvalidParameter("Invalid field element")

    return OPTIMIZED_FQ(c)


def bytes_to_fq2(data: Bytes) -> Union[OPTIMIZED_FQ2, OPTIMIZED_FQ2]:
    """
    Decode 128 bytes to an OPTIMIZED_FQ2 element.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    fq2 : Union[OPTIMIZED_FQ2, OPTIMIZED_FQP]
        The OPTIMIZED_FQ2 element.

    Raises
    ------
    InvalidParameter
        If the field element is invalid.
    """
    if len(data) != 128:
        raise InvalidParameter("FQ2 input should be 128 bytes long")
    c_0 = int.from_bytes(data[:64], "big")
    c_1 = int.from_bytes(data[64:], "big")

    if c_0 >= OPTIMIZED_FQ.field_modulus:
        raise InvalidParameter("Invalid field element")
    if c_1 >= OPTIMIZED_FQ.field_modulus:
        raise InvalidParameter("Invalid field element")

    return OPTIMIZED_FQ2((c_0, c_1))


def bytes_to_g2(
    data: bytes,
) -> Optimized_Point3D[OPTIMIZED_FQ2]:
    """
    Decode 256 bytes to a G2 point. Does not perform sub-group check.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Optimized_Point3D[OPTIMIZED_FQ2]
        The G2 point.

    Raises
    ------
    InvalidParameter
        Either a field element is invalid or the point is not on the curve.
    """
    if len(data) != 256:
        raise InvalidParameter("G2 should be 256 bytes long")

    x = bytes_to_fq2(data[:128])
    y = bytes_to_fq2(data[128:])

    z = (
        (0, 0)
        if x == OPTIMIZED_FQ2((0, 0)) and y == OPTIMIZED_FQ2((0, 0))
        else (1, 0)
    )
    point = x, y, OPTIMIZED_FQ2(z)

    # Check if the point is on the curve
    if not is_on_curve(point, b2):
        raise InvalidParameter("Point is not on curve")

    return point


def FQ2_to_bytes(fq2: Union[OPTIMIZED_FQ2, OPTIMIZED_FQP]) -> bytes:
    """
    Encode a OPTIMIZED_FQ2 point to 128 bytes.

    Parameters
    ----------
    fq2 :
        The OPTIMIZED_FQ2 point to encode.

    Returns
    -------
    data : Bytes
        The encoded data.
    """
    coord0, coord1 = fq2.coeffs
    return b"".join(
        [
            int(coord0).to_bytes(64, "big"),
            int(coord1).to_bytes(64, "big"),
        ]
    )


def g2_to_bytes(
    g2_point: Optimized_Point3D[OPTIMIZED_FQ2],
) -> bytes:
    """
    Encode a G2 point to 256 bytes.

    Parameters
    ----------
    g2_point :
        The G2 point to encode.

    Returns
    -------
    data : Bytes
        The encoded data.
    """
    x_coords, y_coords = normalize(g2_point)
    return b"".join([FQ2_to_bytes(x_coords), FQ2_to_bytes(y_coords)])


def decode_g2_scalar_pair(
    data: bytes,
) -> Tuple[Optimized_Point3D[OPTIMIZED_FQ2], int]:
    """
    Decode 288 bytes to a G2 point and a scalar.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Tuple[Optimized_Point3D[OPTIMIZED_FQ2], int]
        The G2 point and the scalar.

    Raises
    ------
    InvalidParameter
        If the sub-group check failed.
    """
    if len(data) != 288:
        InvalidParameter("Input should be 288 bytes long")

    point = bytes_to_g2(data[:256])

    if not is_inf(bls12_multiply_optimized(point, curve_order)):
        raise InvalidParameter("Point failed sub-group check.")

    n = int.from_bytes(data[256 : 256 + 32], "big")

    return point, n
