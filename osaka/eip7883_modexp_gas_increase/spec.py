"""Defines EIP-7883 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7883 = ReferenceSpec("EIPS/eip-7883.md", "13aa65810336d4f243d4563a828d5afe36035d23")


def ceiling_division(a: int, b: int) -> int:
    """
    Calculate the ceil without using floating point.
    Used by many of the EVM's formulas.
    """
    return -(a // -b)


@dataclass(frozen=True)
class Spec:
    """Constants and helpers for the ModExp gas cost calculation."""

    MODEXP_ADDRESS = 0x05
    MIN_GAS = 200

    LARGE_BASE_MODULUS_MULTIPLIER = 1
    MAX_LENGTH_THRESHOLD = 32
    EXPONENT_BYTE_MULTIPLIER = 8

    WORD_SIZE = 8
    EXPONENT_THRESHOLD = 32
    GAS_DIVISOR = 3

    @classmethod
    def calculate_multiplication_complexity(cls, base_length: int, modulus_length: int) -> int:
        """Calculate the multiplication complexity of the ModExp precompile."""
        max_length = max(base_length, modulus_length)
        words = ceiling_division(max_length, cls.WORD_SIZE)
        if max_length <= cls.MAX_LENGTH_THRESHOLD:
            return words**2
        return cls.LARGE_BASE_MODULUS_MULTIPLIER * words**2

    @classmethod
    def calculate_iteration_count(cls, exponent_length: int, exponent: bytes) -> int:
        """Calculate the iteration count of the ModExp precompile."""
        iteration_count = 0
        exponent_value = int.from_bytes(exponent, byteorder="big")
        if exponent_length <= cls.EXPONENT_THRESHOLD and exponent_value == 0:
            iteration_count = 0
        elif exponent_length <= cls.EXPONENT_THRESHOLD:
            iteration_count = exponent_value.bit_length() - 1
        elif exponent_length > cls.EXPONENT_THRESHOLD:
            exponent_head = int.from_bytes(exponent[0:32], byteorder="big")
            length_part = cls.EXPONENT_BYTE_MULTIPLIER * (exponent_length - 32)
            bits_part = exponent_head.bit_length()
            if bits_part > 0:
                bits_part -= 1
            iteration_count = length_part + bits_part
        return max(iteration_count, 1)

    @classmethod
    def calculate_gas_cost(
        cls, base_length: int, modulus_length: int, exponent_length: int, exponent: bytes
    ) -> int:
        """Calculate the ModExp gas cost according to EIP-7883 specification."""
        multiplication_complexity = cls.calculate_multiplication_complexity(
            base_length, modulus_length
        )
        iteration_count = cls.calculate_iteration_count(exponent_length, exponent)
        return max(cls.MIN_GAS, (multiplication_complexity * iteration_count // cls.GAS_DIVISOR))


@dataclass(frozen=True)
class Spec7883(Spec):
    """Constants and helpers for the ModExp gas cost increase EIP."""

    MODEXP_ADDRESS = 0x05
    MIN_GAS = 500

    LARGE_BASE_MODULUS_MULTIPLIER = 2
    EXPONENT_BYTE_MULTIPLIER = 16
