"""Defines EIP-4895 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_4895 = ReferenceSpec("EIPS/eip-4895.md", "81af3b60b632bc9c03513d1d137f25410e3f4d34")
