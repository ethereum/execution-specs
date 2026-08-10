"""
The secp256k1 operations required by the RLPx handshake.

Transaction signing elsewhere in the framework only needs to sign and
recover, which `spec256k1` provides. RLPx additionally needs a raw
Diffie-Hellman agreement (a point multiplication by a foreign public
key), which it does not expose, so the group arithmetic lives here.
"""

from typing import Tuple

from spec256k1 import PrivateKey

FIELD_PRIME = 2**256 - 2**32 - 977
"""Prime of the field the curve is defined over."""

Point = Tuple[int, int]
"""An affine curve point. The point at infinity is `(0, 0)`."""


def _add(left: Point, right: Point) -> Point:
    """Return the sum of two affine curve points."""
    if left == (0, 0):
        return right
    if right == (0, 0):
        return left

    left_x, left_y = left
    right_x, right_y = right

    if left_x == right_x:
        if (left_y + right_y) % FIELD_PRIME == 0:
            return (0, 0)
        slope = (
            3 * left_x * left_x * pow(2 * left_y, FIELD_PRIME - 2, FIELD_PRIME)
        ) % FIELD_PRIME
    else:
        slope = (
            (right_y - left_y)
            * pow(right_x - left_x, FIELD_PRIME - 2, FIELD_PRIME)
        ) % FIELD_PRIME

    sum_x = (slope * slope - left_x - right_x) % FIELD_PRIME
    sum_y = (slope * (left_x - sum_x) - left_y) % FIELD_PRIME
    return (sum_x, sum_y)


def _multiply(point: Point, scalar: int) -> Point:
    """Return `scalar` times `point` by double-and-add."""
    result: Point = (0, 0)
    addend = point
    while scalar:
        if scalar & 1:
            result = _add(result, addend)
        addend = _add(addend, addend)
        scalar >>= 1
    return result


def public_key_bytes(private_key: bytes) -> bytes:
    """
    Return the 64 byte uncompressed public key for `private_key`.

    The leading `0x04` tag of the SEC encoding is stripped: RLPx carries
    public keys as bare coordinate pairs.
    """
    return PrivateKey(private_key).public_key.format(compressed=False)[1:]


def agree(private_key: bytes, public_key: bytes) -> bytes:
    """
    Return the x coordinate of `private_key` times `public_key`.

    This is the raw Diffie-Hellman agreement used to derive the RLPx
    static and ephemeral shared secrets. `public_key` is the 64 byte
    coordinate pair form.
    """
    point = (
        int.from_bytes(public_key[:32], "big"),
        int.from_bytes(public_key[32:], "big"),
    )
    shared_x, _ = _multiply(point, int.from_bytes(private_key, "big"))
    return shared_x.to_bytes(32, "big")
