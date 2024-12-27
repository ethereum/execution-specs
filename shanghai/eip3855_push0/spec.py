"""Defines EIP-3855 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_3855 = ReferenceSpec("EIPS/eip-3855.md", "42034250ae8dd4b21fdc6795773893c6f1e74d3a")
