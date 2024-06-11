"""
Defines EIP-3651 specification constants and functions.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """
    Defines the reference spec version and git path.
    """

    git_path: str
    version: str


ref_spec_3651 = ReferenceSpec("EIPS/eip-3651.md", "d94c694c6f12291bb6626669c3e8587eef3adff1")
