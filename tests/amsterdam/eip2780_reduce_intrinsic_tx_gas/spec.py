"""Reference spec for [EIP-2780: Resource-based intrinsic transaction gas.](https://eips.ethereum.org/EIPS/eip-2780)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_2780 = ReferenceSpec(
    git_path="EIPS/eip-2780.md",
    version="4b612eec2ef70611bba3e0819d137dcfb9b6cd81",
)
