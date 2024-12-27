"""Defines EIP-7623 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7623 = ReferenceSpec("EIPS/eip-7623.md", "9104d079c04737b1fec5f7150715f024d8028558")


# Constants
@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7623 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7623.
    """

    STANDARD_TOKEN_COST = 4
    TOTAL_COST_FLOOR_PER_TOKEN = 10
