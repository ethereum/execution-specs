"""Reference spec for [EIP-3298](https://eips.ethereum.org/EIPS/eip-3298)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_3298 = ReferenceSpec(
    git_path="EIPS/eip-3298.md",
    version="19be2a355694d7f2a206ea61550d40170b1929e0",
)
