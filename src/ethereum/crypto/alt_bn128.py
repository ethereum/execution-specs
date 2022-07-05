"""
The alt_bn128 curve
^^^^^^^^^^^^^^^^^^^
"""

from . import elliptic_curve, finite_field

ALT_BN128_PRIME = 21888242871839275222246405745257275088696311157297823662689037894645226208583  # noqa: E501
ALT_BN128_CURVE_ORDER = 21888242871839275222246405745257275088548364400416034343698204186575808495617  # noqa: E501
ATE_PAIRING_COUNT = 29793968203157093289
ATE_PAIRING_COUNT_BITS = 63


class BNF(finite_field.PrimeField):
    """
    The prime field over which the alt_bn128 curve is defined.
    """

    PRIME = ALT_BN128_PRIME


class BNP(elliptic_curve.EllipticCurve):
    """
    The alt_bn128 curve.
    """

    FIELD = BNF
    A = BNF(0)
    B = BNF(3)


class BNF2(finite_field.GaloisField):
    """
    `BNF` extended with a square root of 1 (`i`).
    """

    PRIME = ALT_BN128_PRIME
    MODULUS = (1, 0)

    i: "BNF2"
    i_plus_9: "BNF2"


BNF2.FROBENIUS_COEFFICIENTS = BNF2.calculate_frobenius_coefficients()
"""autoapi_noindex"""

BNF2.i = BNF2((0, 1))
"""autoapi_noindex"""

BNF2.i_plus_9 = BNF2((9, 1))
"""autoapi_noindex"""


class BNP2(elliptic_curve.EllipticCurve):
    """
    A twist of `BNP`. This is actually the same curve as `BNP` under a change
    of variable, but that change of variable is only possible over the larger
    field `BNP12`.
    """

    FIELD = BNF2
    A = BNF2.zero()
    B = BNF2.from_int(3) / (BNF2.i + BNF2.from_int(9))


class BNF12(finite_field.GaloisField):
    """
    `BNF2` extended by adding a 6th root of `9 + i` called `w` (omega).
    """

    PRIME = ALT_BN128_PRIME
    MODULUS = (82, 0, 0, 0, 0, 0, -18, 0, 0, 0, 0, 0)

    w: "BNF12"
    i_plus_9: "BNF12"

    def __mul__(self: "BNF12", right: "BNF12") -> "BNF12":  # type: ignore[override] # noqa: E501
        """
        Multiplication special cased for BNF12.
        """
        mul = [0] * 23

        for i in range(12):
            for j in range(12):
                mul[i + j] += self[i] * right[j]

        for i in range(22, 11, -1):
            mul[i - 6] -= mul[i] * (-18)
            mul[i - 12] -= mul[i] * 82

        return BNF12.__new__(
            BNF12,
            mul[:12],
        )


BNF12.FROBENIUS_COEFFICIENTS = BNF12.calculate_frobenius_coefficients()
"""autoapi_noindex"""

BNF12.w = BNF12((0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
"""autoapi_noindex"""

BNF12.i_plus_9 = BNF12.w**6
"""autoapi_noindex"""


class BNP12(elliptic_curve.EllipticCurve):
    """
    The same curve as `BNP`, but defined over the larger field. This curve has
    both subgroups of order `ALT_BN128_CURVE_ORDER` and allows pairings to be
    computed.
    """

    FIELD = BNF12
    A = BNF12.zero()
    B = BNF12.from_int(3)


def bnf2_to_bnf12(x: BNF2) -> BNF12:
    """
    Lift a field element in `BNF2` to `BNF12`.
    """
    return BNF12.from_int(x[0]) + BNF12.from_int(x[1]) * (
        BNF12.i_plus_9 - BNF12.from_int(9)
    )


def bnp_to_bnp12(p: BNP) -> BNP12:
    """
    Lift a point from `BNP` to `BNP12`.
    """
    return BNP12(BNF12.from_int(int(p.x)), BNF12.from_int(int(p.y)))


def twist(p: BNP2) -> BNP12:
    """
    Apply to twist to change variables from the curve `BNP2` to `BNP12`.
    """
    return BNP12(
        bnf2_to_bnf12(p.x) * (BNF12.w**2),
        bnf2_to_bnf12(p.y) * (BNF12.w**3),
    )


def linefunc(p1: BNP12, p2: BNP12, t: BNP12) -> BNF12:
    """
    Evaluate the function defining the line between points `p1` and `p2` at the
    point `t`. The mathematical significance of this function is that is has
    divisor `(p1) + (p2) + (p1 + p2) - 3(O)`.

    Note: Abstract mathematical presentations of Miller's algorithm often
    specify the divisor `(p1) + (p2) - (p1 + p2) - (O)`. This turns out not to
    matter.
    """
    if p1.x != p2.x:
        lam = (p2.y - p1.y) / (p2.x - p1.x)
        return lam * (t.x - p1.x) - (t.y - p1.y)
    elif p1.y == p2.y:
        lam = BNF12.from_int(3) * p1.x**2 / (BNF12.from_int(2) * p1.y)
        return lam * (t.x - p1.x) - (t.y - p1.y)
    else:
        return t.x - p1.x


def miller_loop(q: BNP12, p: BNP12) -> BNF12:
    """
    The core of the pairing algorithm.
    """
    if p == BNP12.point_at_infinity() or q == BNP12.point_at_infinity():
        return BNF12.from_int(1)
    r = q
    f = BNF12.from_int(1)
    for i in range(ATE_PAIRING_COUNT_BITS, -1, -1):
        f = f * f * linefunc(r, r, p)
        r = r.double()
        if (ATE_PAIRING_COUNT - 1) & (2**i):
            f = f * linefunc(r, q, p)
            r = r + q
    assert r == q.mul_by(ATE_PAIRING_COUNT - 1)

    q1 = BNP12(q.x.frobenius(), q.y.frobenius())
    nq2 = BNP12(q1.x.frobenius(), -q1.y.frobenius())

    f = f * linefunc(r, q1, p)
    r = r + q1
    f = f * linefunc(r, nq2, p)

    return f ** ((ALT_BN128_PRIME**12 - 1) // ALT_BN128_CURVE_ORDER)


def pairing(q: BNP2, p: BNP) -> BNF12:
    """
    Compute the pairing of `q` and `p`.
    """
    return miller_loop(twist(q), bnp_to_bnp12(p))
