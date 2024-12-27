"""Defines EIP-1014 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_1014 = ReferenceSpec("EIPS/eip-1014.md", "0a3c1015a07958523bb3ef48c2f230c9ba9605d9")


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-1014 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-1014.
    """
