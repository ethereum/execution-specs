from typing import (
    Optional,
    Tuple,
)

from py_ecc.fields import (
    optimized_bls12_381_FQ as FQ,
    optimized_bls12_381_FQ2 as FQ2,
)
from py_ecc.optimized_bls12_381 import (
    Z1,
    Z2,
    b,
    b2,
    field_modulus as q,
    is_inf,
    is_on_curve,
    normalize,
)

from .constants import (
    EIGHTH_ROOTS_OF_UNITY,
    FQ2_ORDER,
    POW_2_381,
    POW_2_382,
    POW_2_383,
)
from .typing import (
    G1Compressed,
    G1Uncompressed,
    G2Compressed,
    G2Uncompressed,
)


#
# The most-significant three bits of a G1 or G2 encoding should be masked away before
# the coordinate(s) are interpreted.
# These bits are used to unambiguously represent the underlying element
# The format: (c_flag, b_flag, a_flag, x)
# https://github.com/zcash/librustzcash/blob/6e0364cd42a2b3d2b958a54771ef51a8db79dd29/pairing/src/bls12_381/README.md#bls12-381-instantiation  # noqa: E501
#
def get_flags(z: int) -> Tuple[bool, bool, bool]:
    c_flag = bool((z >> 383) & 1)  # The most significant bit.
    b_flag = bool((z >> 382) & 1)  # The second-most significant bit.
    a_flag = bool((z >> 381) & 1)  # The third-most significant bit.
    return c_flag, b_flag, a_flag


def is_point_at_infinity(z1: int, z2: Optional[int] = None) -> bool:
    """
    If z2 is None, the given z1 is a G1 point.
    Else, (z1, z2) is a G2 point.
    """
    return (z1 % POW_2_381 == 0) and (z2 is None or z2 == 0)


#
# G1
#
def compress_G1(pt: G1Uncompressed) -> G1Compressed:
    """
    A compressed point is a 384-bit integer with the bit order
    (c_flag, b_flag, a_flag, x), where the c_flag bit is always set to 1,
    the b_flag bit indicates infinity when set to 1,
    the a_flag bit helps determine the y-coordinate when decompressing,
    and the 381-bit integer x is the x-coordinate of the point.
    """
    if is_inf(pt):
        # Set c_flag = 1 and b_flag = 1. leave a_flag = x = 0
        return G1Compressed(POW_2_383 + POW_2_382)
    else:
        x, y = normalize(pt)
        # Record y's leftmost bit to the a_flag
        a_flag = (y.n * 2) // q
        # Set c_flag = 1 and b_flag = 0
        return G1Compressed(x.n + a_flag * POW_2_381 + POW_2_383)


