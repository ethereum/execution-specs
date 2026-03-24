"""
Byte-level interface to BLS12-381 curve operations.

All inputs and outputs are raw (unpadded) bytes.
"""

from typing import Sequence

from py_ecc.bls.hash_to_curve import (
    clear_cofactor_G1,
    clear_cofactor_G2,
    map_to_curve_G1,
    map_to_curve_G2,
)
from py_ecc.optimized_bls12_381 import FQ12, pairing
from py_ecc.optimized_bls12_381 import multiply as bls12_multiply
from py_ecc.optimized_bls12_381.optimized_curve import (
    FQ,
    FQ2,
    Z1,
    Z2,
    b,
    b2,
    curve_order,
    is_inf,
    is_on_curve,
    normalize,
)
from py_ecc.optimized_bls12_381.optimized_curve import add as bls12_add
from py_ecc.typing import Optimized_Point3D as Point3D


def bytes_to_g1(raw: bytes) -> Point3D[FQ]:
    """
    Decode a 96-byte raw G1 point to a py-ecc Point3D.

    Validate that field elements are in range and the point is on the
    curve.
    """
    if len(raw) != 96:
        raise ValueError("G1 point must be 96 bytes")

    x = int.from_bytes(raw[:48], "big")
    if x >= FQ.field_modulus:
        raise ValueError("x coordinate >= field modulus")

    y = int.from_bytes(raw[48:], "big")
    if y >= FQ.field_modulus:
        raise ValueError("y coordinate >= field modulus")

    z = 1
    if x == 0 and y == 0:
        z = 0

    point: Point3D[FQ] = (FQ(x), FQ(y), FQ(z))
    if not is_on_curve(point, b):
        raise ValueError("G1 point is not on curve")
    return point


def g1_to_bytes(point: Point3D[FQ]) -> bytes:
    """Encode a py-ecc G1 point to 96 raw bytes."""
    x, y = normalize(point)
    return int(x).to_bytes(48, "big") + int(y).to_bytes(48, "big")


def bytes_to_g2(raw: bytes) -> Point3D[FQ2]:
    """
    Decode a 192-byte raw G2 point to a py-ecc Point3D.

    Validate that field elements are in range and the point is on the
    curve.
    """
    if len(raw) != 192:
        raise ValueError("G2 point must be 192 bytes")

    c0_x = int.from_bytes(raw[:48], "big")
    if c0_x >= FQ.field_modulus:
        raise ValueError("coordinate >= field modulus")

    c1_x = int.from_bytes(raw[48:96], "big")
    if c1_x >= FQ.field_modulus:
        raise ValueError("coordinate >= field modulus")

    c0_y = int.from_bytes(raw[96:144], "big")
    if c0_y >= FQ.field_modulus:
        raise ValueError("coordinate >= field modulus")

    c1_y = int.from_bytes(raw[144:], "big")

    if c1_y >= FQ.field_modulus:
        raise ValueError("coordinate >= field modulus")

    x = FQ2((c0_x, c1_x))
    y = FQ2((c0_y, c1_y))

    z: FQ2
    if x == FQ2((0, 0)) and y == FQ2((0, 0)):
        z = FQ2((0, 0))
    else:
        z = FQ2((1, 0))

    point: Point3D[FQ2] = (x, y, z)

    if not is_on_curve(point, b2):
        raise ValueError("G2 point is not on curve")
    return point


def g2_to_bytes(point: Point3D[FQ2]) -> bytes:
    """Encode a py-ecc G2 point to 192 raw bytes."""
    x, y = normalize(point)
    c0_x, c1_x = x.coeffs
    c0_y, c1_y = y.coeffs
    return (
        int(c0_x).to_bytes(48, "big")
        + int(c1_x).to_bytes(48, "big")
        + int(c0_y).to_bytes(48, "big")
        + int(c1_y).to_bytes(48, "big")
    )


def g1_add(a: bytes, b_point: bytes) -> bytes:
    """
    Add two G1 points.

    `a` and `b_point` are 96-byte G1 points.
    Return the 96-byte sum as a G1 point.
    """
    p1 = bytes_to_g1(a)
    p2 = bytes_to_g1(b_point)
    return g1_to_bytes(bls12_add(p1, p2))


