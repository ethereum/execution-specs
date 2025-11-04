"""
BLS12 381 Precompile.

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Precompile for BLS12-381 curve operations.
"""

from functools import lru_cache
from typing import Tuple

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint
from py_ecc.optimized_bls12_381.optimized_curve import (
    FQ,
    FQ2,
    b,
    b2,
    curve_order,
    is_inf,
    is_on_curve,
    normalize,
)
from py_ecc.optimized_bls12_381.optimized_curve import (
    multiply as bls12_multiply,
)
from py_ecc.typing import Optimized_Point3D as Point3D

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


# Note: Caching as a way to optimize client performance can create a DoS
# attack vector for worst-case inputs that trigger only cache misses. This
# should not be relied upon for client performance optimization in
# production systems.
@lru_cache(maxsize=128)
def _bytes_to_g1_cached(
    data: bytes,
    subgroup_check: bool = False,
) -> Point3D[FQ]:
    """
    Internal cached version of `bytes_to_g1` that works with hashable `bytes`.
    """
    if len(data) != 128:
        raise InvalidParameter("Input should be 128 bytes long")

    x = bytes_to_fq(data[:64])
    y = bytes_to_fq(data[64:])

    if x >= FQ.field_modulus:
        raise InvalidParameter("x >= field modulus")
    if y >= FQ.field_modulus:
        raise InvalidParameter("y >= field modulus")

    z = 1
    if x == 0 and y == 0:
        z = 0
    point = FQ(x), FQ(y), FQ(z)

    if not is_on_curve(point, b):
        raise InvalidParameter("G1 point is not on curve")

    if subgroup_check and not is_inf(bls12_multiply(point, curve_order)):
        raise InvalidParameter("Subgroup check failed for G1 point.")

    return point


def bytes_to_g1(
    data: Bytes,
    subgroup_check: bool = False,
) -> Point3D[FQ]:
    """
    Decode 128 bytes to a G1 point with or without subgroup check.

    Parameters
    ----------
    data :
        The bytes data to decode.
    subgroup_check : bool
        Whether to perform a subgroup check on the G1 point.

    Returns
    -------
    point : Point3D[FQ]
        The G1 point.

    Raises
    ------
    InvalidParameter
        If a field element is invalid, the point is not on the curve, or the
        subgroup check fails.

    """
    # This is needed bc when we slice `Bytes` we get a `bytearray`,
    # which is not hashable
    return _bytes_to_g1_cached(bytes(data), subgroup_check)


def g1_to_bytes(
    g1_point: Point3D[FQ],
) -> Bytes:
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
    return int(x).to_bytes(64, "big") + int(y).to_bytes(64, "big")


def decode_g1_scalar_pair(
    data: Bytes,
) -> Tuple[Point3D[FQ], int]:
    """
    Decode 160 bytes to a G1 point and a scalar.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Tuple[Point3D[FQ], int]
        The G1 point and the scalar.

    Raises
    ------
    InvalidParameter
        If the subgroup check failed.

    """
    if len(data) != 160:
        InvalidParameter("Input should be 160 bytes long")

    point = bytes_to_g1(data[:128], subgroup_check=True)

    m = int.from_bytes(buffer_read(data, U256(128), U256(32)), "big")

    return point, m


def bytes_to_fq(data: Bytes) -> FQ:
    """
    Decode 64 bytes to a FQ element.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    fq : FQ
        The FQ element.

    Raises
    ------
    InvalidParameter
        If the field element is invalid.

    """
    if len(data) != 64:
        raise InvalidParameter("FQ should be 64 bytes long")

    c = int.from_bytes(data[:64], "big")

    if c >= FQ.field_modulus:
        raise InvalidParameter("Invalid field element")

    return FQ(c)


def bytes_to_fq2(data: Bytes) -> FQ2:
    """
    Decode 128 bytes to an FQ2 element.

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
    if len(data) != 128:
        raise InvalidParameter("FQ2 input should be 128 bytes long")
    c_0 = int.from_bytes(data[:64], "big")
    c_1 = int.from_bytes(data[64:], "big")

    if c_0 >= FQ.field_modulus:
        raise InvalidParameter("Invalid field element")
    if c_1 >= FQ.field_modulus:
        raise InvalidParameter("Invalid field element")

    return FQ2((c_0, c_1))


# Note: Caching as a way to optimize client performance can create a DoS
# attack vector for worst-case inputs that trigger only cache misses. This
# should not be relied upon for client performance optimization in
# production systems.
@lru_cache(maxsize=128)
def _bytes_to_g2_cached(
    data: bytes,
    subgroup_check: bool = False,
) -> Point3D[FQ2]:
    """
    Internal cached version of `bytes_to_g2` that works with hashable `bytes`.
    """
    if len(data) != 256:
        raise InvalidParameter("G2 should be 256 bytes long")

    x = bytes_to_fq2(data[:128])
    y = bytes_to_fq2(data[128:])

    z = (1, 0)
    if x == FQ2((0, 0)) and y == FQ2((0, 0)):
        z = (0, 0)

    point = x, y, FQ2(z)

    if not is_on_curve(point, b2):
        raise InvalidParameter("Point is not on curve")

    if subgroup_check and not is_inf(bls12_multiply(point, curve_order)):
        raise InvalidParameter("Subgroup check failed for G2 point.")

    return point


def bytes_to_g2(
    data: Bytes,
    subgroup_check: bool = False,
) -> Point3D[FQ2]:
    """
    Decode 256 bytes to a G2 point with or without subgroup check.

    Parameters
    ----------
    data :
        The bytes data to decode.
    subgroup_check : bool
        Whether to perform a subgroup check on the G2 point.

    Returns
    -------
    point : Point3D[FQ2]
        The G2 point.

    Raises
    ------
    InvalidParameter
        If a field element is invalid, the point is not on the curve, or the
        subgroup check fails.

    """
    # This is needed bc when we slice `Bytes` we get a `bytearray`,
    # which is not hashable
    return _bytes_to_g2_cached(data, subgroup_check)


def fq2_to_bytes(fq2: FQ2) -> Bytes:
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
    coord0, coord1 = fq2.coeffs
    return int(coord0).to_bytes(64, "big") + int(coord1).to_bytes(64, "big")


def g2_to_bytes(
    g2_point: Point3D[FQ2],
) -> Bytes:
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
    return fq2_to_bytes(x_coords) + fq2_to_bytes(y_coords)


def decode_g2_scalar_pair(
    data: Bytes,
) -> Tuple[Point3D[FQ2], int]:
    """
    Decode 288 bytes to a G2 point and a scalar.

    Parameters
    ----------
    data :
        The bytes data to decode.

    Returns
    -------
    point : Tuple[Point3D[FQ2], int]
        The G2 point and the scalar.

    Raises
    ------
    InvalidParameter
        If the subgroup check failed.

    """
    if len(data) != 288:
        InvalidParameter("Input should be 288 bytes long")

    point = bytes_to_g2(data[:256], subgroup_check=True)
    n = int.from_bytes(data[256 : 256 + 32], "big")

    return point, n
