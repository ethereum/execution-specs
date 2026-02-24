"""Defines EIP-7976 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7976 = ReferenceSpec(
    "EIPS/eip-7976.md", "57af840f568c5743b5bdb4bff72ff29145efe8a5"
)


# Constants
@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7976 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7976.
    """

    STANDARD_TOKEN_COST = 4
    TOTAL_COST_FLOOR_PER_TOKEN = 16
