import hashlib
import hmac
from typing import (
    TYPE_CHECKING,
    Any,
    Tuple,
    cast,
)

if TYPE_CHECKING:
    from py_ecc.typing import (
        PlainPoint2D,
        PlainPoint3D,
    )


def safe_ord(value: Any) -> int:
    if isinstance(value, int):
        return value
    else:
        return ord(value)


# Elliptic curve parameters (secp256k1)
P = 2**256 - 2**32 - 977
N = 115792089237316195423570985008687907852837564279074904382605163141518161494337
A = 0
B = 7
Gx = 55066263022277343669578718895168534326250603453777594175500187360389116729240
Gy = 32670510020758816978083085130507043184471273380659243275938904335757337482424
G = cast("PlainPoint2D", (Gx, Gy))


def bytes_to_int(x: bytes) -> int:
    o = 0
    for b in x:
        o = (o << 8) + safe_ord(b)
    return o


# Extended Euclidean Algorithm
def inv(a: int, n: int) -> int:
    if a == 0:
        return 0
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high // low
        nm, new = hm - lm * r, high - low * r
        lm, low, hm, high = nm, new, lm, low
    return lm % n


def to_jacobian(p: "PlainPoint2D") -> "PlainPoint3D":
    """
    Convert a 2D point to its corresponding Jacobian point representation.

    :param p: the point to convert
    :type p: PlainPoint2D

    :return: the Jacobian point representation
    :rtype: PlainPoint3D
    """
    o = (p[0], p[1], 1)
    return cast("PlainPoint3D", o)


def jacobian_double(p: "PlainPoint3D") -> "PlainPoint3D":
    """
    Double a point in Jacobian coordinates and return the result.

    :param p: the point to double
    :type p: PlainPoint3D

    :return: the resulting Jacobian point
    :rtype: PlainPoint3D
    """
    if not p[1]:
        return cast("PlainPoint3D", (0, 0, 0))
    ysq = (p[1] ** 2) % P
    S = (4 * p[0] * ysq) % P
    M = (3 * p[0] ** 2 + A * p[2] ** 4) % P
    nx = (M**2 - 2 * S) % P
    ny = (M * (S - nx) - 8 * ysq**2) % P
    nz = (2 * p[1] * p[2]) % P
    return cast("PlainPoint3D", (nx, ny, nz))


def jacobian_add(p: "PlainPoint3D", q: "PlainPoint3D") -> "PlainPoint3D":
    """
    Add two points in Jacobian coordinates and return the result.

    :param p: the first point to add
    :type p: PlainPoint3D
    :param q: the second point to add
    :type q: PlainPoint3D

    :return: the resulting Jacobian point
    :rtype: PlainPoint3D
    """
    if not p[1]:
        return q
    if not q[1]:
        return p
    U1 = (p[0] * q[2] ** 2) % P
    U2 = (q[0] * p[2] ** 2) % P
    S1 = (p[1] * q[2] ** 3) % P
    S2 = (q[1] * p[2] ** 3) % P
    if U1 == U2:
        if S1 != S2:
            return cast("PlainPoint3D", (0, 0, 1))
        return jacobian_double(p)
    H = U2 - U1
    R = S2 - S1
    H2 = (H * H) % P
    H3 = (H * H2) % P
    U1H2 = (U1 * H2) % P
    nx = (R**2 - H3 - 2 * U1H2) % P
    ny = (R * (U1H2 - nx) - S1 * H3) % P
    nz = (H * p[2] * q[2]) % P
    return cast("PlainPoint3D", (nx, ny, nz))


def from_jacobian(p: "PlainPoint3D") -> "PlainPoint2D":
    """
    Convert a Jacobian point back to its corresponding 2D point representation.

    :param p: the point to convert
    :type p: PlainPoint3D

    :return: the 2D point representation
    :rtype: PlainPoint2D
    """
    z = inv(p[2], P)
    return cast("PlainPoint2D", ((p[0] * z**2) % P, (p[1] * z**3) % P))


