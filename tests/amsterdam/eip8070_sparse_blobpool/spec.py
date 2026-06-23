"""Defines EIP-8070 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8070 = ReferenceSpec(
    "EIPS/eip-8070.md", "64d1b463e1c75884c995f81d8ffab40401acbcaa"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-8070 specification as defined at
    https://eips.ethereum.org/EIPS/eip-8070.
    """

    CELLS_PER_EXT_BLOB = 128
    """Number of cells an extended blob is split into for `getBlobsV4`."""

    RECONSTRUCTION_THRESHOLD = 64
    """Number of cells required for Reed-Solomon reconstruction of a blob."""
