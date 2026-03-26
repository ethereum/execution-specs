"""
Reference spec for EIP-7928: Block-level Access Lists.

https://eips.ethereum.org/EIPS/eip-7928
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7928 = ReferenceSpec(
    git_path="EIPS/eip-7928.md",
    version="aca88aa0932580c29d0233f902cb4390e88b8c41",
)
