# flake8: noqa

from typing import Generic, Type, TypeVar

from .finite_field import Field

F = TypeVar("F", bound=Field)
T = TypeVar("T", bound="EllipticCurve")


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
        res = object.__new__(cls)
        res.x = x
        res.y = y
        return res

    def __init__(self, x: F, y: F) -> None:
        if (
            x != self.FIELD.zero() or y != self.FIELD.zero()
        ) and y ** 2 - x ** 3 - self.A * x - self.B != self.FIELD.zero():
            print(y ** 2 - x ** 3 - self.A * x - self.B)
            raise ValueError("Point not on curve")

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __str__(self) -> str:
        return str((self.x, self.y))

    @classmethod
    def inf(cls: Type[T]) -> T:
        return cls.__new__(cls, cls.FIELD.zero(), cls.FIELD.zero())

    def double(self: T) -> T:
        x, y, F = self.x, self.y, self.FIELD
        if x == 0 and y == 0:
            return self
        lam = (F.from_int(3) * x ** 2 + self.A) / (F.from_int(2) * y)
        new_x = lam ** 2 - x - x
        new_y = lam * (x - new_x) - y
        return self.__new__(type(self), new_x, new_y)

    def __add__(self: T, other: T) -> T:
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
                return self.inf()
        lam = (other_y - self_y) / (other_x - self_x)
        x = lam ** 2 - self_x - other_x
        y = lam * (self_x - x) - self_y
        return self.__new__(type(self), x, y)

    def mul_by(self: T, n: int) -> T:
        res = self.__new__(type(self), self.FIELD.zero(), self.FIELD.zero())
        s = self
        while n != 0:
            if n % 2 == 1:
                res = res + s
            s = s + s
            n //= 2
        return res
