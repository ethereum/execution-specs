"""Defines EIP-155 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_155 = ReferenceSpec(
    "EIPS/eip-155.md", "17024fa653e75d93f895632e96b20766569cebbd"
)
