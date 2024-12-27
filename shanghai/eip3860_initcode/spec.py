"""Defines EIP-3860 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_3860 = ReferenceSpec("EIPS/eip-3860.md", "5f8151e19ad1c99da4bafd514ce0e8ab89783c8f")


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-3860 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-3860#parameters.
    """

    MAX_INITCODE_SIZE = 49152
    INITCODE_WORD_COST = 2
