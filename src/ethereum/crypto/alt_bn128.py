"""F"""

from . import elliptic_curve, finite_field

alt_bn128_prime = 21888242871839275222246405745257275088696311157297823662689037894645226208583  # noqa: E501


class BNF(finite_field.PrimeField):
    """
    The prime field over which the alt_bn128 curve is defined.
    """

    PRIME = alt_bn128_prime


BNF.ZERO = BNF(0)


class BNP(elliptic_curve.EllipticCurve):
    """
    The alt_bn128 curve.
    """

    FIELD = BNF
    A = BNF(0)
    B = BNF(3)
