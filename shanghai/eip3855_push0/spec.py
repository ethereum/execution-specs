"""Defines EIP-3855 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_3855 = ReferenceSpec("EIPS/eip-3855.md", "6f85bd73336de4aacfad7ac3bb3a7e1ba2d68f51")
