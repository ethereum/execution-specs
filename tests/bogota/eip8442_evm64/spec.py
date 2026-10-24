"""Reference spec for [EIP-8442: 64-bit Opcodes for the EVM](https://eips.ethereum.org/EIPS/eip-8442)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8442 = ReferenceSpec(
    git_path="EIPS/eip-8442.md",
    # To be set to the EIP file's commit hash once the EIP is merged.
    version="0000000000000000000000000000000000000000",
)


class Spec:
    """Constants and parameters from EIP-8442."""

    # Gas tiers, each a step below the tier of the twin.
    VERY_LOW_64: int = 2
    LOW_64: int = 3
    MID_64: int = 5
    EXP64_BASE: int = 5
    EXP64_PER_BYTE: int = 25

    # The unassigned values in the block 0xC0..0xDF.
    UNASSIGNED: tuple = (0xC0, 0xCF, 0xDA, 0xDF)
