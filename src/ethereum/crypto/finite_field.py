"""
Finite Fields
^^^^^^^^^^^^^
"""

# flake8: noqa: D102, D105

from typing import Iterable, List, Tuple, Type, TypeVar, Self, cast

from ethereum_types.bytes import Bytes, Bytes32
from typing_extensions import Protocol


class Field(Protocol):
    """
    A type protocol for defining fields.
    """

    __slots__ = ()

    @classmethod
    def zero(cls) -> Self:
        """Returns the additive identity (0) of the field."""
        ...

    @classmethod
    def from_int(cls, n: int) -> Self:
        """Constructs a field element from an integer."""
        ...

    def __radd__(self, left: Self) -> Self:
        """Reverse addition (left + self)."""
        ...

    def __add__(self, right: Self) -> Self:
        """Field addition (self + right)."""
        ...

    def __iadd__(self, right: Self) -> Self:
        """In-place addition (self += right)."""
        ...

    def __sub__(self, right: Self) -> Self:
        """Field subtraction (self - right)."""
        ...

    def __rsub__(self, left: Self) -> Self:
        """Reverse subtraction (left - self)."""
        ...

    def __mul__(self, right: Self) -> Self:
        """Field multiplication (self * right)."""
        ...

    def __rmul__(self, left: Self) -> Self:
        """Reverse multiplication (left * self)."""
        ...

    def __imul__(self, right: Self) -> Self:
        """In-place multiplication (self *= right)."""
        ...

    def __pow__(self, exponent: int) -> Self:
        """Field exponentiation (self ** exponent)."""
        ...

    def __ipow__(self, right: int) -> Self:
        """In-place exponentiation (self **= right)."""
        ...

    def __neg__(self) -> Self:
        """Additive inverse (-self)."""
        ...

    def __truediv__(self, right: Self) -> Self:
        """Field division (self / right)."""
        ...



class PrimeField(int, Field):
    """
    Superclass for integers modulo a prime. Not intended to be used
    directly, but rather to be subclassed.
    """

    __slots__ = ()
    PRIME: int

    @classmethod
    def from_be_bytes(cls, buffer: Bytes) -> Self:
        """
        Converts a sequence of bytes into an element of the field.
        Parameters
        ----------
        buffer :
            Bytes to decode.
        Returns
        -------
        The decoded field element.
        """
        return cls(int.from_bytes(buffer, "big"))

    @classmethod
    def zero(cls) -> Self:
        """Returns the additive identity (0) of the field."""
        return cls.__new__(cls, 0)

    @classmethod
    def from_int(cls, n: int) -> Self:
        """Constructs a field element from an integer."""
        return cls(n)

    def __new__(cls, value: int) -> Self:
        return int.__new__(cls, value % cls.PRIME)

    def __radd__(self, left: Self) -> Self:  # type: ignore[override]
        return self.__add__(left)

    def __add__(self, right: Self) -> Self:  # type: ignore[override]
        if not isinstance(right, int):
            return NotImplemented
        return self.__new__(type(self), int.__add__(self, right))

    def __iadd__(self, right: Self) -> Self:  # type: ignore[override]
        return self.__add__(right)

    def __sub__(self, right: Self) -> Self:  # type: ignore[override]
        if not isinstance(right, int):
            return NotImplemented
        return self.__new__(type(self), int.__sub__(self, right))

    def __rsub__(self, left: Self) -> Self:  # type: ignore[override]
        if not isinstance(left, int):
            return NotImplemented
        return self.__new__(type(self), int.__rsub__(self, left))

    def __mul__(self, right: Self) -> Self:  # type: ignore[override]
        if not isinstance(right, int):
            return NotImplemented
        return self.__new__(type(self), int.__mul__(self, right))

    def __rmul__(self, left: Self) -> Self:  # type: ignore[override]
        return self.__mul__(left)

    def __imul__(self, right: Self) -> Self:  # type: ignore[override]
        return self.__mul__(right)

    # Disabled operations
    __floordiv__ = None  # type: ignore
    __rfloordiv__ = None  # type: ignore
    __ifloordiv__ = None
    __divmod__ = None  # type: ignore
    __rdivmod__ = None  # type: ignore

    def __pow__(self, exponent: int) -> Self:  # type: ignore[override]
        """Modular exponentiation (self ** exponent % PRIME)."""
        return self.__new__(
            type(self), int.__pow__(int(self), exponent, self.PRIME)
        )

    __rpow__ = None  # type: ignore

    def __ipow__(self, right: int) -> Self:  # type: ignore[override]
        return self.__pow__(right)

    # Disabled bitwise operations
    __and__ = None  # type: ignore
    __or__ = None  # type: ignore
    __xor__ = None  # type: ignore
    __rxor__ = None  # type: ignore
    __ixor__ = None
    __rshift__ = None  # type: ignore
    __lshift__ = None  # type: ignore
    __irshift__ = None
    __ilshift__ = None

    def __neg__(self) -> Self:
        """Additive inverse (-self)."""
        return self.__new__(type(self), int.__neg__(self))

    def __truediv__(self, right: Self) -> Self:  # type: ignore[override]
        """Field division (self / right)."""
        return self * right.multiplicative_inverse()

    def multiplicative_inverse(self) -> Self:
        """Returns the multiplicative inverse (self ** -1)."""
        return self ** (-1)

    def to_be_bytes32(self) -> Bytes32:
        """
        Converts this field element to big-endian bytes representation.
        Returns
        -------
        Bytes32
            Big-endian representation with exactly 32 bytes.
        """
        return Bytes32(self.to_bytes(32, "big"))


