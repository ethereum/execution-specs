"""Reference spec for [EIP-8163: Reserve EXTENSION (0xae) opcode](https://eips.ethereum.org/EIPS/eip-8163)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8163 = ReferenceSpec(
    git_path="EIPS/eip-8163.md",
    version="aef32ae28e42ba3a391ed8d991ddf6a68d53c152",
)
