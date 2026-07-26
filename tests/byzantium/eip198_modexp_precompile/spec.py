"""Defines the ModExp precompile gas cost specifications up to EIP-2565."""

from typing import Type

from execution_testing import Fork
from execution_testing.forks import Berlin

from .helpers import ModExpInput


def ceiling_division(a: int, b: int) -> int:
    """
    Calculate the ceil without using floating point. Used by many of the EVM's
    formulas.
    """
    return -(a // -b)


class ModExpGasSpec:
    """
    Base for the ModExp precompile gas cost calculations. Subclasses define
    the pricing introduced by a single EIP.
    """

    MODEXP_ADDRESS = 0x05
    MIN_GAS = 0

    EXPONENT_THRESHOLD = 32
    EXPONENT_BYTE_MULTIPLIER = 8
    GAS_DIVISOR = 1

    @classmethod
    def calculate_multiplication_complexity(
        cls, base_length: int, modulus_length: int
    ) -> int:
        """Calculate the multiplication complexity of the ModExp precompile."""
        raise NotImplementedError

    @classmethod
    def calculate_iteration_count(cls, modexp_input: ModExpInput) -> int:
        """
        Calculate the iteration count of the ModExp precompile. This handles
        length mismatch cases by using declared lengths from the raw input and
        only the first 32 bytes of exponent data for iteration calculation.
        """
        _, exponent_length, _ = modexp_input.get_declared_lengths()
        exponent_head = modexp_input.get_exponent_head()
        head_bits = max(exponent_head.bit_length() - 1, 0)
        if exponent_length <= cls.EXPONENT_THRESHOLD:
            iteration_count = head_bits
        else:
            iteration_count = (
                cls.EXPONENT_BYTE_MULTIPLIER
                * (exponent_length - cls.EXPONENT_THRESHOLD)
                + head_bits
            )
        return max(iteration_count, 1)

    @classmethod
    def calculate_gas_cost(cls, modexp_input: ModExpInput) -> int:
        """Calculate the ModExp gas cost."""
        base_length, _, modulus_length = modexp_input.get_declared_lengths()
        multiplication_complexity = cls.calculate_multiplication_complexity(
            base_length, modulus_length
        )
        iteration_count = cls.calculate_iteration_count(modexp_input)
        return max(
            cls.MIN_GAS,
            (multiplication_complexity * iteration_count // cls.GAS_DIVISOR),
        )


class Spec198(ModExpGasSpec):
    """
    Constants and helpers for the ModExp gas cost calculation as introduced by
    EIP-198, in effect from Byzantium until EIP-2565 takes over in Berlin.
    There is no minimum charge, so a call over empty operands is free.
    """

    GAS_DIVISOR = 20

    QUADRATIC_LENGTH_THRESHOLD = 64
    LINEAR_LENGTH_THRESHOLD = 1024

    @classmethod
    def calculate_multiplication_complexity(
        cls, base_length: int, modulus_length: int
    ) -> int:
        """
        Calculate the multiplication complexity of the ModExp precompile for
        EIP-198, which is piecewise in the length of the longer operand.
        """
        max_length = max(base_length, modulus_length)
        if max_length <= cls.QUADRATIC_LENGTH_THRESHOLD:
            return max_length**2
        if max_length <= cls.LINEAR_LENGTH_THRESHOLD:
            return max_length**2 // 4 + 96 * max_length - 3072
        return max_length**2 // 16 + 480 * max_length - 199680


class Spec2565(ModExpGasSpec):
    """
    Constants and helpers for the ModExp gas cost calculation as introduced by
    EIP-2565, in effect from Berlin.
    """

    MIN_GAS = 200

    LARGE_BASE_MODULUS_MULTIPLIER = 1
    MAX_LENGTH_THRESHOLD = 32
    MAX_LENGTH_BYTES = 1024

    WORD_SIZE = 8
    GAS_DIVISOR = 3

    @classmethod
    def calculate_multiplication_complexity(
        cls, base_length: int, modulus_length: int
    ) -> int:
        """Calculate the multiplication complexity of the ModExp precompile."""
        max_length = max(base_length, modulus_length)
        words = ceiling_division(max_length, cls.WORD_SIZE)
        if max_length <= cls.MAX_LENGTH_THRESHOLD:
            return words**2
        return cls.LARGE_BASE_MODULUS_MULTIPLIER * words**2


def modexp_gas_spec(fork: Fork) -> Type[ModExpGasSpec]:
    """Return the ModExp gas specification in effect at the given fork."""
    return Spec2565 if fork >= Berlin else Spec198
