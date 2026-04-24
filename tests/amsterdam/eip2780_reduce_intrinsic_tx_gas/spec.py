"""Reference spec for [EIP-2780: Reduce intrinsic transaction gas.](https://eips.ethereum.org/EIPS/eip-2780)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_2780 = ReferenceSpec(
    git_path="EIPS/eip-2780.md",
    version="5c092808affade87ad04086b8ce0c41cb8d2b5dd",
)
