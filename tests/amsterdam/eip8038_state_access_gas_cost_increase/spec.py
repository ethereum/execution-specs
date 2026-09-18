"""Defines the EIP-8038 reference specification."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8038 = ReferenceSpec(
    "EIPS/eip-8038.md", "a3f1333eba8c0b950d36399a4648ebbd28c014ab"
)
