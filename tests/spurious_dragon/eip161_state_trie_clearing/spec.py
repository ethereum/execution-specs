"""Defines EIP-161 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_161 = ReferenceSpec(
    "EIPS/eip-161.md", "b746c239881f24996f0205855e44f9b2d3b92b6a"
)
