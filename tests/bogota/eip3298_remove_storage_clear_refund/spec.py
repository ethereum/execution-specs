"""Reference spec for [EIP-3298](https://eips.ethereum.org/EIPS/eip-3298)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_3298 = ReferenceSpec(
    git_path="EIPS/eip-3298.md",
    version="a618240aad9b098e079270045fcb1380d3e7992a",
)
