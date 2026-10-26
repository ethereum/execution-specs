"""
Reference spec for [EIP-8025: Optional Execution Proofs][8025].

[8025]: https://eips.ethereum.org/EIPS/eip-8025
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_8025 = ReferenceSpec(
    git_path="EIPS/eip-8025.md",
    version="6287bacd18648daa53c955f5d4674b045b364128",
)
