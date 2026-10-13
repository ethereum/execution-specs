"""Defines EIP-8198 specification constants and functions."""

from dataclasses import dataclass

# Base the spec on EIP-4844 for the blob transaction constants
from ...cancun.eip4844_blobs.spec import Spec as EIP4844Spec


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8198 = ReferenceSpec(
    "EIPS/eip-8198.md", "e256c0d5ef51182f42488b5d1da2eb57228b8dd8"
)


class Spec(EIP4844Spec):
    """
    Parameters from the EIP-8198 specifications. Extends the EIP-4844 spec.

    The new base fee change and blob schedule are read from the fork, which
    carries them from the EIP-8198 fork class.
    """

    GAS_LIMIT_ADJUSTMENT_FACTOR = 1024
