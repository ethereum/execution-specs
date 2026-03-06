"""
# BLS12-381 Curve Operations

Byte-level interface to BLS12-381 curve operations. All inputs and
outputs are raw (unpadded) bytes.
"""

from typing import Sequence

from ethereum_types.bytes import Bytes96
from py_arkworks_bls12381 import GT, G1Point, G2Point, Scalar


def g1_add(a: Bytes96, b: Bytes96) -> Bytes96:
    """
    Add two G1 points.

    `a` and `b` are 96-byte G1 points.
    Return the 96-byte sum as a G1 point.
    """
    p1 = G1Point.from_xy_bytes_unchecked_be(a)
    p2 = G1Point.from_xy_bytes_unchecked_be(b)
    return (p1 + p2).to_xy_bytes_be()


def g2_add(a: bytes, b: bytes) -> bytes:
    """
    Add two G2 points.

    `a` and `b` are 192-byte G2 points.
    Return the 192-byte sum as a G2 point.
    """
    p1 = G2Point.from_xy_bytes_unchecked_be(a)
    p2 = G2Point.from_xy_bytes_unchecked_be(b)
    return (p1 + p2).to_xy_bytes_be()


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
    g1s = []
    for p in points:
        point = G1Point.from_xy_bytes_unchecked_be(p)
        if not point.is_in_subgroup():
            raise ValueError("Subgroup check failed for G1 point.")
        g1s.append(point)
    scalar_values = [Scalar.from_be_bytes_mod_order(s) for s in scalars]
    return G1Point.multiexp_unchecked(g1s, scalar_values).to_xy_bytes_be()


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
    g2s = []
    for p in points:
        point = G2Point.from_xy_bytes_unchecked_be(p)
        if not point.is_in_subgroup():
            raise ValueError("Subgroup check failed for G2 point.")
        g2s.append(point)
    scalar_values = [Scalar.from_be_bytes_mod_order(s) for s in scalars]
    return G2Point.multiexp_unchecked(g2s, scalar_values).to_xy_bytes_be()


def map_fp_to_g1(fp: bytes) -> bytes:
    """
    Map a 48-byte field element to a 96-byte G1 point.
    """
    return G1Point.map_from_fp_be(fp).to_xy_bytes_be()


def map_fp2_to_g2(fp2: bytes) -> bytes:
    """
    Map a 96-byte FP2 element to a 192-byte G2 point.
    """
    return G2Point.map_from_fp2_be(fp2).to_xy_bytes_be()


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
    g1s = []
    for p in g1_points:
        g1_point = G1Point.from_xy_bytes_unchecked_be(p)
        if not g1_point.is_in_subgroup():
            raise ValueError("Subgroup check failed for G1 point.")
        g1s.append(g1_point)

    g2s = []
    for p in g2_points:
        g2_point = G2Point.from_xy_bytes_unchecked_be(p)
        if not g2_point.is_in_subgroup():
            raise ValueError("Subgroup check failed for G2 point.")
        g2s.append(g2_point)

    return GT.pairing_check(g1s, g2s)
