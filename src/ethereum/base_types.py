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

# flake8: noqa

from __future__ import annotations

from typing import Optional, Tuple, Type

U255_MAX_VALUE = (2 ** 255) - 1
U255_CEIL_VALUE = 2 ** 255
U256_MAX_VALUE = (2 ** 256) - 1
U256_CEIL_VALUE = 2 ** 256
U8_MAX_VALUE = (2 ** 8) - 1


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

    def __new__(cls: Type, value: int) -> "Uint":
        if not isinstance(value, int):
            raise TypeError()

        if value < 0:
            raise ValueError()

        return super(cls, cls).__new__(cls, value)

    def __radd__(self, left: int) -> "Uint":
        return self.__add__(left)

    def __add__(self, right: int) -> "Uint":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0:
            raise ValueError()

        result = super(Uint, self).__add__(right)
        return self.__class__(result)

    def __iadd__(self, right: int) -> "Uint":
        return self.__add__(right)

    def __sub__(self, right: int) -> "Uint":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0:
            raise ValueError()

        if super(Uint, self).__lt__(right):
            raise ValueError()

        result = super(Uint, self).__sub__(right)
        return self.__class__(result)

    def __rsub__(self, left: int) -> "Uint":
        if not isinstance(left, int):
            return NotImplemented

        if left < 0:
            raise ValueError()

        if super(Uint, self).__gt__(left):
            raise ValueError()

        result = super(Uint, self).__rsub__(left)
        return self.__class__(result)

    def __isub__(self, right: int) -> "Uint":
        return self.__sub__(right)

    def __mul__(self, right: int) -> "Uint":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0:
            raise ValueError()

        result = super(Uint, self).__mul__(right)
        return self.__class__(result)

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

        result = super(Uint, self).__floordiv__(right)
        return self.__class__(result)

    def __rfloordiv__(self, left: int) -> "Uint":
        if not isinstance(left, int):
            return NotImplemented

        if left < 0:
            raise ValueError()

        result = super(Uint, self).__rfloordiv__(left)
        return self.__class__(result)

    def __ifloordiv__(self, right: int) -> "Uint":
        return self.__floordiv__(right)

    def __mod__(self, right: int) -> "Uint":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0:
            raise ValueError()

        result = super(Uint, self).__mod__(right)
        return self.__class__(result)

    def __rmod__(self, left: int) -> "Uint":
        if not isinstance(left, int):
            return NotImplemented

        if left < 0:
            raise ValueError()

        result = super(Uint, self).__rmod__(left)
        return self.__class__(result)

    def __imod__(self, right: int) -> "Uint":
        return self.__mod__(right)

    def __divmod__(self, right: int) -> Tuple["Uint", "Uint"]:
        if not isinstance(right, int):
            return NotImplemented

        if right < 0:
            raise ValueError()

        result = super(Uint, self).__divmod__(right)
        return (self.__class__(result[0]), self.__class__(result[1]))

    def __rdivmod__(self, left: int) -> Tuple["Uint", "Uint"]:
        if not isinstance(left, int):
            return NotImplemented

        if left < 0:
            raise ValueError()

        result = super(Uint, self).__rdivmod__(left)
        return (self.__class__(result[0]), self.__class__(result[1]))

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

        result = super(Uint, self).__pow__(right, modulo)
        return self.__class__(result)

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

        result = super(Uint, self).__rpow__(left, modulo)
        return self.__class__(result)

    def __ipow__(self, right: int, modulo: Optional[int] = None) -> "Uint":
        return self.__pow__(right, modulo)

    # TODO: Implement and, or, xor, neg, pos, abs, invert, ...

    def to_be_bytes32(self) -> "Bytes32":
        """
        Converts this arbitrarily sized unsigned integer into its big endian
        representation with exactly 32 bytes.
        Returns
        -------
        big_endian : `Bytes32`
            Big endian (most significant bits first) representation.
        """
        return self.to_bytes(32, "big")

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


