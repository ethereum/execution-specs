"""Defines EIP-7823 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7823 = ReferenceSpec("EIPS/eip-7823.md", "c8321494fdfbfda52ad46c3515a7ca5dc86b857c")
