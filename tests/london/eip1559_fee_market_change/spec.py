"""Defines EIP-1559 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_1559 = ReferenceSpec(
    "EIPS/eip-1559.md", "ba6c342c23164072adb500c3136e3ae6eabff306"
)
