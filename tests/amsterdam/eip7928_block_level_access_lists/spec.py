"""Reference spec for [EIP-7928: Block-level Access Lists.](https://eips.ethereum.org/EIPS/eip-7928)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7928 = ReferenceSpec(
    git_path="EIPS/eip-7928.md",
    version="d6f0b763bcb92d19ea342d3e09550853c741246e",
)


class Spec:
    """Constants from EIP-7928."""
