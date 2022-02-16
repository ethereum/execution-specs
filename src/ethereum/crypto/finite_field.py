# flake8: noqa: D102, D105

import math
from typing import Iterable, Tuple, Type, TypeVar, cast

from typing_extensions import Protocol

from ..base_types import Bytes, Bytes32, Uint

p = 21888242871839275222246405745257275088696311157297823662689037894645226208583
primitive_root = 3

F = TypeVar("F", bound="Field")


class Field(Protocol):
    __slots__ = ()

    ZERO: "Field"

    def __radd__(self: F, left: F) -> F:
        ...

    def __add__(self: F, right: F) -> F:
        ...

    def __iadd__(self: F, right: F) -> F:
        ...

    def __sub__(self: F, right: F) -> F:
        ...

    def __rsub__(self: F, left: F) -> F:
        ...

    def __mul__(self: F, right: F) -> F:
        ...

    def __rmul__(self: F, left: F) -> F:
        ...

    def __imul__(self: F, right: F) -> F:
        ...

    def __pow__(self: F, exponent: int) -> F:
        ...

    def __ipow__(self: F, right: int) -> F:
        ...

    def __invert__(self: F) -> F:
        ...

    def __truediv__(self: F, right: F) -> F:
        ...


T = TypeVar("T", bound="PrimeField")


class PrimeField(int, Field):
    """
    Superclass for integers modulo a prime. Not intended to be used
    directly, but rather to be subclassed.
    """

    __slots__ = ()
    PRIME: int
    ZERO: "PrimeField"

    @classmethod
    def from_be_bytes(cls: Type, buffer: "Bytes") -> "Uint":
        """
        Converts a sequence of bytes into a element of the field.
        Parameters
        ----------
        buffer :
            Bytes to decode.
        Returns
        -------
        self : `Uint`
            Unsigned integer decoded from `buffer`.
        """
        return cls(int.from_bytes(buffer, "big"))

    @classmethod
    def zero(cls: Type[T]) -> T:
        return cls.__new__(cls, 0)

    def __new__(cls: Type[T], value: int) -> T:
        return int.__new__(cls, value % cls.PRIME)

    def __radd__(self: T, left: T) -> T:  # type: ignore[override]
        return self.__add__(left)

    def __add__(self: T, right: T) -> T:  # type: ignore[override]
        if not isinstance(right, int):
            return NotImplemented

        return self.__new__(type(self), int.__add__(self, right))

    def __iadd__(self: T, right: T) -> T:  # type: ignore[override]
        return self.__add__(right)

    def __sub__(self: T, right: T) -> T:  # type: ignore[override]
        if not isinstance(right, int):
            return NotImplemented

        return self.__new__(type(self), int.__sub__(self, right))

    def __rsub__(self: T, left: T) -> T:  # type: ignore[override]
        if not isinstance(left, int):
            return NotImplemented

        return self.__new__(type(self), int.__rsub__(self, left))

    def __mul__(self: T, right: T) -> T:  # type: ignore[override]
        if not isinstance(right, int):
            return NotImplemented

        return self.__new__(type(self), int.__mul__(self, right))

    def __rmul__(self: T, left: T) -> T:  # type: ignore[override]
        return self.__mul__(left)

    def __imul__(self: T, right: T) -> T:  # type: ignore[override]
        return self.__mul__(right)

    __floordiv__ = None  # type: ignore
    __rfloordiv__ = None  # type: ignore
    __ifloordiv__ = None
    __divmod__ = None  # type: ignore
    __rdivmod__ = None  # type: ignore

    def __pow__(self: T, exponent: int) -> T:  # type: ignore[override]
        # FIXME: Euclidian Algorithm
        return int.__pow__(self, exponent % (self.PRIME - 1), self.PRIME)

    __rpow__ = None  # type: ignore

    def __ipow__(self: T, right: int) -> T:  # type: ignore[override]
        return self.__pow__(right)

    __and__ = None  # type: ignore
    __or__ = None  # type: ignore
    __xor__ = None  # type: ignore
    __rxor__ = None  # type: ignore
    __ixor__ = None
    __rshift__ = None  # type: ignore
    __lshift__ = None  # type: ignore
    __irshift__ = None
    __ilshift__ = None

    def __invert__(self: T) -> T:
        return self.__new__(type(self), int.__invert__(self))

    def __truediv__(self: T, right: T) -> T:  # type: ignore[override]
        return self * right ** (-1)

    def to_be_bytes32(self) -> "Bytes32":
        """
        Converts this arbitrarily sized unsigned integer into its big endian
        representation with exactly 32 bytes.
        Returns
        -------
        big_endian : `Bytes32`
            Big endian (most significant bits first) representation.
        """
        return Bytes32(self.to_bytes(32, "big"))


U = TypeVar("U", bound="GaloisField")


class GaloisField(tuple, Field):
    """
    FIXME
    """

    __slots__ = ()

    PRIME: int
    DEGREE: int
    PRIMITIVE_ROOT: int
    ZERO: "GaloisField"

    PRIME = 13
    DEGREE = 3
    PRIMITIVE_ROOT = 2

    def __new__(cls: Type[U], iterable: Iterable[int]) -> U:
        self = tuple.__new__(cls, (x % cls.PRIME for x in iterable))
        assert len(self) == self.DEGREE
        return self

    def __add__(self: U, right: U) -> U:  # type: ignore[override]
        if not isinstance(right, type(self)):
            return NotImplemented

        return self.__new__(
            type(self),
            (
                x + y
                for (x, y) in cast(Iterable[Tuple[int, int]], zip(self, right))
            ),
        )

    def __radd__(self: U, left: U) -> U:
        return self.__add__(left)

    def __iadd__(self: U, right: U) -> U:  # type: ignore[override]
        return self.__add__(right)

    def __sub__(self: U, right: U) -> U:
        if not isinstance(right, type(self)):
            return NotImplemented

        x: int
        y: int
        return self.__new__(
            type(self),
            (
                x - y
                for (x, y) in cast(Iterable[Tuple[int, int]], zip(self, right))
            ),
        )

    def __rsub__(self: U, left: U) -> U:
        if not isinstance(left, type(self)):
            return NotImplemented

        return self.__new__(
            type(self),
            (
                x - y
                for (x, y) in cast(Iterable[Tuple[int, int]], zip(left, self))
            ),
        )

    def __mul__(self: U, right: U) -> U:  # type: ignore[override]
        if not isinstance(right, type(self)):
            return NotImplemented

        degree = self.DEGREE
        root = self.PRIMITIVE_ROOT
        mul = [0] * (degree * 2)

        for i in range(degree):
            for j in range(degree):
                mul[i + j] += self[i] * right[j]

        return self.__new__(
            type(self),
            (mul[i] + root * mul[i + degree] for i in range(degree)),
        )

    def __rmul__(self: U, left: U) -> U:  # type: ignore[override]
        return self.__mul__(left)

    def __imul__(self: U, right: U) -> U:  # type: ignore[override]
        return self.__mul__(right)

    def __pow__(self: U, exponent: int) -> U:
        if exponent < 0:
            # FIXME: Euclidian Algorithm
            exponent = self.PRIME + exponent

        res = self.__new__(type(self), [1] + [0] * (self.DEGREE - 1))
        s = self
        while exponent != 0:
            if exponent % 2 == 1:
                res *= s
            s *= s
            exponent //= 2
        return res
