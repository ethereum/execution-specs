"""
Numeric Types
-------------
"""

# flake8: noqa

from __future__ import annotations

from typing import Optional, Tuple, Type


class Uint(int):
    """
    Unsigned positive integer.
    """

    __slots__ = ()

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

    def to_big_endian(self) -> bytes:
        return bytes(bytearray.fromhex(hex(self).lstrip("0x")))
