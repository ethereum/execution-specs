"""Reference spec for [EIP-7843: SLOTNUM](https://eips.ethereum.org/EIPS/eip-7843)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7843 = ReferenceSpec(
    git_path="EIPS/eip-7843.md",
    version="6bc5d6b7acbc016a79fa573f98975093b5c2ca52",
)


@dataclass(frozen=True)
class Spec:
    """Constants and parameters from EIP-7843."""
