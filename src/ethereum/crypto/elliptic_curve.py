"""
Elliptic Curves
^^^^^^^^^^^^^^^
"""

from typing import Generic, Type, TypeVar

import coincurve
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256

from .finite_field import Field
from .hash import Hash32

SECP256K1N = U256(
    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
)

F = TypeVar("F", bound=Field)
T = TypeVar("T", bound="EllipticCurve")


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
    r_bytes = r.to_be_bytes32()
    s_bytes = s.to_be_bytes32()

    signature = bytearray([0] * 65)
    signature[32 - len(r_bytes) : 32] = r_bytes
    signature[64 - len(s_bytes) : 64] = s_bytes
    signature[64] = v
    public_key = coincurve.PublicKey.from_signature_and_message(
        bytes(signature), msg_hash, hasher=None
    )
    public_key = public_key.format(compressed=False)[1:]
    return public_key


class EllipticCurve(Generic[F]):
    """
    Superclass for integers modulo a prime. Not intended to be used
    directly, but rather to be subclassed.
    """

    __slots__ = ("x", "y")

    FIELD: Type[F]
    A: F
    B: F

    x: F
    y: F

    def __new__(cls: Type[T], x: F, y: F) -> T:
        """
        Make new point on the curve. The point is not checked to see if it is
        on the curve.
        """
        res = object.__new__(cls)
        res.x = x
        res.y = y
        return res

    def __init__(self, x: F, y: F) -> None:
        """
        Checks if the point is on the curve. To skip this check call
        `__new__()` directly.
        """
        if (
            x != self.FIELD.zero() or y != self.FIELD.zero()
        ) and y ** 2 - x**3 - self.A * x - self.B != self.FIELD.zero():
            raise ValueError("Point not on curve")

    def __eq__(self, other: object) -> bool:
        """
        Test two points for equality.
        """
        if not isinstance(other, type(self)):
            return False
        return self.x == other.x and self.y == other.y

    def __str__(self) -> str:
        """
        Stringify a point as its coordinates.
        """
        return str((self.x, self.y))

    @classmethod
    def point_at_infinity(cls: Type[T]) -> T:
        """
        Return the point at infinity. This is the identity element of the group
        operation.

        The point at infinity doesn't actually have coordinates so we use
        `(0, 0)` (which isn't on the curve) to represent it.
        """
        return cls.__new__(cls, cls.FIELD.zero(), cls.FIELD.zero())

    def double(self: T) -> T:
        """
        Add a point to itself.
        """
        x, y, F = self.x, self.y, self.FIELD
        if x == 0 and y == 0:
            return self
        lam = (F.from_int(3) * x**2 + self.A) / (F.from_int(2) * y)
        new_x = lam**2 - x - x
        new_y = lam * (x - new_x) - y
        return self.__new__(type(self), new_x, new_y)

    def __add__(self: T, other: T) -> T:
        """
        Add two points together.
        """
        ZERO = self.FIELD.zero()
        self_x, self_y, other_x, other_y = self.x, self.y, other.x, other.y
        if self_x == ZERO and self_y == ZERO:
            return other
        if other_x == ZERO and other_y == ZERO:
            return self
        if self_x == other_x:
            if self_y == other_y:
                return self.double()
            else:
                return self.point_at_infinity()
        lam = (other_y - self_y) / (other_x - self_x)
        x = lam**2 - self_x - other_x
        y = lam * (self_x - x) - self_y
        return self.__new__(type(self), x, y)

    def mul_by(self: T, n: int) -> T:
        """
        Multiply `self` by `n` using the double and add algorithm.
        """
        res = self.__new__(type(self), self.FIELD.zero(), self.FIELD.zero())
        s = self
        while n != 0:
            if n % 2 == 1:
                res = res + s
            s = s + s
            n //= 2
        return res
