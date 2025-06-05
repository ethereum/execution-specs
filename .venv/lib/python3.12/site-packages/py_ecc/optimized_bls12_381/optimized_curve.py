from py_ecc.fields import (
    optimized_bls12_381_FQ as FQ,
    optimized_bls12_381_FQ2 as FQ2,
    optimized_bls12_381_FQ12 as FQ12,
    optimized_bls12_381_FQP as FQP,
)
from py_ecc.fields.field_properties import (
    field_properties,
)
from py_ecc.typing import (
    Optimized_Field,
    Optimized_Point2D,
    Optimized_Point3D,
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
    ),
    FQ(
        1339506544944476473020471379941921221584933875938349620426543736416511423956333506472724655353366534992391756441569  # noqa: E501
    ),
    FQ(1),
)
# Generator for twisted curve over FQ2
G2 = (
    FQ2(
        (
            352701069587466618187139116011060144890029952792775240219908644239793785735715026873347600343865175952761926303160,  # noqa: E501
            3059144344244213709971259814753781636986470325476647558659373206291635324768958432433509563104347017837885763365758,  # noqa: E501
        )
    ),
    FQ2(
        (
            1985150602287291935568054521177171638300868978215655730859378665066344726373823718423869104263333984641494340347905,  # noqa: E501
            927553665492332455747201965776037880757740193453592970025027978793976877002675564980949289727957565575433344219582,  # noqa: E501
        )
    ),
    FQ2.one(),
)
# Point at infinity over FQ
Z1 = (FQ.one(), FQ.one(), FQ.zero())
# Point at infinity for twisted curve over FQ2
Z2 = (FQ2.one(), FQ2.one(), FQ2.zero())


# Check if a point is the point at infinity
def is_inf(pt: Optimized_Point3D[Optimized_Field]) -> bool:
    return pt[-1] == pt[-1].__class__.zero()


# Check that a point is on the curve defined by y**2 == x**3 + b
def is_on_curve(pt: Optimized_Point3D[Optimized_Field], b: Optimized_Field) -> bool:
    if is_inf(pt):
        return True
    x, y, z = pt
    return y**2 * z - x**3 == b * z**3


if not is_on_curve(G1, b):
    raise ValueError("Generator is not on curve")
if not is_on_curve(G2, b2):
    raise ValueError("Generator is not on twisted curve")


# Elliptic curve doubling
def double(
    pt: Optimized_Point3D[Optimized_Field],
) -> Optimized_Point3D[Optimized_Field]:
    x, y, z = pt
    W = 3 * x * x
    S = y * z
    B = x * y * S
    H = W * W - 8 * B
    S_squared = S * S
    newx = 2 * H * S
    newy = W * (4 * B - H) - 8 * y * y * S_squared
    newz = 8 * S * S_squared
    return (newx, newy, newz)


# Elliptic curve addition
def add(
    p1: Optimized_Point3D[Optimized_Field], p2: Optimized_Point3D[Optimized_Field]
) -> Optimized_Point3D[Optimized_Field]:
    one, zero = p1[0].one(), p1[0].zero()
    if p1[2] == zero or p2[2] == zero:
        return p1 if p2[2] == zero else p2
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    U1 = y2 * z1
    U2 = y1 * z2
    V1 = x2 * z1
    V2 = x1 * z2
    if V1 == V2 and U1 == U2:
        return double(p1)
    elif V1 == V2:
        return (one, one, zero)
    U = U1 - U2
    V = V1 - V2
    V_squared = V * V
    V_squared_times_V2 = V_squared * V2
    V_cubed = V * V_squared
    W = z1 * z2
    A = U * U * W - V_cubed - 2 * V_squared_times_V2
    newx = V * A
    newy = U * (V_squared_times_V2 - A) - V_cubed * U2
    newz = V_cubed * W
    return (newx, newy, newz)


# Elliptic curve point multiplication
def multiply(
    pt: Optimized_Point3D[Optimized_Field], n: int
) -> Optimized_Point3D[Optimized_Field]:
    if n == 0:
        return (pt[0].one(), pt[0].one(), pt[0].zero())
    elif n == 1:
        return pt
    elif not n % 2:
        return multiply(double(pt), n // 2)
    else:
        return add(multiply(double(pt), int(n // 2)), pt)


def eq(
    p1: Optimized_Point3D[Optimized_Field], p2: Optimized_Point3D[Optimized_Field]
) -> bool:
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    return x1 * z2 == x2 * z1 and y1 * z2 == y2 * z1


def normalize(
    pt: Optimized_Point3D[Optimized_Field],
) -> Optimized_Point2D[Optimized_Field]:
    x, y, z = pt
    return (x / z, y / z)


# "Twist" a point in E(FQ2) into a point in E(FQ12)
w = FQ12([0, 1] + [0] * 10)


# Convert P => -P
def neg(pt: Optimized_Point3D[Optimized_Field]) -> Optimized_Point3D[Optimized_Field]:
    x, y, z = pt
    return (x, -y, z)


def twist(pt: Optimized_Point3D[FQP]) -> Optimized_Point3D[FQ12]:
    _x, _y, _z = pt
    # Field isomorphism from Z[p] / x**2 to Z[p] / x**2 - 2*x + 2
    xcoeffs = [_x.coeffs[0] - _x.coeffs[1], _x.coeffs[1]]
    ycoeffs = [_y.coeffs[0] - _y.coeffs[1], _y.coeffs[1]]
    zcoeffs = [_z.coeffs[0] - _z.coeffs[1], _z.coeffs[1]]
    nx = FQ12([0] + [xcoeffs[0]] + [0] * 5 + [xcoeffs[1]] + [0] * 4)
    ny = FQ12([ycoeffs[0]] + [0] * 5 + [ycoeffs[1]] + [0] * 5)
    nz = FQ12([0] * 3 + [zcoeffs[0]] + [0] * 5 + [zcoeffs[1]] + [0] * 2)
    return (nx, ny, nz)


# Check that the twist creates a point that is on the curve
G12 = twist(G2)
if not is_on_curve(G12, b12):
    raise ValueError("Twist creates a point not on curve")
