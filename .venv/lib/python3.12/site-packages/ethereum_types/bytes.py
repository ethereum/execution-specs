"""
Sequences of 256-bit values.
"""

from typing import Any, ClassVar, Type, TypeVar

B = TypeVar("B", bound="FixedBytes")


class FixedBytes(bytes):
    """
    Superclass for fixed sized byte arrays. Not intended to be used directly,
    but should be subclassed.
    """

    LENGTH: ClassVar[int]
    """
    Number of bytes in each instance of this class.
    """

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
    """
    Number of bytes in each instance of this class.
    """


class Bytes1(FixedBytes):
    """
    Byte array of exactly one elements.
    """

    LENGTH = 1
    """
    Number of bytes in each instance of this class.
    """


class Bytes4(FixedBytes):
    """
    Byte array of exactly four elements.
    """

    LENGTH = 4
    """
    Number of bytes in each instance of this class.
    """


class Bytes8(FixedBytes):
    """
    Byte array of exactly eight elements.
    """

    LENGTH = 8
    """
    Number of bytes in each instance of this class.
    """


class Bytes20(FixedBytes):
    """
    Byte array of exactly 20 elements.
    """

    LENGTH = 20
    """
    Number of bytes in each instance of this class.
    """


class Bytes32(FixedBytes):
    """
    Byte array of exactly 32 elements.
    """

    LENGTH = 32
    """
    Number of bytes in each instance of this class.
    """


class Bytes48(FixedBytes):
    """
    Byte array of exactly 48 elements.
    """

    LENGTH = 48


class Bytes64(FixedBytes):
    """
    Byte array of exactly 64 elements.
    """

    LENGTH = 64
    """
    Number of bytes in each instance of this class.
    """


class Bytes96(FixedBytes):
    """
    Byte array of exactly 96 elements.
    """

    LENGTH = 96
    """
    Number of bytes in each instance of this class.
    """


class Bytes256(FixedBytes):
    """
    Byte array of exactly 256 elements.
    """

    LENGTH = 256
    """
    Number of bytes in each instance of this class.
    """


Bytes = bytes
"""
Sequence of bytes (octets) of arbitrary length.
"""
