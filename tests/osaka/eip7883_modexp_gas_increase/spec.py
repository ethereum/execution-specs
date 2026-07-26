"""Defines EIP-7883 specification constants and functions."""

from dataclasses import dataclass
from typing import Type

from execution_testing import Fork

from ...byzantium.eip198_modexp_precompile.helpers import ModExpInput
from ...byzantium.eip198_modexp_precompile.spec import (
    ModExpGasSpec,
    Spec2565,
    ceiling_division,
    modexp_gas_spec,
)


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7883 = ReferenceSpec(
    "EIPS/eip-7883.md", "13aa65810336d4f243d4563a828d5afe36035d23"
)


class Spec(Spec2565):
    """
    Constants and helpers for the ModExp gas cost calculation, plus the
    arbitrary inputs shared by the tests.
    """

    # Arbitrary Test Constants
    modexp_input = ModExpInput(
        base="e8e77626586f73b955364c7b4bbf0bb7f7685ebd40e852b164633a4acbd3244c0001020304050607",
        exponent="01ffffff",
        modulus="f01681d2220bfea4bb888a5543db8c0916274ddb1ea93b144c042c01d8164c950001020304050607",
    )
    modexp_expected = bytes.fromhex(
        "1abce71dc2205cce4eb6934397a88136f94641342e283cbcd30e929e85605c6718ed67f475192ffd"
    )
    modexp_error = bytes()


@dataclass(frozen=True)
class Spec7883(Spec):
    """
    Constants and helpers for the ModExp gas cost increase EIP. These override
    the original Spec class variables for EIP-7883.
    """

    MODEXP_ADDRESS = 0x05
    MIN_GAS = 500

    LARGE_BASE_MODULUS_MULTIPLIER = 2
    EXPONENT_BYTE_MULTIPLIER = 16
    GAS_DIVISOR = 1  # Overrides the original Spec class GAS_DIVISOR

    @classmethod
    def calculate_multiplication_complexity(
        cls, base_length: int, modulus_length: int
    ) -> int:
        """
        Calculate the multiplication complexity of the ModExp precompile for
        EIP-7883.
        """
        max_length = max(base_length, modulus_length)
        words = ceiling_division(max_length, cls.WORD_SIZE)
        complexity = 16
        if max_length > cls.MAX_LENGTH_THRESHOLD:
            complexity = cls.LARGE_BASE_MODULUS_MULTIPLIER * words**2
        return complexity


def modexp_spec_at(fork: Fork) -> Type[ModExpGasSpec]:
    """Return the ModExp gas specification in effect at the given fork."""
    return Spec7883 if fork.is_eip_enabled(7883) else modexp_gas_spec(fork)