class U256(int):
    """
    Unsigned positive integer, which can represent `0` to `2 ** 256 - 1`,
    inclusive.
    """

    MAX_VALUE: "U256"

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

        return cls(value & U256_MAX_VALUE)

    def __new__(cls: Type, value: int) -> "U256":
        if not isinstance(value, int):
            raise TypeError()

        if value < 0 or value > U256_MAX_VALUE:
            raise ValueError()

        return super(cls, cls).__new__(cls, value)

    def __radd__(self, left: int) -> "U256":
        return self.__add__(left)

    def __add__(self, right: int) -> "U256":
        result = self.unchecked_add(right)

        if result == NotImplemented:
            return NotImplemented

        return self.__class__(result)

    def unchecked_add(self, right: int) -> int:
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        return super(U256, self).__add__(right)

    def wrapping_add(self, right: int) -> "U256":
        result = self.unchecked_add(right)

        if result == NotImplemented:
            return NotImplemented

        # This is a fast way of ensuring that the result is < (2 ** 256)
        result &= self.MAX_VALUE
        return self.__class__(result)

    def __iadd__(self, right: int) -> "U256":
        return self.__add__(right)

    def __sub__(self, right: int) -> "U256":
        result = self.unchecked_sub(right)

        if result == NotImplemented:
            return NotImplemented

        return self.__class__(result)

    def unchecked_sub(self, right: int) -> int:
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        return super(U256, self).__sub__(right)

    def wrapping_sub(self, right: int) -> "U256":
        result = self.unchecked_sub(right)

        if result == NotImplemented:
            return NotImplemented

        # This is a fast way of ensuring that the result is < (2 ** 256)
        result &= self.MAX_VALUE
        return self.__class__(result)

    def __rsub__(self, left: int) -> "U256":
        if not isinstance(left, int):
            return NotImplemented

        if left < 0 or left > self.MAX_VALUE:
            raise ValueError()

        result = super(U256, self).__rsub__(left)
        return self.__class__(result)

    def __isub__(self, right: int) -> "U256":
        return self.__sub__(right)

    def unchecked_mul(self, right: int) -> int:
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        return super(U256, self).__mul__(right)

    def wrapping_mul(self, right: int) -> "U256":
        result = self.unchecked_mul(right)

        if result == NotImplemented:
            return NotImplemented

        # This is a fast way of ensuring that the result is < (2 ** 256)
        result &= self.MAX_VALUE
        return self.__class__(result)

    def __mul__(self, right: int) -> "U256":
        result = self.unchecked_mul(right)

        if result == NotImplemented:
            return NotImplemented

        return self.__class__(result)

    def __rmul__(self, left: int) -> "U256":
        return self.__mul__(left)

    def __imul__(self, right: int) -> "U256":
        return self.__mul__(right)

    # Explicitly don't override __truediv__, __rtruediv__, and __itruediv__
    # since they return floats anyway.

    def __floordiv__(self, right: int) -> "U256":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        result = super(U256, self).__floordiv__(right)
        return self.__class__(result)

    def __rfloordiv__(self, left: int) -> "U256":
        if not isinstance(left, int):
            return NotImplemented

        if left < 0 or left > self.MAX_VALUE:
            raise ValueError()

        result = super(U256, self).__rfloordiv__(left)
        return self.__class__(result)

    def __ifloordiv__(self, right: int) -> "U256":
        return self.__floordiv__(right)

    def __mod__(self, right: int) -> "U256":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        result = super(U256, self).__mod__(right)
        return self.__class__(result)

    def __rmod__(self, left: int) -> "U256":
        if not isinstance(left, int):
            return NotImplemented

        if left < 0 or left > self.MAX_VALUE:
            raise ValueError()

        result = super(U256, self).__rmod__(left)
        return self.__class__(result)

    def __imod__(self, right: int) -> "U256":
        return self.__mod__(right)

    def __divmod__(self, right: int) -> Tuple["U256", "U256"]:
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        result = super(U256, self).__divmod__(right)
        return (self.__class__(result[0]), self.__class__(result[1]))

    def __rdivmod__(self, left: int) -> Tuple["U256", "U256"]:
        if not isinstance(left, int):
            return NotImplemented

        if left < 0 or left > self.MAX_VALUE:
            raise ValueError()

        result = super(U256, self).__rdivmod__(left)
        return (self.__class__(result[0]), self.__class__(result[1]))

    def unchecked_pow(self, right: int, modulo: Optional[int] = None) -> int:
        if modulo is not None:
            if not isinstance(modulo, int):
                return NotImplemented

            if modulo < 0 or modulo > self.MAX_VALUE:
                raise ValueError()

        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        return super(U256, self).__pow__(right, modulo)

    def wrapping_pow(self, right: int, modulo: Optional[int] = None) -> "U256":
        result = self.unchecked_pow(right, modulo)

        if result == NotImplemented:
            return NotImplemented

        # This is a fast way of ensuring that the result is < (2 ** 256)
        result &= self.MAX_VALUE
        return self.__class__(result)

    def __pow__(self, right: int, modulo: Optional[int] = None) -> "U256":
        result = self.unchecked_pow(right, modulo)

        if result == NotImplemented:
            return NotImplemented

        return self.__class__(result)

    def __rpow__(self, left: int, modulo: Optional[int] = None) -> "U256":
        if modulo is not None:
            if not isinstance(modulo, int):
                return NotImplemented

            if modulo < 0 or modulo > self.MAX_VALUE:
                raise ValueError()

        if not isinstance(left, int):
            return NotImplemented

        if left < 0 or left > self.MAX_VALUE:
            raise ValueError()

        result = super(U256, self).__rpow__(left, modulo)
        return self.__class__(result)

    def __ipow__(self, right: int, modulo: Optional[int] = None) -> "U256":
        return self.__pow__(right, modulo)

    def __and__(self, right: int) -> "U256":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        return self.__class__(super(U256, self).__and__(right))

    def __or__(self, right: int) -> "U256":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        return self.__class__(super(U256, self).__or__(right))

    def __xor__(self, right: int) -> "U256":
        if not isinstance(right, int):
            return NotImplemented

        if right < 0 or right > self.MAX_VALUE:
            raise ValueError()

        return self.__class__(super(U256, self).__xor__(right))

    def __rxor__(self, left: int) -> "U256":
        if not isinstance(left, int):
            return NotImplemented

        if left < 0 or left > self.MAX_VALUE:
            raise ValueError()

        return self.__class__(super(U256, self).__rxor__(left))

    def __ixor__(self, right: int) -> "U256":
        return self.__xor__(right)

    def __invert__(self) -> "U256":
        result = super(U256, self).__invert__() & U256_MAX_VALUE
        return self.__class__(result)

    def __rshift__(self, shift_by: int) -> "U256":
        if not isinstance(shift_by, int):
            return NotImplemented

        result = super(U256, self).__rshift__(shift_by)
        return self.__class__(result)

    # TODO: Implement neg, pos, abs ...

    def to_be_bytes32(self) -> "Bytes32":
        """
        Converts this 256-bit unsigned integer into its big endian
        representation with exactly 32 bytes.
        Returns
        -------
        big_endian : `Bytes32`
            Big endian (most significant bits first) representation.
        """
        return self.to_bytes(32, "big")

    def to_be_bytes(self) -> "Bytes":
        """
        Converts this 256-bit unsigned integer into its big endian
        representation, omitting leading zero bytes.
        Returns
        -------
        big_endian : `Bytes`
            Big endian (most significant bits first) representation.
        """
        bit_length = self.bit_length()
        byte_length = (bit_length + 7) // 8
        return self.to_bytes(byte_length, "big")

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


U256.MAX_VALUE = U256(U256_MAX_VALUE)


Bytes = bytes
Bytes8 = Bytes
Bytes20 = Bytes
Bytes32 = Bytes
Bytes64 = Bytes
BytesMutable256 = bytearray
