"""Defines EIP-214 specification reference."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_214 = ReferenceSpec(
    git_path="EIPS/eip-214.md",
    version="009d0e1ce76b2c171c34bacdb2f13d606c9918b0",
)
