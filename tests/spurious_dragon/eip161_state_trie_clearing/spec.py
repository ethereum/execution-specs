"""Defines EIP-161 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_161 = ReferenceSpec(
    "EIPS/eip-161.md", "96523ef4d76ca440f73f0403ddb5c9cb3b24dcae"
)