def g2_add(a: bytes, b_point: bytes) -> bytes:
    """
    Add two G2 points.

    `a` and `b_point` are 192-byte G2 points.
    Return the 192-byte sum as a G2 point.
    """
    p1 = bytes_to_g2(a)
    p2 = bytes_to_g2(b_point)
    return g2_to_bytes(bls12_add(p1, p2))


def g1_msm(
    points: Sequence[bytes],
    scalars: Sequence[bytes],
) -> bytes:
    """
    G1 multi-scalar multiplication with subgroup checks.

    `points` is a sequence of 96-byte G1 points and `scalars` is a
    sequence of 32-byte big-endian scalars.
    Return the 96-byte result as a G1 point.

    Raise `ValueError` if a point is not on the curve or fails the
    subgroup check.
    """
    result: Point3D[FQ] = Z1
    for raw_point, raw_scalar in zip(points, scalars, strict=True):
        point = bytes_to_g1(raw_point)
        if not is_inf(bls12_multiply(point, curve_order)):
            raise ValueError("Subgroup check failed for G1 point")

        m = int.from_bytes(raw_scalar, "big")
        product = bls12_multiply(point, m)
        result = bls12_add(result, product)

    return g1_to_bytes(result)


def g2_msm(
    points: Sequence[bytes],
    scalars: Sequence[bytes],
) -> bytes:
    """
    G2 multi-scalar multiplication with subgroup checks.

    `points` is a sequence of 192-byte G2 points and `scalars` is a
    sequence of 32-byte big-endian scalars.
    Return the 192-byte result as a G2 point.

    Raise `ValueError` if a point is not on the curve or fails the
    subgroup check.
    """
    result: Point3D[FQ2] = Z2
    for raw_point, raw_scalar in zip(points, scalars, strict=True):
        point = bytes_to_g2(raw_point)
        if not is_inf(bls12_multiply(point, curve_order)):
            raise ValueError("Subgroup check failed for G2 point")

        m = int.from_bytes(raw_scalar, "big")
        product = bls12_multiply(point, m)
        result = bls12_add(result, product)

    return g2_to_bytes(result)


def map_fp_to_g1(fp: bytes) -> bytes:
    """
    Map a 48-byte field element to a 96-byte G1 point.
    """
    if len(fp) != 48:
        raise ValueError("field element must be 48 bytes")

    value = int.from_bytes(fp, "big")
    if value >= FQ.field_modulus:
        raise ValueError("coordinate >= field modulus")

    g1_point = clear_cofactor_G1(map_to_curve_G1(FQ(value)))

    return g1_to_bytes(g1_point)


def map_fp2_to_g2(fp2: bytes) -> bytes:
    """
    Map a 96-byte FP2 element to a 192-byte G2 point.
    """
    if len(fp2) != 96:
        raise ValueError("FP2 element must be 96 bytes")

    c0 = int.from_bytes(fp2[:48], "big")
    if c0 >= FQ.field_modulus:
        raise ValueError("coordinate >= field modulus")

    c1 = int.from_bytes(fp2[48:], "big")
    if c1 >= FQ.field_modulus:
        raise ValueError("coordinate >= field modulus")

    fq2 = FQ2((c0, c1))
    g2_point = clear_cofactor_G2(map_to_curve_G2(fq2))

    return g2_to_bytes(g2_point)


def pairing_check(
    g1_points: Sequence[bytes],
    g2_points: Sequence[bytes],
) -> bool:
    """
    Check if the pairing of the given G1 and G2 points is the identity.

    Perform on-curve and subgroup checks for each point.
    `g1_points` is a sequence of 96-byte G1 points and `g2_points` is
    a sequence of 192-byte G2 points.

    Raise `ValueError` if a point is not on the curve or fails the
    subgroup check.
    """
    result = FQ12.one()
    for raw_g1, raw_g2 in zip(g1_points, g2_points, strict=True):
        g1_point = bytes_to_g1(raw_g1)
        if not is_inf(bls12_multiply(g1_point, curve_order)):
            raise ValueError("Subgroup check failed for G1 point")

        g2_point = bytes_to_g2(raw_g2)
        if not is_inf(bls12_multiply(g2_point, curve_order)):
            raise ValueError("Subgroup check failed for G2 point")

        result *= pairing(g2_point, g1_point)

    return result == FQ12.one()
