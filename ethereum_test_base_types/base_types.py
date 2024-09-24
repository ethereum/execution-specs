"""
Basic type primitives used to define other types.
"""

from typing import Any, ClassVar, SupportsBytes, Type, TypeVar

from Crypto.Hash import keccak
from pydantic import GetCoreSchemaHandler
from pydantic_core.core_schema import (
    PlainValidatorFunctionSchema,
    no_info_plain_validator_function,
    to_string_ser_schema,
)

from .conversions import (
    BytesConvertible,
    FixedSizeBytesConvertible,
    NumberConvertible,
    to_bytes,
    to_fixed_size_bytes,
    to_number,
)

N = TypeVar("N", bound="Number")


class ToStringSchema:
    """
    Type converter to add a simple pydantic schema that correctly parses and serializes the type.
    """

    @staticmethod
    def __get_pydantic_core_schema__(
        source_type: Any, handler: GetCoreSchemaHandler
    ) -> PlainValidatorFunctionSchema:
        """
        Calls the class constructor without info and appends the serialization schema.
        """
        return no_info_plain_validator_function(
            source_type,
            serialization=to_string_ser_schema(),
        )


class Number(int, ToStringSchema):
    """
    Class that helps represent numbers in tests.
    """

    def __new__(cls, input: NumberConvertible | N):
        """
        Creates a new Number object.
        """
        return super(Number, cls).__new__(cls, to_number(input))

    def __str__(self) -> str:
        """
        Returns the string representation of the number.
        """
        return str(int(self))

    def hex(self) -> str:
        """
        Returns the hexadecimal representation of the number.
        """
        return hex(self)

    @classmethod
    def or_none(cls: Type[N], input: N | NumberConvertible | None) -> N | None:
        """
        Converts the input to a Number while accepting None.
        """
        if input is None:
            return input
        return cls(input)


class Wei(Number):
    """
    Class that helps represent wei that can be parsed from strings
    """

    def __new__(cls, input: NumberConvertible | N):
        """
        Creates a new Number object.
        """
        if isinstance(input, str):
            words = input.split()
            multiplier = 1
            assert len(words) <= 2
            value_str = words[0]
            if len(words) > 1:
                unit = words[1].lower()
                multiplier = cls._get_multiplier(unit)
            value: float
            if "**" in value_str:
                base, exp = value_str.split("**")
                value = float(base) ** int(exp)
            else:
                value = float(value_str)
            return super(Number, cls).__new__(cls, value * multiplier)
        return super(Number, cls).__new__(cls, to_number(input))

    @staticmethod
    def _get_multiplier(unit: str) -> int:
        """
        Returns the multiplier for the given unit of wei, handling synonyms.
        """
        match unit:
            case "wei":
                return 1
            case "kwei" | "babbage" | "femtoether":
                return 10**3
            case "mwei" | "lovelace" | "picoether":
                return 10**6
            case "gwei" | "shannon" | "nanoether" | "nano":
                return 10**9
            case "szabo" | "microether" | "micro":
                return 10**12
            case "finney" | "milliether" | "milli":
                return 10**15
            case "ether":
                return 10**18
            case _:
                raise ValueError(f"Invalid unit {unit}")


class HexNumber(Number):
    """
    Class that helps represent an hexadecimal numbers in tests.
    """

    def __str__(self) -> str:
        """
        Returns the string representation of the number.
        """
        return self.hex()


class ZeroPaddedHexNumber(HexNumber):
    """
    Class that helps represent zero padded hexadecimal numbers in tests.
    """

    def hex(self) -> str:
        """
        Returns the hexadecimal representation of the number.
        """
        if self == 0:
            return "0x00"
        hex_str = hex(self)[2:]
        if len(hex_str) % 2 == 1:
            return "0x0" + hex_str
        return "0x" + hex_str


NumberBoundTypeVar = TypeVar("NumberBoundTypeVar", Number, HexNumber, ZeroPaddedHexNumber)


class Bytes(bytes, ToStringSchema):
    """
    Class that helps represent bytes of variable length in tests.
    """

    def __new__(cls, input: BytesConvertible):
        """
        Creates a new Bytes object.
        """
        if type(input) is cls:
            return input
        return super(Bytes, cls).__new__(cls, to_bytes(input))

    def __hash__(self) -> int:
        """
        Returns the hash of the bytes.
        """
        return super(Bytes, self).__hash__()

    def __str__(self) -> str:
        """
        Returns the hexadecimal representation of the bytes.
        """
        return self.hex()

    def hex(self, *args, **kwargs) -> str:
        """
        Returns the hexadecimal representation of the bytes.
        """
        return "0x" + super().hex(*args, **kwargs)

    @classmethod
    def or_none(cls, input: "Bytes | BytesConvertible | None") -> "Bytes | None":
        """
        Converts the input to a Bytes while accepting None.
        """
        if input is None:
            return input
        return cls(input)

    def keccak256(self) -> "Bytes":
        """
        Return the keccak256 hash of the opcode byte representation.
        """
        k = keccak.new(digest_bits=256)
        return Bytes(k.update(bytes(self)).digest())