class GaloisField(tuple, Field):
    """
    Superclass for defining finite fields. Not intended to be used
    directly, but rather to be subclassed.

    Fields are represented as `F_p[x]/(x^n + ...)` where the `MODULUS` is a
    tuple of the non-leading coefficients of the defining polynomial. For
    example `x^3 + 2x^2 + 3x + 4` is `(2, 3, 4)`.

    """

    __slots__ = ()

    PRIME: int
    MODULUS: Tuple[int, ...]
    FROBENIUS_COEFFICIENTS: Tuple[Self, ...]

    @classmethod
    def zero(cls) -> Self:
        """Returns the additive identity (0) of the field."""
        return cls.__new__(cls, [0] * len(cls.MODULUS))

    @classmethod
    def from_int(cls, n: int) -> Self:
        """Constructs a field element from an integer."""
        return cls.__new__(cls, [n] + [0] * (len(cls.MODULUS) - 1))

    def __new__(cls, iterable: Iterable[int]) -> Self:
        self = tuple.__new__(cls, (x % cls.PRIME for x in iterable))
        assert len(self) == len(cls.MODULUS)
        return self

    def __add__(self, right: Self) -> Self:  # type: ignore[override]
        """Field addition (self + right)."""
        if not isinstance(right, type(self)):
            return NotImplemented

        return self.__new__(
            type(self),
            (x + y for (x, y) in zip(self, right)),
        )

    def __radd__(self, left: Self) -> Self:
        """Reverse addition (left + self)."""
        return self.__add__(left)

    def __iadd__(self, right: Self) -> Self:  # type: ignore[override]
        """In-place addition (self += right)."""
        return self.__add__(right)

    def __sub__(self, right: Self) -> Self:
        """Field subtraction (self - right)."""
        if not isinstance(right, type(self)):
            return NotImplemented

        return self.__new__(
            type(self),
            (x - y for (x, y) in zip(self, right)),
        )

    def __rsub__(self, left: Self) -> Self:
        """Reverse subtraction (left - self)."""
        if not isinstance(left, type(self)):
            return NotImplemented

        return self.__new__(
            type(self),
            (x - y for (x, y) in zip(left, self)),
        )

    def __mul__(self, right: Self) -> Self:  # type: ignore[override]
        """Field multiplication (self * right)."""
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

        return self.__new__(type(self), mul[:degree])

    def __rmul__(self, left: Self) -> Self:  # type: ignore[override]
        """Reverse multiplication (left * self)."""
        return self.__mul__(left)

    def __imul__(self, right: Self) -> Self:  # type: ignore[override]
        """In-place multiplication (self *= right)."""
        return self.__mul__(right)

    def __truediv__(self, right: Self) -> Self:
        """Field division (self / right)."""
        return self * right.multiplicative_inverse()

    def __neg__(self) -> Self:
        """Additive inverse (-self)."""
        return self.__new__(type(self), (-a for a in self))

    def scalar_mul(self, x: int) -> Self:
        """
        Multiply a field element by an integer.
        Faster than using `from_int()` and field multiplication.
        """
        return self.__new__(type(self), (x * n for n in self))

    def deg(self) -> int:
        """Returns the degree of the polynomial representation."""
        for i in range(len(self.MODULUS) - 1, -1, -1):
            if self[i] != 0:
                return i
        raise ValueError("deg() does not support zero")

    def multiplicative_inverse(self) -> Self:
        """Calculate the multiplicative inverse using Euclidean algorithm."""
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
                    ans[i] *= q
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

    def __pow__(self, exponent: int) -> Self:
        """Field exponentiation (self ** exponent)."""
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

    def __ipow__(self, right: int) -> Self:
        """In-place exponentiation (self **= right)."""
        return self.__pow__(right)

    @classmethod
    def calculate_frobenius_coefficients(cls) -> Tuple[Self, ...]:
        """
        Calculate the coefficients needed by `frobenius()`.
        """
        coefficients = []
        for i in range(len(cls.MODULUS)):
            x = [0] * len(cls.MODULUS)
            x[i] = 1
            coefficients.append(cls.__new__(cls, x) ** cls.PRIME)
        return tuple(coefficients)

    def frobenius(self) -> Self:
        """
        Returns `self ** p` (Frobenius endomorphism).
        Extremely cheap to compute compared to other exponentiations.
        """
        ans = self.from_int(0)
        for i, a in enumerate(self):
            ans += self.FROBENIUS_COEFFICIENTS[i].scalar_mul(a)
        return ans
