"""F"""

from . import elliptic_curve, finite_field

alt_bn128_prime = 21888242871839275222246405745257275088696311157297823662689037894645226208583  # noqa: E501
alt_bn128_curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617  # noqa: E501
trace_of_frobenius = 29793968203157093289


class BNF(finite_field.PrimeField):
    """
    The prime field over which the alt_bn128 curve is defined.
    """

    PRIME = alt_bn128_prime


class BNP(elliptic_curve.EllipticCurve):
    """
    The alt_bn128 curve.
    """

    FIELD = BNF
    A = BNF(0)
    B = BNF(3)


class BNF2(finite_field.GaloisField):
    """i^2 + 1 = 0"""

    PRIME = alt_bn128_prime
    MODULUS = (1, 0)


BNF2.i = BNF2((0, 1))
BNF2.i_plus_9 = BNF2((9, 1))


class BNP2(elliptic_curve.EllipticCurve):
    """F"""

    FIELD = BNF2
    A = BNF2.zero()
    B = BNF2.from_int(3) / (BNF2.i + BNF2.from_int(9))


class BNF12(finite_field.GaloisField):
    """F"""

    PRIME = alt_bn128_prime
    MODULUS = (82, 0, 0, 0, 0, 0, -18, 0, 0, 0, 0, 0)


BNF12.w = BNF12((0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
BNF12.i_plus_9 = BNF12.w ** 6


class BNP12(elliptic_curve.EllipticCurve):
    """F"""

    FIELD = BNF12
    A = BNF12.zero()
    B = BNF12.from_int(3)


def bnf2_to_bnf12(x: BNF2) -> BNF12:
    """F"""
    return BNF12.from_int(x[0]) + BNF12.from_int(x[1]) * (
        BNF12.i_plus_9 - BNF12.from_int(9)
    )


def bnp_to_bnp12(p: BNP) -> BNP12:
    return BNP12(BNF12.from_int(int(p.x)), BNF12.from_int(int(p.y)))


def twist(p: BNP2) -> BNP12:
    """F"""
    return BNP12(
        bnf2_to_bnf12(p.x) * (BNF12.w ** 2),
        bnf2_to_bnf12(p.y) * (BNF12.w ** 3),
    )


def linefunc(p1: BNP12, p2: BNP12, t: BNP12) -> BNF12:
    """F"""
    if p1.x != p2.x:
        lam = (p2.y - p1.y) / (p2.x - p1.x)
        return lam * (t.x - p1.x) - (t.y - p1.y)
    elif p1.y == p2.y:
        lam = BNF12.from_int(3) * p1.x ** 2 / (BNF12.from_int(2) * p1.y)
        return lam * (t.x - p1.x) - (t.y - p1.y)
    else:
        return t.x - p1.x


def miller_loop(q: BNP12, p: BNP12) -> BNF12:
    if p == BNP12.inf() or q == BNP12.inf():
        return BNF12.from_int(1)
    r = q
    f = BNF12.from_int(1)
    for i in range(63, -1, -1):
        f = f * f * linefunc(r, r, p)
        r = r.double()
        if (trace_of_frobenius - 1) & (2 ** i):
            f = f * linefunc(r, q, p)
            r = r + q
    assert r == q.mul_by(trace_of_frobenius - 1)

    q1 = BNP12(q.x ** alt_bn128_prime, q.y ** alt_bn128_prime)
    nq2 = BNP12(q1.x ** alt_bn128_prime, -q1.y ** alt_bn128_prime)

    f = f * linefunc(r, q1, p)
    r = r + q1
    f = f * linefunc(r, nq2, p)

    return f ** ((alt_bn128_prime ** 12 - 1) // alt_bn128_curve_order)


def pairing(q: BNP2, p: BNP) -> BNF12:
    return miller_loop(twist(q), bnp_to_bnp12(p))
