"""
Elliptic Curves
^^^^^^^^^^^^^^^
"""

import coincurve
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