def decompress_G1(z: G1Compressed) -> G1Uncompressed:
    """
    Recovers x and y coordinates from the compressed point.
    """
    c_flag, b_flag, a_flag = get_flags(z)

    # c_flag == 1 indicates the compressed form
    # MSB should be 1
    if not c_flag:
        raise ValueError("c_flag should be 1")

    is_inf_pt = is_point_at_infinity(z)

    if b_flag != is_inf_pt:
        raise ValueError(f"b_flag should be {int(is_inf_pt)}")

    if is_inf_pt:
        # 3 MSBs should be 110
        if a_flag:
            raise ValueError("a point at infinity should have a_flag == 0")
        return Z1

    # Else, not point at infinity
    # 3 MSBs should be 100 or 101
    x = z % POW_2_381
    if x >= q:
        raise ValueError(f"Point value should be less than field modulus. Got {x}")

    # Try solving y coordinate from the equation Y^2 = X^3 + b
    # using quadratic residue
    y = pow((x**3 + b.n) % q, (q + 1) // 4, q)

    if pow(y, 2, q) != (x**3 + b.n) % q:
        raise ValueError("The given point is not on G1: y**2 = x**3 + b")
    # Choose the y whose leftmost bit is equal to the a_flag
    if (y * 2) // q != int(a_flag):
        y = q - y
    return (FQ(x), FQ(y), FQ(1))


#
# G2
#
def modular_squareroot_in_FQ2(value: FQ2) -> Optional[FQ2]:
    """
    Given value=``x``, returns the value ``y`` such that ``y**2 % q == x``,
    and None if this is not possible. In cases where there are two solutions,
    the value with higher imaginary component is favored;
    if both solutions have equal imaginary component the value with higher real
    component is favored.
    """
    candidate_squareroot = value ** ((FQ2_ORDER + 8) // 16)
    check = candidate_squareroot**2 / value
    if check in EIGHTH_ROOTS_OF_UNITY[::2]:
        x1 = (
            candidate_squareroot
            / EIGHTH_ROOTS_OF_UNITY[EIGHTH_ROOTS_OF_UNITY.index(check) // 2]
        )
        x2 = -x1
        x1_re, x1_im = x1.coeffs
        x2_re, x2_im = x2.coeffs
        return x1 if (x1_im > x2_im or (x1_im == x2_im and x1_re > x2_re)) else x2
    return None


def compress_G2(pt: G2Uncompressed) -> G2Compressed:
    """
    The compressed point (z1, z2) has the bit order:
    z1: (c_flag1, b_flag1, a_flag1, x1)
    z2: (c_flag2, b_flag2, a_flag2, x2)
    where
    - c_flag1 is always set to 1
    - b_flag1 indicates infinity when set to 1
    - a_flag1 helps determine the y-coordinate when decompressing,
    - a_flag2, b_flag2, and c_flag2 are always set to 0
    """
    if not is_on_curve(pt, b2):
        raise ValueError("The given point is not on the twisted curve over FQ**2")
    if is_inf(pt):
        return G2Compressed((POW_2_383 + POW_2_382, 0))
    x, y = normalize(pt)
    x_re, x_im = x.coeffs
    y_re, y_im = y.coeffs
    # Record the leftmost bit of y_im to the a_flag1
    # If y_im happens to be zero, then use the bit of y_re
    a_flag1 = (int(y_im) * 2) // q if y_im > 0 else (int(y_re) * 2) // q

    # Imaginary part of x goes to z1, real part goes to z2
    # c_flag1 = 1, b_flag1 = 0
    z1 = x_im + a_flag1 * POW_2_381 + POW_2_383
    # a_flag2 = b_flag2 = c_flag2 = 0
    z2 = x_re
    return G2Compressed((int(z1), int(z2)))


def decompress_G2(p: G2Compressed) -> G2Uncompressed:
    """
    Recovers x and y coordinates from the compressed point (z1, z2).
    """
    z1, z2 = p
    c_flag1, b_flag1, a_flag1 = get_flags(z1)

    # c_flag == 1 indicates the compressed form
    # MSB should be 1
    if not c_flag1:
        raise ValueError("c_flag should be 1")

    is_inf_pt = is_point_at_infinity(z1, z2)

    if b_flag1 != is_inf_pt:
        raise ValueError(f"b_flag should be {int(is_inf_pt)}")

    if is_inf_pt:
        # 3 MSBs should be 110
        if a_flag1:
            raise ValueError("a point at infinity should have a_flag == 0")
        return Z2

    # Else, not point at infinity
    # 3 MSBs should be 100 or 101
    x1 = z1 % POW_2_381
    # Ensure that x1 is less than the field modulus.
    if x1 >= q:
        raise ValueError(f"x1 value should be less than field modulus. Got {x1}")

    # Ensure that z2 is less than the field modulus.
    if z2 >= q:
        raise ValueError(f"z2 point value should be less than field modulus. Got {z2}")

    x2 = z2
    # x1 is the imaginary part, x2 is the real part
    x = FQ2([x2, x1])
    y = modular_squareroot_in_FQ2(x**3 + b2)
    if y is None:
        raise ValueError("Failed to find a modular squareroot")

    # Choose the y whose leftmost bit of the imaginary part is equal to the a_flag1
    # If y_im happens to be zero, then use the bit of y_re
    y_re, y_im = y.coeffs
    if (y_im > 0 and (int(y_im) * 2) // q != int(a_flag1)) or (
        y_im == 0 and (int(y_re) * 2) // q != int(a_flag1)
    ):
        y = FQ2((y * -1).coeffs)

    if not is_on_curve((x, y, FQ2([1, 0])), b2):
        raise ValueError("The given point is not on the twisted curve over FQ**2")
    return (x, y, FQ2([1, 0]))
