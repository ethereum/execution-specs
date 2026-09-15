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
    version="d2a64c2d4cc44f2f507577d0ebfb110dcc21d358",
)