def jacobian_multiply(a: "PlainPoint3D", n: int) -> "PlainPoint3D":
    """
    Multiply a point in Jacobian coordinates by an integer and return the result.

    :param a: the point to multiply
    :type a: PlainPoint3D
    :param n: the integer to multiply the point by
    :type n: int

    :return: the resulting Jacobian point
    :rtype: PlainPoint3D
    """
    if a[1] == 0 or n == 0:
        return cast("PlainPoint3D", (0, 0, 1))
    if n == 1:
        return a
    if n < 0 or n >= N:
        return jacobian_multiply(a, n % N)
    if (n % 2) == 0:
        return jacobian_double(jacobian_multiply(a, n // 2))
    if (n % 2) == 1:
        return jacobian_add(jacobian_double(jacobian_multiply(a, n // 2)), a)
    raise ValueError("Unexpected case in jacobian_multiply: This should never happen.")


def multiply(a: "PlainPoint2D", n: int) -> "PlainPoint2D":
    """
    Multiply a 2D point a by an integer n using elliptic curve point multiplication,
    and return the resulting 2D point in plain coordinates.

    :param a: a 2D point on the elliptic curve
    :type a: PlainPoint2D
    :param n: an integer used for point multiplication
    :type n: int

    :return: the resulting 2D point in plain coordinates
    :rtype: PlainPoint2D
    """
    return from_jacobian(jacobian_multiply(to_jacobian(a), n))


def add(a: "PlainPoint2D", b: "PlainPoint2D") -> "PlainPoint2D":
    """
    Add two 2D points a and b using elliptic curve point addition, and return the
    resulting 2D point in plain coordinates.

    :param a: a 2D point on the elliptic curve
    :type a: PlainPoint2D
    :param b: another 2D point on the elliptic curve
    :type b: PlainPoint2D

    :return: the resulting 2D point in plain coordinates
    :rtype: PlainPoint2D
    """
    return from_jacobian(jacobian_add(to_jacobian(a), to_jacobian(b)))


# bytes32
def privtopub(privkey: bytes) -> "PlainPoint2D":
    return multiply(G, bytes_to_int(privkey))


def deterministic_generate_k(msghash: bytes, priv: bytes) -> int:
    """
    Generate a deterministic value `k` for use in ECDSA signature generation,
    as described in RFC 6979. The generated `k` value is intended to provide
    protection against weak random number generation.
    https://datatracker.ietf.org/doc/html/rfc6979

    :param msghash: The hash of the message to be signed.
    :type msghash: bytes
    :param priv: The private key to be used in the signature.
    :type priv: bytes

    :return: A deterministic value k (as an int) that can be used as the ephemeral
        private key in the signature generation process.
    :rtype: int
    """
    v = b"\x01" * 32
    k = b"\x00" * 32
    k = hmac.new(k, v + b"\x00" + priv + msghash, hashlib.sha256).digest()
    v = hmac.new(k, v, hashlib.sha256).digest()
    k = hmac.new(k, v + b"\x01" + priv + msghash, hashlib.sha256).digest()
    v = hmac.new(k, v, hashlib.sha256).digest()
    return bytes_to_int(hmac.new(k, v, hashlib.sha256).digest())


# bytes32, bytes32 -> v, r, s (as numbers)
def ecdsa_raw_sign(msghash: bytes, priv: bytes) -> Tuple[int, int, int]:
    """
    Return a raw ECDSA signature of the provided `data`, using the provided
    `private_key`.

    :param msghash: the data to sign
    :type msghash: bytes
    :param priv: the private key to use for signing
    :type priv: bytes

    :return: a tuple of integers `(v, r, s)`, representing the raw ECDSA signature
    :rtype: Tuple[int, int, int]
    """
    z = bytes_to_int(msghash)
    k = deterministic_generate_k(msghash, priv)

    r, y = multiply(G, k)
    s = inv(k, N) * (z + r * bytes_to_int(priv)) % N

    v, r, s = 27 + ((y % 2) ^ (0 if s * 2 < N else 1)), r, s if s * 2 < N else N - s
    return v, r, s


def ecdsa_raw_recover(msghash: bytes, vrs: Tuple[int, int, int]) -> "PlainPoint2D":
    """
    Recover the public key from the signature and message hash.

    :param msghash: the hash of the message to be signed
    :type msghash: bytes
    :param vrs: the signature generated by the `ecdsa_raw_sign` function
    :type vrs: Tuple[int, int, int]

    :return: the recovered public key
    :rtype: PlainPoint2D
    """
    v, r, s = vrs
    if v not in (27, 28):
        raise ValueError(f"value of v was {v}, must be either 27 or 28")
    x = r
    xcubedaxb = (x * x * x + A * x + B) % P
    beta = pow(xcubedaxb, (P + 1) // 4, P)
    y = beta if v % 2 ^ beta % 2 else (P - beta)
    # If xcubedaxb is not a quadratic residue, then r cannot be the x coord
    # for a point on the curve, and so the sig is invalid
    if (xcubedaxb - y * y) % P != 0 or not (r % N) or not (s % N):
        raise ValueError(
            f"sig is invalid, {r} cannot be the x coord for point on curve"
        )
    z = bytes_to_int(msghash)
    Gz = jacobian_multiply(cast("PlainPoint3D", (Gx, Gy, 1)), (N - z) % N)
    XY = jacobian_multiply(cast("PlainPoint3D", (x, y, 1)), s)
    Qr = jacobian_add(Gz, XY)
    Q = jacobian_multiply(Qr, inv(r, N))
    Q_jacobian = from_jacobian(Q)

    return Q_jacobian
