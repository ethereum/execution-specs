"""Reference spec for [EIP-7954: Increase Maximum Contract Size](https://eips.ethereum.org/EIPS/eip-7954)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7954 = ReferenceSpec(
    git_path="EIPS/eip-7954.md",
    version="83509e66344741895858ad756f9e3d290e5a88f4",
)
