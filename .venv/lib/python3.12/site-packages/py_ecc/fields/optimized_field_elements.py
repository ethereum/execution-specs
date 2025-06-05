from functools import (
    cached_property,
    total_ordering,
)
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from py_ecc.utils import (
    deg,
    prime_field_inv,
)

if TYPE_CHECKING:
    from py_ecc.typing import (
        FQ2_modulus_coeffs_type,
        FQ12_modulus_coeffs_type,
    )


# These new TypeVars are needed because these classes are kind of base classes and
# we need the output type to correspond to the type of the inherited class
T_FQ = TypeVar("T_FQ", bound="FQ")
T_FQP = TypeVar("T_FQP", bound="FQP")
T_FQ2 = TypeVar("T_FQ2", bound="FQ2")
T_FQ12 = TypeVar("T_FQ12", bound="FQ12")
IntOrFQ = Union[int, "FQ"]


def mod_int(x: IntOrFQ, n: int) -> int:
    if isinstance(x, int):
        return x % n
    elif isinstance(x, FQ):
        return x.n % n
    else:
        raise TypeError(f"Only int and T_FQ types are accepted: got {type(x)}")


@total_ordering
class FQ:
    """
    A class for field elements in FQ. Wrap a number in this class,
    and it becomes a field element.
    """

    n: int
    field_modulus: int

    def __init__(self: T_FQ, val: IntOrFQ) -> None:
        if not hasattr(self, "field_modulus"):
            raise AttributeError("Field Modulus hasn't been specified")

        if isinstance(val, FQ):
            self.n = val.n
        elif isinstance(val, int):
            self.n = val % self.field_modulus
        else:
            raise TypeError(
                f"Expected an int or FQ object, but got object of type {type(val)}"
            )

    def __add__(self: T_FQ, other: IntOrFQ) -> T_FQ:
        if isinstance(other, FQ):
            on = other.n
        elif isinstance(other, int):
            on = other
        else:
            raise TypeError(
                f"Expected an int or FQ object, but got object of type {type(other)}"
            )

        return type(self)((self.n + on) % self.field_modulus)

    def __mul__(self: T_FQ, other: IntOrFQ) -> T_FQ:
        if isinstance(other, FQ):
            on = other.n
        elif isinstance(other, int):
            on = other
        else:
            raise TypeError(
                f"Expected an int or FQ object, but got object of type {type(other)}"
            )

        return type(self)((self.n * on) % self.field_modulus)

    def __rmul__(self: T_FQ, other: IntOrFQ) -> T_FQ:
        return self * other

    def __radd__(self: T_FQ, other: IntOrFQ) -> T_FQ:
        return self + other

    def __rsub__(self: T_FQ, other: IntOrFQ) -> T_FQ:
        if isinstance(other, FQ):
            on = other.n
        elif isinstance(other, int):
            on = other
        else:
            raise TypeError(
                f"Expected an int or FQ object, but got object of type {type(other)}"
            )

        return type(self)((on - self.n) % self.field_modulus)

    def __sub__(self: T_FQ, other: IntOrFQ) -> T_FQ:
        if isinstance(other, FQ):
            on = other.n
        elif isinstance(other, int):
            on = other
        else:
            raise TypeError(
                f"Expected an int or FQ object, but got object of type {type(other)}"
            )

        return type(self)((self.n - on) % self.field_modulus)

    def __mod__(self: T_FQ, other: IntOrFQ) -> T_FQ:
        raise NotImplementedError("Modulo Operation not yet supported by fields")

    def __div__(self: T_FQ, other: IntOrFQ) -> T_FQ:
        if isinstance(other, FQ):
            on = other.n
        elif isinstance(other, int):
            on = other
        else:
            raise TypeError(
                f"Expected an int or FQ object, but got object of type {type(other)}"
            )

        return type(self)(
            self.n * prime_field_inv(on, self.field_modulus) % self.field_modulus
        )

    def __truediv__(self: T_FQ, other: IntOrFQ) -> T_FQ:
        return self.__div__(other)

    def __rdiv__(self: T_FQ, other: IntOrFQ) -> T_FQ:
        if isinstance(other, FQ):
            on = other.n
        elif isinstance(other, int):
            on = other
        else:
            raise TypeError(
                f"Expected an int or FQ object, but got object of type {type(other)}"
            )

        return type(self)(
            prime_field_inv(self.n, self.field_modulus) * on % self.field_modulus
        )

    def __rtruediv__(self: T_FQ, other: IntOrFQ) -> T_FQ:
        return self.__rdiv__(other)

    def __pow__(self: T_FQ, other: int) -> T_FQ:
        if other == 0:
            return type(self)(1)
        elif other == 1:
            return type(self)(self.n)
        elif other % 2 == 0:
            return (self * self) ** (other // 2)
        else:
            return ((self * self) ** int(other // 2)) * self

    def __eq__(self: T_FQ, other: Any) -> bool:
        if isinstance(other, FQ):
            return self.n == other.n
        elif isinstance(other, int):
            return self.n == other
        else:
            raise TypeError(
                f"Expected an int or FQ object, but got object of type {type(other)}"
            )

    def __ne__(self: T_FQ, other: Any) -> bool:
        return not self == other

    def __neg__(self: T_FQ) -> T_FQ:
        return type(self)(-self.n)

    def __repr__(self: T_FQ) -> str:
        return repr(self.n)

    def __int__(self: T_FQ) -> int:
        return self.n

    def __lt__(self: T_FQ, other: IntOrFQ) -> bool:
        if isinstance(other, FQ):
            on = other.n
        elif isinstance(other, int):
            on = other
        else:
            raise TypeError(
                f"Expected an int or FQ object, but got object of type {type(other)}"
            )
        return self.n < on

    @cached_property
    def sgn0(self: T_FQ) -> int:
        """
        Calculates the sign of a value.
        sgn0(x) = 1 when x is 'negative'; otherwise, sg0(x) = 0

        Note this is an optimized variant for m = 1

        Defined here:
        https://tools.ietf.org/html/draft-irtf-cfrg-hash-to-curve-09#section-4.1
        """
        return self.n % 2

    @classmethod
    def one(cls: Type[T_FQ]) -> T_FQ:
        return cls(1)

    @classmethod
    def zero(cls: Type[T_FQ]) -> T_FQ:
        return cls(0)


class FQP:
    """
    A class for elements in polynomial extension fields
    """

    degree: int = 0
    field_modulus: int
    mc_tuples: List[Tuple[int, int]]

    def __init__(
        self, coeffs: Sequence[IntOrFQ], modulus_coeffs: Sequence[IntOrFQ] = ()
    ) -> None:
        if not hasattr(self, "field_modulus"):
            raise AttributeError("Field Modulus hasn't been specified")

        if len(coeffs) != len(modulus_coeffs):
            raise Exception("coeffs and modulus_coeffs aren't of the same length")

        # Not converting coeffs to FQ or explicitly making them integers
        # for performance reasons
        if isinstance(coeffs[0], int):
            self.coeffs: Tuple[IntOrFQ, ...] = tuple(
                coeff % self.field_modulus for coeff in coeffs
            )
        else:
            self.coeffs = tuple(coeffs)
        # The coefficients of the modulus, without the leading [1]
        self.modulus_coeffs: Tuple[IntOrFQ, ...] = tuple(modulus_coeffs)
        # The degree of the extension field
        self.degree = len(self.modulus_coeffs)

    def __add__(self: T_FQP, other: T_FQP) -> T_FQP:
        if not isinstance(other, type(self)):
            raise TypeError(
                f"Expected an FQP object, but got object of type {type(other)}"
            )

        return type(self)(
            [int(x + y) % self.field_modulus for x, y in zip(self.coeffs, other.coeffs)]
        )

    def __sub__(self: T_FQP, other: T_FQP) -> T_FQP:
        if not isinstance(other, type(self)):
            raise TypeError(
                f"Expected an FQP object, but got object of type {type(other)}"
            )

        return type(self)(
            [int(x - y) % self.field_modulus for x, y in zip(self.coeffs, other.coeffs)]
        )

    def __mod__(self: T_FQP, other: Union[int, T_FQP]) -> T_FQP:
        raise NotImplementedError("Modulo Operation not yet supported by fields")

    def __mul__(self: T_FQP, other: Union[int, T_FQP]) -> T_FQP:
        if isinstance(other, int):
            return type(self)(
                [int(c) * other % self.field_modulus for c in self.coeffs]
            )
        elif isinstance(other, FQP):
            b = [0] * (self.degree * 2 - 1)
            inner_enumerate = list(enumerate(other.coeffs))
            for i, eli in enumerate(self.coeffs):
                for j, elj in inner_enumerate:
                    b[i + j] += int(eli * elj)
            # MID = len(self.coeffs) // 2
            for exp in range(self.degree - 2, -1, -1):
                top = b.pop()
                for i, c in self.mc_tuples:
                    b[exp + i] -= top * c
            return type(self)([x % self.field_modulus for x in b])
        else:
            raise TypeError(
                f"Expected an int or FQP object, but got object of type {type(other)}"
            )

    def __rmul__(self: T_FQP, other: Union[int, T_FQP]) -> T_FQP:
        return self * other

    def __div__(self: T_FQP, other: Union[int, T_FQP]) -> T_FQP:
        if isinstance(other, int):
            return type(self)(
                [
                    int(c)
                    * prime_field_inv(other, self.field_modulus)
                    % self.field_modulus
                    for c in self.coeffs
                ]
            )
        elif isinstance(other, type(self)):
            return self * other.inv()
        else:
            raise TypeError(
                f"Expected an int or FQP object, but got object of type {type(other)}"
            )

    def __truediv__(self: T_FQP, other: Union[int, T_FQP]) -> T_FQP:
        return self.__div__(other)

    def __pow__(self: T_FQP, other: int) -> T_FQP:
        o = type(self)([1] + [0] * (self.degree - 1))
        t = self
        while other > 0:
            if other & 1:
                o = o * t
            other >>= 1
            t = t * t
        return o

    def optimized_poly_rounded_div(
        self, a: Sequence[IntOrFQ], b: Sequence[IntOrFQ]
    ) -> Sequence[IntOrFQ]:
        dega = deg(a)
        degb = deg(b)
        temp = [x for x in a]
        o = [0 for x in a]
        for i in range(dega - degb, -1, -1):
            o[i] = int(
                o[i]
                + temp[degb + i] * prime_field_inv(int(b[degb]), self.field_modulus)
            )
            for c in range(degb + 1):
                temp[c + i] = temp[c + i] - o[c]
        return [x % self.field_modulus for x in o[: deg(o) + 1]]

    # Extended euclidean algorithm used to find the modular inverse
    def inv(self: T_FQP) -> T_FQP:
        lm, hm = [1] + [0] * self.degree, [0] * (self.degree + 1)
        low, high = (
            cast(List[IntOrFQ], list(self.coeffs + (0,))),
            cast(List[IntOrFQ], list(self.modulus_coeffs + (1,))),
        )
        while deg(low):
            r = cast(List[IntOrFQ], list(self.optimized_poly_rounded_div(high, low)))
            r += [0] * (self.degree + 1 - len(r))
            nm = [x for x in hm]
            new = [x for x in high]
            # assert len(lm) == len(hm) == len(low) == len(high) == len(nm) == len(new) == self.degree + 1  # noqa: E501
            for i in range(self.degree + 1):
                for j in range(self.degree + 1 - i):
                    nm[i + j] -= lm[i] * int(r[j])
                    new[i + j] -= low[i] * r[j]
            nm = [x % self.field_modulus for x in nm]
            new = [int(x) % self.field_modulus for x in new]
            lm, low, hm, high = nm, new, lm, low
        return type(self)(lm[: self.degree]) / int(low[0])

    def __repr__(self) -> str:
        return repr(self.coeffs)

    def __eq__(self: T_FQP, other: Any) -> bool:
        if not isinstance(other, type(self)):
            raise TypeError(
                f"Expected an FQP object, but got object of type {type(other)}"
            )

        for c1, c2 in zip(self.coeffs, other.coeffs):
            if c1 != c2:
                return False
        return True

    def __ne__(self: T_FQP, other: Any) -> bool:
        return not self == other

    def __neg__(self: T_FQP) -> T_FQP:
        return type(self)([-c for c in self.coeffs])

    @cached_property
    def sgn0(self: T_FQP) -> int:
        """
        Calculates the sign of a value.
        sgn0(x) = 1 when x is 'negative'; otherwise, sg0(x) = 0

        Defined here:
        https://tools.ietf.org/html/draft-irtf-cfrg-hash-to-curve-09#section-4.1
        """
        sign = 0
        zero = 1
        for x_i in self.coeffs:
            sign_i = mod_int(x_i, 2)
            zero_i = x_i == 0
            sign = sign or (zero and sign_i)
            zero = zero and zero_i
        return sign

    @classmethod
    def one(cls: Type[T_FQP]) -> T_FQP:
        return cls([1] + [0] * (cls.degree - 1))

    @classmethod
    def zero(cls: Type[T_FQP]) -> T_FQP:
        return cls([0] * cls.degree)


class FQ2(FQP):
    """
    The quadratic extension field
    """

    degree: int = 2
    FQ2_MODULUS_COEFFS: "FQ2_modulus_coeffs_type"

    def __init__(self, coeffs: Sequence[IntOrFQ]) -> None:
        if not hasattr(self, "FQ2_MODULUS_COEFFS"):
            raise AttributeError("FQ2 Modulus Coeffs haven't been specified")

        self.mc_tuples = [(i, c) for i, c in enumerate(self.FQ2_MODULUS_COEFFS) if c]
        super().__init__(coeffs, self.FQ2_MODULUS_COEFFS)

    @cached_property
    def sgn0(self: T_FQP) -> int:
        """
        Calculates the sign of a value.
        sgn0(x) = 1 when x is 'negative'; otherwise, sg0(x) = 0

        Note this is an optimized variant for m = 2

        Defined here:
        https://tools.ietf.org/html/draft-irtf-cfrg-hash-to-curve-09#section-4.1
        """
        x_0, x_1 = self.coeffs
        sign_0 = mod_int(x_0, 2)
        zero_0 = x_0 == 0
        sign_1 = mod_int(x_1, 2)
        return sign_0 or (zero_0 and sign_1)


class FQ12(FQP):
    """
    The 12th-degree extension field
    """

    degree: int = 12
    FQ12_MODULUS_COEFFS: "FQ12_modulus_coeffs_type"

    def __init__(self, coeffs: Sequence[IntOrFQ]) -> None:
        if not hasattr(self, "FQ12_MODULUS_COEFFS"):
            raise AttributeError("FQ12 Modulus Coeffs haven't been specified")

        self.mc_tuples = [(i, c) for i, c in enumerate(self.FQ12_MODULUS_COEFFS) if c]
        super().__init__(coeffs, self.FQ12_MODULUS_COEFFS)
