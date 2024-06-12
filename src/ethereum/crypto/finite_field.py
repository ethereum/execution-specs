"""
Finite Fields
^^^^^^^^^^^^^
"""

# flake8: noqa: D102, D105

from typing import Iterable, List, Tuple, Type, TypeVar, cast

from typing_extensions import Protocol

from ..base_types import Bytes, Bytes32

F = TypeVar("F", bound="Field")


class Field(Protocol):
    """
    A type protocol for defining fields.
    """

    __slots__ = ()

    @classmethod
    def zero(cls: Type[F]) -> F:
        ...

    @classmethod
    def from_int(cls: Type[F], n: int) -> F:
        ...

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

    def __neg__(self: F) -> F:
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

    @classmethod
    def from_be_bytes(cls: Type[T], buffer: "Bytes") -> T:
        """
        Converts a sequence of bytes into a element of the field.
        Parameters
        ----------
        buffer :
            Bytes to decode.
        Returns
        -------
        self : `T`
            Unsigned integer decoded from `buffer`.
        """
        return cls(int.from_bytes(buffer, "big"))

    @classmethod
    def zero(cls: Type[T]) -> T:
        return cls.__new__(cls, 0)

    @classmethod
    def from_int(cls: Type[T], n: int) -> T:
        return cls(n)

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
        # For reasons that are unclear, self must be cast to int here under
        # PyPy.
        return self.__new__(
            type(self), int.__pow__(int(self), exponent, self.PRIME)
        )

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

    def __neg__(self: T) -> T:
        return self.__new__(type(self), int.__neg__(self))

    def __truediv__(self: T, right: T) -> T:  # type: ignore[override]
        return self * right.multiplicative_inverse()

    def multiplicative_inverse(self: T) -> T:
        return self ** (-1)

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
    Superclass for defining finite fields. Not intended to be used
    directly, but rather to be subclassed.

    Fields are represented as `F_p[x]/(x^n + ...)` where the `MODULUS` is a
    tuple of the non-leading coefficients of the defining polynomial. For
    example `x^3 + 2x^2 + 3x + 4` is `(2, 3, 4)`.

    In practice the polynomial is likely to be sparse and you should overload
    the `__mul__()` function to take advantage of this fact.
    """

    __slots__ = ()

    PRIME: int
    MODULUS: Tuple[int, ...]
    FROBENIUS_COEFFICIENTS: Tuple["GaloisField", ...]

    @classmethod
    def zero(cls: Type[U]) -> U:
        return cls.__new__(cls, [0] * len(cls.MODULUS))

    @classmethod
    def from_int(cls: Type[U], n: int) -> U:
        return cls.__new__(cls, [n] + [0] * (len(cls.MODULUS) - 1))

    def __new__(cls: Type[U], iterable: Iterable[int]) -> U:
        self = tuple.__new__(cls, (x % cls.PRIME for x in iterable))
        assert len(self) == len(cls.MODULUS)
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
        modulus = self.MODULUS
        degree = len(modulus)
        prime = self.PRIME
        mul = [0] * (degree * 2)

        for i in range(degree):
            for j in range(degree):
                mul[i + j] += self[i] * right[j]

        for i in range(degree * 2 - 1, degree - 1, -1):
            for j in range(i - degree, i):
                mul[j] -= (mul[i] * modulus[degree - (i - j)]) % prime

        return self.__new__(
            type(self),
            mul[:degree],
        )

    def __rmul__(self: U, left: U) -> U:  # type: ignore[override]
        return self.__mul__(left)

    def __imul__(self: U, right: U) -> U:  # type: ignore[override]
        return self.__mul__(right)

    def __truediv__(self: U, right: U) -> U:
        return self * right.multiplicative_inverse()

    def __neg__(self: U) -> U:
        return self.__new__(type(self), (-a for a in self))

    def scalar_mul(self: U, x: int) -> U:
        """
        Multiply a field element by a integer. This is faster than using
        `from_int()` and field multiplication.
        """
        return self.__new__(type(self), (x * n for n in self))

    def deg(self: U) -> int:
        """
        This is a support function for `multiplicative_inverse()`.
        """
        for i in range(len(self.MODULUS) - 1, -1, -1):
            if self[i] != 0:
                return i
        raise ValueError("deg() does not support zero")

    def multiplicative_inverse(self: U) -> U:
        """
        Calculate the multiplicative inverse. Uses the Euclidean algorithm.
        """
        x2: List[int]
        p = self.PRIME
        x1, f1 = list(self.MODULUS), [0] * len(self)
        x2, f2, d2 = list(self), [1] + [0] * (len(self) - 1), self.deg()
        q_0 = pow(x2[d2], -1, p)
        for i in range(d2):
            x1[i + len(x1) - d2] = (x1[i + len(x1) - d2] - q_0 * x2[i]) % p
            f1[i + len(x1) - d2] = (f1[i + len(x1) - d2] - q_0 * f2[i]) % p
        for i in range(len(self.MODULUS) - 1, -1, -1):
            if x1[i] != 0:
                d1 = i
                break
        while True:
            if d1 == 0:
                ans = f1
                q = pow(x1[0], -1, self.PRIME)
                for i in range(len(ans)):
                    ans[i] *= q
                break
            elif d2 == 0:
                ans = f2
                q = pow(x2[0], -1, self.PRIME)
                for i in range(len(ans)):
                    ans *= q
                break
            if d1 < d2:
                q = x2[d2] * pow(x1[d1], -1, self.PRIME)
                for i in range(len(self.MODULUS) - (d2 - d1)):
                    x2[i + (d2 - d1)] = (x2[i + (d2 - d1)] - q * x1[i]) % p
                    f2[i + (d2 - d1)] = (f2[i + (d2 - d1)] - q * f1[i]) % p
                while x2[d2] == 0:
                    d2 -= 1
            else:
                q = x1[d1] * pow(x2[d2], -1, self.PRIME)
                for i in range(len(self.MODULUS) - (d1 - d2)):
                    x1[i + (d1 - d2)] = (x1[i + (d1 - d2)] - q * x2[i]) % p
                    f1[i + (d1 - d2)] = (f1[i + (d1 - d2)] - q * f2[i]) % p
                while x1[d1] == 0:
                    d1 -= 1
        return self.__new__(type(self), ans)

    def __pow__(self: U, exponent: int) -> U:
        degree = len(self.MODULUS)
        if exponent < 0:
            self = self.multiplicative_inverse()
            exponent = -exponent

        res = self.__new__(type(self), [1] + [0] * (degree - 1))
        s = self
        while exponent != 0:
            if exponent % 2 == 1:
                res *= s
            s *= s
            exponent //= 2
        return res

    def __ipow__(self: U, right: int) -> U:
        return self.__pow__(right)

    @classmethod
    def calculate_frobenius_coefficients(cls: Type[U]) -> Tuple[U, ...]:
        """
        Calculate the coefficients needed by `frobenius()`.
        """
        coefficients = []
        for i in range(len(cls.MODULUS)):
            x = [0] * len(cls.MODULUS)
            x[i] = 1
            coefficients.append(cls.__new__(cls, x) ** cls.PRIME)
        return tuple(coefficients)

    def frobenius(self: U) -> U:
        """
        Returns `self ** p`. This function is known as the Frobenius
        endomorphism and has many special mathematical properties. In
        particular it is extremely cheap to compute compared to other
        exponentiations.
        """
        ans = self.from_int(0)
        a: int
        for i, a in enumerate(self):
            ans += cast(U, self.FROBENIUS_COEFFICIENTS[i]).scalar_mul(a)
        return ans
