"""Reference spec for [EIP-8268](https://eips.ethereum.org/EIPS/eip-8268)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8268 = ReferenceSpec(
    git_path="EIPS/eip-8268.md",
    version="a6a301bd35a6268ee245e5e0e6011774d4e6fd0d",
)
