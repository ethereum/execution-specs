"""
Numeric & Array Types
^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Integer and array types which are used by—but not unique to—Ethereum.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable, ClassVar, Optional, Tuple, Type, TypeVar

U8_MAX_VALUE = (2**8) - 1
U32_MAX_VALUE = (2**32) - 1
U32_CEIL_VALUE = 2**32
U64_MAX_VALUE = (2**64) - 1
U255_MAX_VALUE = (2**255) - 1
U255_CEIL_VALUE = 2**255
U256_MAX_VALUE = (2**256) - 1
U256_CEIL_VALUE = 2**256


class Uint(int):
    """
    Unsigned positive integer.
    """

    __slots__ = ()

    @classmethod
    def from_be_bytes(cls: Type, buffer: "Bytes") -> "Uint":
        """
        Converts a sequence of bytes into an arbitrarily sized unsigned integer
        from its big endian representation.
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
    def from_le_bytes(cls: Type, buffer: "Bytes") -> "Uint":
        """
        Convert a series of little endian bytes to an unsigned integer.
        """
        return cls(int.from_bytes(buffer, "little"))

    def __init__(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError()

        if value < 0:
            raise ValueError()

    def __radd__(self, left: int) -> "Uint":
        return self.__add__(left)

    def __add__(self, right: int) -> "Uint":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0:
            raise ValueError()

        return int.__new__(self.__class__, int.__add__(self, right))

    def __iadd__(self, right: int) -> "Uint":
        return self.__add__(right)

    def __sub__(self, right: int) -> "Uint":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or self < right:
            raise ValueError()

        return int.__new__(self.__class__, int.__sub__(self, right))

    def __rsub__(self, left: int) -> "Uint":
        if not isinstance(left, int):
            return NotImplemented

        if left < 0 or self > left:
            raise ValueError()

        return int.__new__(self.__class__, int.__rsub__(self, left))

    def __isub__(self, right: int) -> "Uint":
        return self.__sub__(right)

    def __mul__(self, right: int) -> "Uint":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0:
            raise ValueError()

        return int.__new__(self.__class__, int.__mul__(self, right))

    def __rmul__(self, left: int) -> "Uint":
        return self.__mul__(left)

    def __imul__(self, right: int) -> "Uint":
        return self.__mul__(right)

    # Explicitly don't override __truediv__, __rtruediv__, and __itruediv__
    # since they return floats anyway.

    def __floordiv__(self, right: int) -> "Uint":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0:
            raise ValueError()

        return int.__new__(self.__class__, int.__floordiv__(self, right))

    def __rfloordiv__(self, left: int) -> "Uint":
        if not isinstance(left, int):
            return NotImplemented

        if left < 0:
            raise ValueError()

        return int.__new__(self.__class__, int.__rfloordiv__(self, left))

    def __ifloordiv__(self, right: int) -> "Uint":
        return self.__floordiv__(right)

    def __mod__(self, right: int) -> "Uint":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0:
            raise ValueError()

        return int.__new__(self.__class__, int.__mod__(self, right))

    def __rmod__(self, left: int) -> "Uint":
        if not isinstance(left, int):
            return NotImplemented

        if left < 0:
            raise ValueError()

        return int.__new__(self.__class__, int.__rmod__(self, left))

    def __imod__(self, right: int) -> "Uint":
        return self.__mod__(right)

    def __divmod__(self, right: int) -> Tuple["Uint", "Uint"]:
        if not isinstance(right, int):
            return NotImplemented

        if right < 0:
            raise ValueError()

        result = int.__divmod__(self, right)
        return (
            int.__new__(self.__class__, result[0]),
            int.__new__(self.__class__, result[1]),
        )

    def __rdivmod__(self, left: int) -> Tuple["Uint", "Uint"]:
        if not isinstance(left, int):
            return NotImplemented

        if left < 0:
            raise ValueError()

        result = int.__rdivmod__(self, left)
        return (
            int.__new__(self.__class__, result[0]),
            int.__new__(self.__class__, result[1]),
        )

    def __pow__(self, right: int, modulo: Optional[int] = None) -> "Uint":
        if modulo is not None:
            if not isinstance(modulo, int):
                return NotImplemented

            if modulo < 0:
                raise ValueError()

        if not isinstance(right, int):
            return NotImplemented

        if right < 0:
            raise ValueError()

        return int.__new__(self.__class__, int.__pow__(self, right, modulo))

    def __rpow__(self, left: int, modulo: Optional[int] = None) -> "Uint":
        if modulo is not None:
            if not isinstance(modulo, int):
                return NotImplemented

            if modulo < 0:
                raise ValueError()

        if not isinstance(left, int):
            return NotImplemented

        if left < 0:
            raise ValueError()

        return int.__new__(self.__class__, int.__rpow__(self, left, modulo))

    def __ipow__(self, right: int, modulo: Optional[int] = None) -> "Uint":
        return self.__pow__(right, modulo)

    def __xor__(self, right: int) -> "Uint":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0:
            raise ValueError()

        return int.__new__(self.__class__, int.__xor__(self, right))

    def __rxor__(self, left: int) -> "Uint":
        if not isinstance(left, int):
            return NotImplemented

        if left < 0:
            raise ValueError()

        return int.__new__(self.__class__, int.__rxor__(self, left))

    def __ixor__(self, right: int) -> "Uint":
        return self.__xor__(right)

    # TODO: Implement and, or, neg, pos, abs, invert, ...

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

    def to_be_bytes(self) -> "Bytes":
        """
        Converts this arbitrarily sized unsigned integer into its big endian
        representation.
        Returns
        -------
        big_endian : `Bytes`
            Big endian (most significant bits first) representation.
        """
        bit_length = self.bit_length()
        byte_length = (bit_length + 7) // 8
        return self.to_bytes(byte_length, "big")

    def to_le_bytes(self, number_bytes: int = None) -> "Bytes":
        """
        Converts this arbitrarily sized unsigned integer into its little endian
        representation.

        Parameters
        ----------
        number_bytes :
            Exact number of bytes to return (defaults to the fewest that can
            represent this number.)

        Returns
        -------
        little_endian : `Bytes`
            Little endian (most significant bits last) representation.
        """
        if number_bytes is None:
            bit_length = self.bit_length()
            number_bytes = (bit_length + 7) // 8
        return self.to_bytes(number_bytes, "little")


T = TypeVar("T", bound="FixedUInt")


class FixedUInt(int):
    """
    Superclass for fixed size unsigned integers. Not intended to be used
    directly, but rather to be subclassed.
    """

    MAX_VALUE: ClassVar["FixedUInt"]

    __slots__ = ()

    def __init__(self: T, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError()

        if value < 0 or value > self.MAX_VALUE:
            raise ValueError()

    def __radd__(self: T, left: int) -> T:
        return self.__add__(left)

    def __add__(self: T, right: int) -> T:
        if not isinstance(right, int):
            return NotImplemented

        result = int.__add__(self, right)

        if right < 0 or result > self.MAX_VALUE:
            raise ValueError()

        return int.__new__(self.__class__, result)

    def wrapping_add(self: T, right: int) -> T:
        """
        Return a new instance containing `self + right (mod N)`.

        Parameters
        ----------

        right :
            Other operand for addition.

        Returns
        -------

        sum : T
            The result of adding `self` and `right`, wrapped.
        """
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        # This is a fast way of ensuring that the result is < (2 ** 256)
        return int.__new__(
            self.__class__, int.__add__(self, right) & self.MAX_VALUE
        )

    def __iadd__(self: T, right: int) -> T:
        return self.__add__(right)

    def __sub__(self: T, right: int) -> T:
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE or self < right:
            raise ValueError()

        return int.__new__(self.__class__, int.__sub__(self, right))

    def wrapping_sub(self: T, right: int) -> T:
        """
        Return a new instance containing `self - right (mod N)`.

        Parameters
        ----------

        right :
            Subtrahend operand for subtraction.

        Returns
        -------

        difference : T
            The result of subtracting `right` from `self`, wrapped.
        """
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        # This is a fast way of ensuring that the result is < (2 ** 256)
        return int.__new__(
            self.__class__, int.__sub__(self, right) & self.MAX_VALUE
        )

    def __rsub__(self: T, left: int) -> T:
        if not isinstance(left, int):
            return NotImplemented

        if left < 0 or left > self.MAX_VALUE or self > left:
            raise ValueError()

        return int.__new__(self.__class__, int.__rsub__(self, left))

    def __isub__(self: T, right: int) -> T:
        return self.__sub__(right)

    def __mul__(self: T, right: int) -> T:
        if not isinstance(right, int):
            return NotImplemented

        result = int.__mul__(self, right)

        if right < 0 or result > self.MAX_VALUE:
            raise ValueError()

        return int.__new__(self.__class__, result)

    def wrapping_mul(self: T, right: int) -> T:
        """
        Return a new instance containing `self * right (mod N)`.

        Parameters
        ----------

        right :
            Other operand for multiplication.

        Returns
        -------

        product : T
            The result of multiplying `self` by `right`, wrapped.
        """
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        # This is a fast way of ensuring that the result is < (2 ** 256)
        return int.__new__(
            self.__class__, int.__mul__(self, right) & self.MAX_VALUE
        )

    def __rmul__(self: T, left: int) -> T:
        return self.__mul__(left)

    def __imul__(self: T, right: int) -> T:
        return self.__mul__(right)

    # Explicitly don't override __truediv__, __rtruediv__, and __itruediv__
    # since they return floats anyway.

    def __floordiv__(self: T, right: int) -> T:
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        return int.__new__(self.__class__, int.__floordiv__(self, right))

    def __rfloordiv__(self: T, left: int) -> T:
        if not isinstance(left, int):
            return NotImplemented

        if left < 0 or left > self.MAX_VALUE:
            raise ValueError()

        return int.__new__(self.__class__, int.__rfloordiv__(self, left))

    def __ifloordiv__(self: T, right: int) -> T:
        return self.__floordiv__(right)

    def __mod__(self: T, right: int) -> T:
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        return int.__new__(self.__class__, int.__mod__(self, right))

    def __rmod__(self: T, left: int) -> T:
        if not isinstance(left, int):
            return NotImplemented

        if left < 0 or left > self.MAX_VALUE:
            raise ValueError()

        return int.__new__(self.__class__, int.__rmod__(self, left))

    def __imod__(self: T, right: int) -> T:
        return self.__mod__(right)

    def __divmod__(self: T, right: int) -> Tuple[T, T]:
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        result = super(FixedUInt, self).__divmod__(right)
        return (
            int.__new__(self.__class__, result[0]),
            int.__new__(self.__class__, result[1]),
        )

    def __rdivmod__(self: T, left: int) -> Tuple[T, T]:
        if not isinstance(left, int):
            return NotImplemented

        if left < 0 or left > self.MAX_VALUE:
            raise ValueError()

        result = super(FixedUInt, self).__rdivmod__(left)
        return (
            int.__new__(self.__class__, result[0]),
            int.__new__(self.__class__, result[1]),
        )

    def __pow__(self: T, right: int, modulo: Optional[int] = None) -> T:
        if modulo is not None:
            if not isinstance(modulo, int):
                return NotImplemented

            if modulo < 0 or modulo > self.MAX_VALUE:
                raise ValueError()

        if not isinstance(right, int):
            return NotImplemented

        result = int.__pow__(self, right, modulo)

        if right < 0 or right > self.MAX_VALUE or result > self.MAX_VALUE:
            raise ValueError()

        return int.__new__(self.__class__, result)

    def wrapping_pow(self: T, right: int, modulo: Optional[int] = None) -> T:
        """
        Return a new instance containing `self ** right (mod modulo)`.

        Parameters
        ----------

        right :
            Exponent operand.

        modulo :
            Optional modulus (defaults to `MAX_VALUE + 1`.)

        Returns
        -------

        power : T
            The result of raising `self` to the power of `right`, wrapped.
        """
        if modulo is not None:
            if not isinstance(modulo, int):
                return NotImplemented

            if modulo < 0 or modulo > self.MAX_VALUE:
                raise ValueError()

        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        # This is a fast way of ensuring that the result is < (2 ** 256)
        return int.__new__(
            self.__class__, int.__pow__(self, right, modulo) & self.MAX_VALUE
        )

    def __rpow__(self: T, left: int, modulo: Optional[int] = None) -> T:
        if modulo is not None:
            if not isinstance(modulo, int):
                return NotImplemented

            if modulo < 0 or modulo > self.MAX_VALUE:
                raise ValueError()

        if not isinstance(left, int):
            return NotImplemented

        if left < 0 or left > self.MAX_VALUE:
            raise ValueError()

        return int.__new__(self.__class__, int.__rpow__(self, left, modulo))

    def __ipow__(self: T, right: int, modulo: Optional[int] = None) -> T:
        return self.__pow__(right, modulo)

    def __and__(self: T, right: int) -> T:
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        return int.__new__(self.__class__, int.__and__(self, right))

    def __or__(self: T, right: int) -> T:
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        return int.__new__(self.__class__, int.__or__(self, right))

    def __xor__(self: T, right: int) -> T:
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        return int.__new__(self.__class__, int.__xor__(self, right))

    def __rxor__(self: T, left: int) -> T:
        if not isinstance(left, int):
            return NotImplemented

        if left < 0 or left > self.MAX_VALUE:
            raise ValueError()

        return int.__new__(self.__class__, int.__rxor__(self, left))

    def __ixor__(self: T, right: int) -> T:
        return self.__xor__(right)

    def __invert__(self: T) -> T:
        return int.__new__(
            self.__class__, int.__invert__(self) & self.MAX_VALUE
        )

    def __rshift__(self: T, shift_by: int) -> T:
        if not isinstance(shift_by, int):
            return NotImplemented
        return int.__new__(self.__class__, int.__rshift__(self, shift_by))

    def to_be_bytes(self) -> "Bytes":
        """
        Converts this unsigned integer into its big endian representation,
        omitting leading zero bytes.

        Returns
        -------
        big_endian : `Bytes`
            Big endian (most significant bits first) representation.
        """
        bit_length = self.bit_length()
        byte_length = (bit_length + 7) // 8
        return self.to_bytes(byte_length, "big")

    # TODO: Implement neg, pos, abs ...


class U256(FixedUInt):
    """
    Unsigned positive integer, which can represent `0` to `2 ** 256 - 1`,
    inclusive.
    """

    MAX_VALUE: ClassVar["U256"]

    __slots__ = ()

    @classmethod
    def from_be_bytes(cls: Type, buffer: "Bytes") -> "U256":
        """
        Converts a sequence of bytes into an arbitrarily sized unsigned integer
        from its big endian representation.
        Parameters
        ----------
        buffer :
            Bytes to decode.
        Returns
        -------
        self : `U256`
            Unsigned integer decoded from `buffer`.
        """
        if len(buffer) > 32:
            raise ValueError()

        return cls(int.from_bytes(buffer, "big"))

    @classmethod
    def from_signed(cls: Type, value: int) -> "U256":
        """
        Converts a signed number into a 256-bit unsigned integer.
        Parameters
        ----------
        value :
            Signed number
        Returns
        -------
        self : `U256`
            Unsigned integer obtained from `value`.
        """
        if value >= 0:
            return cls(value)

        return cls(value & cls.MAX_VALUE)

    def to_be_bytes32(self) -> "Bytes32":
        """
        Converts this 256-bit unsigned integer into its big endian
        representation with exactly 32 bytes.
        Returns
        -------
        big_endian : `Bytes32`
            Big endian (most significant bits first) representation.
        """
        return Bytes32(self.to_bytes(32, "big"))

    def to_signed(self) -> int:
        """
        Converts this 256-bit unsigned integer into a signed integer.
        Returns
        -------
        signed_int : `int`
            Signed integer obtained from 256-bit unsigned integer.
        """
        if self <= U255_MAX_VALUE:
            # This means that the sign bit is 0
            return int(self)

        # -1 * (2's complement of U256 value)
        return int(self) - U256_CEIL_VALUE


U256.MAX_VALUE = int.__new__(U256, U256_MAX_VALUE)
"""autoapi_noindex"""


class U32(FixedUInt):
    """
    Unsigned positive integer, which can represent `0` to `2 ** 32 - 1`,
    inclusive.
    """

    MAX_VALUE: ClassVar["U32"]

    __slots__ = ()

    @classmethod
    def from_le_bytes(cls: Type, buffer: "Bytes") -> "U32":
        """
        Converts a sequence of bytes into an arbitrarily sized unsigned integer
        from its little endian representation.
        """
        if len(buffer) > 4:
            raise ValueError()

        return cls(int.from_bytes(buffer, "little"))

    def to_le_bytes4(self) -> "Bytes4":
        """
        Converts this fixed sized unsigned integer into its little endian
        representation, with exactly 4 bytes.

        Returns
        -------
        little_endian : `Bytes4`
            Little endian (most significant bits last) representation.
        """
        return Bytes4(self.to_bytes(4, "little"))

    def to_le_bytes(self) -> "Bytes":
        """
        Converts this fixed sized unsigned integer into its little endian
        representation, in the fewest bytes possible.

        Returns
        -------
        little_endian : `Bytes`
            Little endian (most significant bits last) representation.
        """
        bit_length = self.bit_length()
        byte_length = (bit_length + 7) // 8
        return self.to_bytes(byte_length, "little")


U32.MAX_VALUE = int.__new__(U32, U32_MAX_VALUE)
"""autoapi_noindex"""


class U64(FixedUInt):
    """
    Unsigned positive integer, which can represent `0` to `2 ** 64 - 1`,
    inclusive.
    """

    MAX_VALUE: ClassVar["U64"]

    __slots__ = ()

    @classmethod
    def from_le_bytes(cls: Type, buffer: "Bytes") -> "U64":
        """
        Converts a sequence of bytes into an arbitrarily sized unsigned integer
        from its little endian representation.
        """
        if len(buffer) > 8:
            raise ValueError()

        return cls(int.from_bytes(buffer, "little"))

    def to_le_bytes8(self) -> "Bytes8":
        """
        Converts this fixed sized unsigned integer into its little endian
        representation, with exactly 8 bytes.

        Returns
        -------
        little_endian : `Bytes8`
            Little endian (most significant bits last) representation.
        """
        return Bytes8(self.to_bytes(8, "little"))

    def to_le_bytes(self) -> "Bytes":
        """
        Converts this fixed sized unsigned integer into its little endian
        representation, in the fewest bytes possible.

        Returns
        -------
        little_endian : `Bytes`
            Little endian (most significant bits last) representation.
        """
        bit_length = self.bit_length()
        byte_length = (bit_length + 7) // 8
        return self.to_bytes(byte_length, "little")

    @classmethod
    def from_be_bytes(cls: Type, buffer: "Bytes") -> "U64":
        """
        Converts a sequence of bytes into an unsigned 64 bit integer from its
        big endian representation.

        Parameters
        ----------
        buffer :
            Bytes to decode.
        Returns
        -------
        self : `U64`
            Unsigned integer decoded from `buffer`.
        """
        if len(buffer) > 8:
            raise ValueError()

        return cls(int.from_bytes(buffer, "big"))


U64.MAX_VALUE = int.__new__(U64, U64_MAX_VALUE)
"""autoapi_noindex"""


B = TypeVar("B", bound="FixedBytes")


class FixedBytes(bytes):
    """
    Superclass for fixed sized byte arrays. Not intended to be used directly,
    but should be subclassed.
    """

    LENGTH: int

    __slots__ = ()

    def __new__(cls: Type[B], *args: Any, **kwargs: Any) -> B:
        """
        Create a new instance, ensuring the result has the correct length.
        """
        result = super(FixedBytes, cls).__new__(cls, *args, **kwargs)
        if len(result) != cls.LENGTH:
            raise ValueError(
                f"expected {cls.LENGTH} bytes but got {len(result)}"
            )
        return result


class Bytes0(FixedBytes):
    """
    Byte array of exactly zero elements.
    """

    LENGTH = 0


class Bytes4(FixedBytes):
    """
    Byte array of exactly four elements.
    """

    LENGTH = 4


class Bytes8(FixedBytes):
    """
    Byte array of exactly eight elements.
    """

    LENGTH = 8


class Bytes20(FixedBytes):
    """
    Byte array of exactly 20 elements.
    """

    LENGTH = 20


class Bytes32(FixedBytes):
    """
    Byte array of exactly 32 elements.
    """

    LENGTH = 32


class Bytes64(FixedBytes):
    """
    Byte array of exactly 64 elements.
    """

    LENGTH = 64


class Bytes256(FixedBytes):
    """
    Byte array of exactly 256 elements.
    """

    LENGTH = 256


Bytes = bytes


def _setattr_function(self: Any, attr: str, value: Any) -> None:
    if getattr(self, "_frozen", None):
        raise Exception("Mutating frozen dataclasses is not allowed.")
    else:
        object.__setattr__(self, attr, value)


def _delattr_function(self: Any, attr: str) -> None:
    if self._frozen:
        raise Exception("Mutating frozen dataclasses is not allowed.")
    else:
        object.__delattr__(self, attr)


def _make_init_function(f: Callable) -> Callable:
    def init_function(self: Any, *args: Any, **kwargs: Any) -> None:
        will_be_frozen = kwargs.pop("_frozen", True)
        object.__setattr__(self, "_frozen", False)
        f(self, *args, **kwargs)
        self._frozen = will_be_frozen

    return init_function


def slotted_freezable(cls: Any) -> Any:
    """
    Monkey patches a dataclass so it can be frozen by setting `_frozen` to
    `True` and uses `__slots__` for efficiency.

    Instances will be created frozen by default unless you pass `_frozen=False`
    to `__init__`.
    """
    cls.__slots__ = ("_frozen",) + tuple(cls.__annotations__)
    cls.__init__ = _make_init_function(cls.__init__)
    cls.__setattr__ = _setattr_function
    cls.__delattr__ = _delattr_function
    return type(cls)(cls.__name__, cls.__bases__, dict(cls.__dict__))


S = TypeVar("S")


def modify(obj: S, f: Callable[[S], None]) -> S:
    """
    Create a mutable copy of `obj` (which must be `@slotted_freezable`) and
    apply `f` to the copy before freezing it.

    Parameters
    ----------
    obj : `S`
        Object to copy.
    f : `Callable[[S], None]`
        Function to apply to `obj`.

    Returns
    -------
    new_obj : `S`
        Compact byte array.
    """
    new_obj = replace(obj, _frozen=False)
    f(new_obj)
    new_obj._frozen = True  # type: ignore
    return new_obj
