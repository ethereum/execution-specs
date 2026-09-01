"""Defines EIP-8070 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8070 = ReferenceSpec(
    "EIPS/eip-8070.md", "43c7af020f1641924bed60565fde86f6ad3469df"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-8070 specification as defined at
    https://eips.ethereum.org/EIPS/eip-8070.
    """

    BLOB_COMMITMENT_VERSION_KZG = 1
    """Version byte of a KZG blob versioned hash (EIP-4844)."""

    CELLS_PER_EXT_BLOB = 128
    """Number of cells an extended blob is split into for `getBlobsV4`."""

    RECONSTRUCTION_THRESHOLD = 64
    """Number of cells required for Reed-Solomon reconstruction of a blob."""

    SAMPLES_PER_SLOT = 8
    """Minimum number of blob columns a node must custody."""

    CUSTODY_BITMAP_BYTES = 16
    """Byte length of the `custodyColumns` and cell mask bitmaps."""

    MIN_SUPPORTED_REQUEST_SIZE = 128
    """
    Minimum `getBlobsV4` request size (in versioned hashes) that clients
    must support, per the execution-apis `engine_getBlobsV4` definition.
    """
