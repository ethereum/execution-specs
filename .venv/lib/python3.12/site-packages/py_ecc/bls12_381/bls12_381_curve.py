from py_ecc.fields import (
    bls12_381_FQ as FQ,
    bls12_381_FQ2 as FQ2,
    bls12_381_FQ12 as FQ12,
    bls12_381_FQP as FQP,
)
from py_ecc.fields.field_properties import (
    field_properties,
)
from py_ecc.typing import (
    Field,
    GeneralPoint,
    Point2D,
)

field_modulus = field_properties["bls12_381"]["field_modulus"]
curve_order = (
    52435875175126190479447740508185965837690552500527637822603658699938581184513
)

# Curve order should be prime
if not pow(2, curve_order, curve_order) == 2:
    raise ValueError("Curve order is not prime")
# Curve order should be a factor of field_modulus**12 - 1
if not (field_modulus**12 - 1) % curve_order == 0:
    raise ValueError("Curve order is not a factor of field_modulus**12 - 1")

# Curve is y**2 = x**3 + 4
b = FQ(4)
# Twisted curve over FQ**2
b2 = FQ2((4, 4))
# Extension curve over FQ**12; same b value as over FQ
b12 = FQ12((4,) + (0,) * 11)

# Generator for curve over FQ
G1 = (
    FQ(
        3685416753713387016781088315183077757961620795782546409894578378688607592378376318836054947676345821548104185464507  # noqa: E501
    ),  # noqa: E501
    FQ(
        1339506544944476473020471379941921221584933875938349620426543736416511423956333506472724655353366534992391756441569  # noqa: E501
    ),  # noqa: E501
)
# Generator for twisted curve over FQ2
G2 = (
    FQ2(
        [
            352701069587466618187139116011060144890029952792775240219908644239793785735715026873347600343865175952761926303160,  # noqa: E501
            3059144344244213709971259814753781636986470325476647558659373206291635324768958432433509563104347017837885763365758,  # noqa: E501
        ]
    ),
    FQ2(
        [
            1985150602287291935568054521177171638300868978215655730859378665066344726373823718423869104263333984641494340347905,  # noqa: E501
            927553665492332455747201965776037880757740193453592970025027978793976877002675564980949289727957565575433344219582,  # noqa: E501
        ]
    ),
)
# Point at infinity over FQ
Z1 = None
# Point at infinity for twisted curve over FQ2
Z2 = None


# Check if a point is the point at infinity
def is_inf(pt: GeneralPoint[Field]) -> bool:
    return pt is None


# Check that a point is on the curve defined by y**2 == x**3 + b
def is_on_curve(pt: Point2D[Field], b: Field) -> bool:
    if is_inf(pt) or pt is None:
        return True
    x, y = pt
    return y**2 - x**3 == b


if not is_on_curve(G1, b):
    raise ValueError("Generator is not on curve")
if not is_on_curve(G2, b2):
    raise ValueError("Generator is not on twisted curve")


# Elliptic curve doubling
def double(pt: Point2D[Field]) -> Point2D[Field]:
    if is_inf(pt) or pt is None:
        return pt
    x, y = pt
    m = 3 * x**2 / (2 * y)
    newx = m**2 - 2 * x
    newy = -m * newx + m * x - y
    return (newx, newy)


# Elliptic curve addition
def add(p1: Point2D[Field], p2: Point2D[Field]) -> Point2D[Field]:
    if p1 is None or p2 is None:
        return p1 if p2 is None else p2
    x1, y1 = p1
    x2, y2 = p2
    if x2 == x1 and y2 == y1:
        return double(p1)
    elif x2 == x1:
        return None
    else:
        m = (y2 - y1) / (x2 - x1)
    newx = m**2 - x1 - x2
    newy = -m * newx + m * x1 - y1
    if not newy == (-m * newx + m * x2 - y2):
        raise ValueError("Point addition is incorrect")
    return (newx, newy)


# Elliptic curve point multiplication
def multiply(pt: Point2D[Field], n: int) -> Point2D[Field]:
    if n == 0:
        return None
    elif n == 1:
        return pt
    elif not n % 2:
        return multiply(double(pt), n // 2)
    else:
        return add(multiply(double(pt), int(n // 2)), pt)


def eq(p1: GeneralPoint[Field], p2: GeneralPoint[Field]) -> bool:
    return p1 == p2


# "Twist" a point in E(FQ2) into a point in E(FQ12)
w = FQ12([0, 1] + [0] * 10)


# Convert P => -P
def neg(pt: Point2D[Field]) -> Point2D[Field]:
    if pt is None:
        return None
    x, y = pt
    return (x, -y)


def twist(pt: Point2D[FQP]) -> Point2D[FQ12]:
    if pt is None:
        return None
    _x, _y = pt
    # Field isomorphism from Z[p] / x**2 to Z[p] / x**2 - 2*x + 2
    xcoeffs = [_x.coeffs[0] - _x.coeffs[1], _x.coeffs[1]]
    ycoeffs = [_y.coeffs[0] - _y.coeffs[1], _y.coeffs[1]]
    # Isomorphism into subfield of Z[p] / w**12 - 2 * w**6 + 2,
    # where w**6 = x
    nx = FQ12([xcoeffs[0]] + [0] * 5 + [xcoeffs[1]] + [0] * 5)
    ny = FQ12([ycoeffs[0]] + [0] * 5 + [ycoeffs[1]] + [0] * 5)
    # Divide x coord by w**2 and y coord by w**3
    return (nx / w**2, ny / w**3)


G12 = twist(G2)
# Check that the twist creates a point that is on the curve
if not is_on_curve(G12, b12):
    raise ValueError("Twist creates a point not on curve")
