"""Defines the EIP-8038 reference specification."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8038 = ReferenceSpec(
    "EIPS/eip-8038.md", "1bbccfb3b9dd06d3b5668792eb8185d309b6e407"
)
