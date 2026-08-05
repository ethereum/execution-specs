"""Defines the EIP-8038 reference specification."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8038 = ReferenceSpec(
    "EIPS/eip-8038.md", "fc2322854d047ba1fd6e3ae9e61fb7a915535cb7"
)
