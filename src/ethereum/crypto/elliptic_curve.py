"""
Elliptic Curves
^^^^^^^^^^^^^^^
"""

import coincurve
from Crypto.Util.asn1 import DerSequence
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256

from ethereum.exceptions import InvalidSignatureError

from .hash import Hash32

SECP256K1B = U256(7)
SECP256K1P = U256(
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
)
SECP256K1N = U256(
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
)


def secp256k1_recover(r: U256, s: U256, v: U256, msg_hash: Hash32) -> Bytes:
    """
    Recovers the public key from a given signature.

    Parameters
    ----------
    r :
        TODO
    s :
        TODO
    v :
        TODO
    msg_hash :
        Hash of the message being recovered.

    Returns
    -------
    public_key : `ethereum.base_types.Bytes`
        Recovered public key.
    """
    is_square = pow(
        pow(r, U256(3), SECP256K1P) + SECP256K1B,
        (SECP256K1P - U256(1)) // U256(2),
        SECP256K1P,
    )

    if is_square != 1:
        raise InvalidSignatureError(
            "r is not the x-coordinate of a point on the secp256k1 curve"
        )

    r_bytes = r.to_be_bytes32()
    s_bytes = s.to_be_bytes32()

    signature = bytearray([0] * 65)
    signature[32 - len(r_bytes) : 32] = r_bytes
    signature[64 - len(s_bytes) : 64] = s_bytes
    signature[64] = v

    # If the recovery algorithm returns the point at infinity,
    # the signature is considered invalid
    # the below function will raise a ValueError.
    try:
        public_key = coincurve.PublicKey.from_signature_and_message(
            bytes(signature), msg_hash, hasher=None
        )
    except ValueError as e:
        raise InvalidSignatureError from e

    public_key = public_key.format(compressed=False)[1:]
    return public_key


SECP256R1N = U256(
    0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
)
SECP256R1P = U256(
    0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
)
SECP256R1A = U256(
    0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC
)
SECP256R1B = U256(
    0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
)


def secp256r1_verify(
    r: U256, s: U256, x: U256, y: U256, msg_hash: Hash32
) -> None:
    """
    Verifies a P-256 signature.

    Parameters
    ----------
    r :
        the `r` component of the signature
    s :
        the `s` component of the signature
    x :
        the `x` coordinate of the public key
    y :
        the `y` coordinate of the public key
    msg_hash :
        Hash of the message being recovered.

    Raises
    ------

    Raises an `InvalidSignatureError` if the signature is not valid.
    """
    # Convert U256 to regular integers for DerSequence
    r_int = int(r)
    s_int = int(s)
    x_int = int(x)
    y_int = int(y)

    sig = DerSequence([r_int, s_int]).encode()

    pubnum = ec.EllipticCurvePublicNumbers(x_int, y_int, ec.SECP256R1())
    pubkey = pubnum.public_key(default_backend())

    try:
        pubkey.verify(sig, msg_hash, ec.ECDSA(Prehashed(hashes.SHA256())))
    except InvalidSignature as e:
        raise InvalidSignatureError from e


def is_on_curve_secp256r1(x: U256, y: U256) -> bool:
    """
    Checks if a point is on the secp256r1 curve.

    The point (x, y) must satisfy the curve equation:
    y^2 ≡ x^3 + a*x + b (mod p)

    Parameters
    ----------
    x : U256
        The x-coordinate of the point
    y : U256
        The y-coordinate of the point

    Returns
    -------
    bool
        True if the point is on the curve, False otherwise
    """
    # Convert U256 to int for calculations
    x_int = int(x)
    y_int = int(y)
    p_int = int(SECP256R1P)
    a_int = int(SECP256R1A)
    b_int = int(SECP256R1B)

    # Calculate y^2 mod p
    y_squared = (y_int * y_int) % p_int

    # Calculate x^3 + ax + b mod p
    x_cubed = (x_int * x_int * x_int) % p_int
    ax = (a_int * x_int) % p_int
    right_side = (x_cubed + ax + b_int) % p_int

    return y_squared == right_side
