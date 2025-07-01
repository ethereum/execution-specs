"""Defines EIP-7594 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7594 = ReferenceSpec("EIPS/eip-7594.md", "45d03a84a8ad0160ed3fb03af52c49bd39e802ba")


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7594 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7594.
    """

    pass
