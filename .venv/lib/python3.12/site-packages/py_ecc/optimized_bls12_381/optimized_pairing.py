from py_ecc.fields import (
    optimized_bls12_381_FQ as FQ,
    optimized_bls12_381_FQ2 as FQ2,
    optimized_bls12_381_FQ12 as FQ12,
)
from py_ecc.fields.field_properties import (
    field_properties,
)
from py_ecc.typing import (
    Optimized_Field,
    Optimized_Point2D,
    Optimized_Point3D,
)

from .optimized_curve import (
    G1,
    add,
    b,
    b2,
    curve_order,
    double,
    is_on_curve,
    multiply,
    normalize,
    twist,
)

field_modulus = field_properties["bls12_381"]["field_modulus"]

ate_loop_count = 15132376222941642752
log_ate_loop_count = 62
pseudo_binary_encoding = [
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    1,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    1,
    0,
    0,
    1,
    0,
    1,
    1,
]


if not (
    sum([e * 2**i for i, e in enumerate(pseudo_binary_encoding)]) == ate_loop_count
):
    raise ValueError("Pseudo binary encoding is incorrect")


def normalize1(
    p: Optimized_Point3D[Optimized_Field],
) -> Optimized_Point3D[Optimized_Field]:
    x, y = normalize(p)

    return x, y, x.one()


# Create a function representing the line between P1 and P2,
# and evaluate it at T. Returns a numerator and a denominator
# to avoid unneeded divisions
def linefunc(
    P1: Optimized_Point3D[Optimized_Field],
    P2: Optimized_Point3D[Optimized_Field],
    T: Optimized_Point3D[Optimized_Field],
) -> Optimized_Point2D[Optimized_Field]:
    zero = P1[0].zero()
    x1, y1, z1 = P1
    x2, y2, z2 = P2
    xt, yt, zt = T
    # points in projective coords: (x / z, y / z)
    # hence, m = (y2/z2 - y1/z1) / (x2/z2 - x1/z1)
    # multiply numerator and denominator by z1z2 to get values below
    m_numerator = y2 * z1 - y1 * z2
    m_denominator = x2 * z1 - x1 * z2
    if m_denominator != zero:
        # m * ((xt/zt) - (x1/z1)) - ((yt/zt) - (y1/z1))
        return (
            m_numerator * (xt * z1 - x1 * zt) - m_denominator * (yt * z1 - y1 * zt),
            m_denominator * zt * z1,
        )
    elif m_numerator == zero:
        # m = 3(x/z)^2 / 2(y/z), multiply num and den by z**2
        m_numerator = 3 * x1 * x1
        m_denominator = 2 * y1 * z1
        return (
            m_numerator * (xt * z1 - x1 * zt) - m_denominator * (yt * z1 - y1 * zt),
            m_denominator * zt * z1,
        )
    else:
        return xt * z1 - x1 * zt, z1 * zt


def cast_point_to_fq12(pt: Optimized_Point3D[FQ]) -> Optimized_Point3D[FQ12]:
    if pt is None:
        return None
    x, y, z = pt
    return (FQ12([x.n] + [0] * 11), FQ12([y.n] + [0] * 11), FQ12([z.n] + [0] * 11))


# Check consistency of the "line function"
one, two, three = G1, double(G1), multiply(G1, 3)
negone, negtwo, negthree = (
    multiply(G1, curve_order - 1),
    multiply(G1, curve_order - 2),
    multiply(G1, curve_order - 3),
)


conditions = [
    linefunc(one, two, one)[0] == FQ(0),
    linefunc(one, two, two)[0] == FQ(0),
    linefunc(one, two, three)[0] != FQ(0),
    linefunc(one, two, negthree)[0] == FQ(0),
    linefunc(one, negone, one)[0] == FQ(0),
    linefunc(one, negone, negone)[0] == FQ(0),
    linefunc(one, negone, two)[0] != FQ(0),
    linefunc(one, one, one)[0] == FQ(0),
    linefunc(one, one, two)[0] != FQ(0),
    linefunc(one, one, negtwo)[0] == FQ(0),
]

if not all(conditions):
    raise ValueError("Line function is inconsistent")


# Main miller loop
def miller_loop(
    Q: Optimized_Point3D[FQ2], P: Optimized_Point3D[FQ], final_exponentiate: bool = True
) -> FQ12:
    if Q is None or P is None:
        return FQ12.one()
    cast_P = cast_point_to_fq12(P)
    twist_R = twist_Q = twist(Q)
    R: Optimized_Point3D[FQ2] = Q
    f_num, f_den = FQ12.one(), FQ12.one()
    # for i in range(log_ate_loop_count, -1, -1):
    for v in pseudo_binary_encoding[62::-1]:
        _n, _d = linefunc(twist_R, twist_R, cast_P)
        f_num = f_num * f_num * _n
        f_den = f_den * f_den * _d
        R = double(R)
        twist_R = twist(R)
        if v == 1:
            _n, _d = linefunc(twist_R, twist_Q, cast_P)
            f_num = f_num * _n
            f_den = f_den * _d
            R = add(R, Q)
            twist_R = twist(R)
    # assert R == multiply(Q, ate_loop_count)
    # Q1 = (Q[0] ** field_modulus, Q[1] ** field_modulus, Q[2] ** field_modulus)
    # assert is_on_curve(Q1, b12)
    # nQ2 = (Q1[0] ** field_modulus, -Q1[1] ** field_modulus, Q1[2] ** field_modulus)
    # assert is_on_curve(nQ2, b12)
    # _n1, _d1 = linefunc(R, Q1, P)
    # R = add(R, Q1)
    # _n2, _d2 = linefunc(R, nQ2, P)
    # f = f_num * _n1 * _n2 / (f_den * _d1 * _d2)
    f = f_num / f_den
    # R = add(R, nQ2) This line is in many specifications but technically does nothing
    if final_exponentiate:
        return f ** ((field_modulus**12 - 1) // curve_order)
    else:
        return f


# Pairing computation
def pairing(
    Q: Optimized_Point3D[FQ2], P: Optimized_Point3D[FQ], final_exponentiate: bool = True
) -> FQ12:
    if not is_on_curve(Q, b2):
        raise ValueError("Invalid input - point Q is not on the correct curve")
    if not is_on_curve(P, b):
        raise ValueError("Invalid input - point P is not on the correct curves")
    if P[-1] == (P[-1].zero()) or Q[-1] == (Q[-1].zero()):
        return FQ12.one()
    return miller_loop(Q, P, final_exponentiate=final_exponentiate)


exptable = [FQ12([0] * i + [1] + [0] * (11 - i)) ** field_modulus for i in range(12)]


def exp_by_p(x: FQ12) -> FQ12:
    return sum(
        (table_entry * int(coeff) for table_entry, coeff in zip(exptable, x.coeffs)),
        FQ12.zero(),
    )


def final_exponentiate(p: FQ12) -> FQ12:
    cofactor = (field_modulus**4 - field_modulus**2 + 1) // curve_order
    p2 = exp_by_p(exp_by_p(p)) * p
    p3 = exp_by_p(exp_by_p(exp_by_p(exp_by_p(exp_by_p(exp_by_p(p2)))))) / p2
    return p3**cofactor
