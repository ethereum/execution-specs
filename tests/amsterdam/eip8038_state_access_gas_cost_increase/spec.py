"""Defines the EIP-8038 reference specification."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8038 = ReferenceSpec(
    "EIPS/eip-8038.md", "f83531466a3862853424a81d000727b3043ef2cc"
)
