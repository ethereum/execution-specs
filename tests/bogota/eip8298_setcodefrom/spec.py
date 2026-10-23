"""Reference spec for [EIP-8298: SETCODEFROM Code Reuse Instruction](https://eips.ethereum.org/EIPS/eip-8298)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8298 = ReferenceSpec(
    git_path="EIPS/eip-8298.md",
    version="94f01555581bef0588f71aa8520b6c289c468890",
)
