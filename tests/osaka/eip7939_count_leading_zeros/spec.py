"""Defines EIP-7939 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7939 = ReferenceSpec("EIPS/eip-7939.md", "c8321494fdfbfda52ad46c3515a7ca5dc86b857c")


@dataclass(frozen=True)
class Spec:
    """Constants and helpers for the CLZ opcode."""

    CLZ = 0x1E
    CLZ_GAS_COST = 5

    @classmethod
    def calculate_clz(cls, value: int) -> int:
        """Calculate the count of leading zeros for a 256-bit value."""
        if value == 0:
            return 256
        return 256 - value.bit_length()