S = TypeVar("S", bound="FixedSizeHexNumber")


class FixedSizeHexNumber(int, ToStringSchema):
    """
    A base class that helps represent an integer as a fixed byte-length
    hexadecimal number.

    This class is used to dynamically generate subclasses of a specific byte
    length.
    """

    byte_length: ClassVar[int]
    max_value: ClassVar[int]

    def __class_getitem__(cls, length: int) -> Type["FixedSizeHexNumber"]:
        """
        Creates a new FixedSizeHexNumber class with the given length.
        """

        class Sized(cls):  # type: ignore
            byte_length = length
            max_value = 2 ** (8 * length) - 1

        return Sized

    def __new__(cls, input: NumberConvertible | N):
        """
        Creates a new Number object.
        """
        i = to_number(input)
        if i > cls.max_value:
            raise ValueError(f"Value {i} is too large for {cls.byte_length} bytes")
        if i < 0:
            i += cls.max_value + 1
            if i <= 0:
                raise ValueError(f"Value {i} is too small for {cls.byte_length} bytes")
        return super(FixedSizeHexNumber, cls).__new__(cls, i)

    def __str__(self) -> str:
        """
        Returns the string representation of the number.
        """
        return self.hex()

    def hex(self) -> str:
        """
        Returns the hexadecimal representation of the number.
        """
        if self == 0:
            return "0x00"
        hex_str = hex(self)[2:]
        if len(hex_str) % 2 == 1:
            return "0x0" + hex_str
        return "0x" + hex_str


class HashInt(FixedSizeHexNumber[32]):  # type: ignore
    """
    Class that helps represent hashes in tests.
    """

    pass


T = TypeVar("T", bound="FixedSizeBytes")


class FixedSizeBytes(Bytes):
    """
    Class that helps represent bytes of fixed length in tests.
    """

    byte_length: ClassVar[int]

    def __class_getitem__(cls, length: int) -> Type["FixedSizeBytes"]:
        """
        Creates a new FixedSizeBytes class with the given length.
        """

        class Sized(cls):  # type: ignore
            byte_length = length

        return Sized

    def __new__(cls, input: FixedSizeBytesConvertible | T):
        """
        Creates a new FixedSizeBytes object.
        """
        if type(input) is cls:
            return input
        return super(FixedSizeBytes, cls).__new__(cls, to_fixed_size_bytes(input, cls.byte_length))

    def __hash__(self) -> int:
        """
        Returns the hash of the bytes.
        """
        return super(FixedSizeBytes, self).__hash__()

    @classmethod
    def or_none(cls: Type[T], input: T | FixedSizeBytesConvertible | None) -> T | None:
        """
        Converts the input to a Fixed Size Bytes while accepting None.
        """
        if input is None:
            return input
        return cls(input)

    def __eq__(self, other: object) -> bool:
        """
        Compares two FixedSizeBytes objects to be equal.
        """
        if not isinstance(other, FixedSizeBytes):
            assert (
                isinstance(other, str)
                or isinstance(other, int)
                or isinstance(other, bytes)
                or isinstance(other, SupportsBytes)
            )
            other = self.__class__(other)
        return super().__eq__(other)

    def __ne__(self, other: object) -> bool:
        """
        Compares two FixedSizeBytes objects to be not equal.
        """
        return not self.__eq__(other)


class Address(FixedSizeBytes[20]):  # type: ignore
    """
    Class that helps represent Ethereum addresses in tests.
    """

    label: str | None = None


class Hash(FixedSizeBytes[32]):  # type: ignore
    """
    Class that helps represent hashes in tests.
    """

    pass


class Bloom(FixedSizeBytes[256]):  # type: ignore
    """
    Class that helps represent blooms in tests.
    """

    pass


class HeaderNonce(FixedSizeBytes[8]):  # type: ignore
    """
    Class that helps represent the header nonce in tests.
    """

    pass


class BLSPublicKey(FixedSizeBytes[48]):  # type: ignore
    """
    Class that helps represent BLS public keys in tests.
    """

    pass


class BLSSignature(FixedSizeBytes[96]):  # type: ignore
    """
    Class that helps represent BLS signatures in tests.
    """

    pass
