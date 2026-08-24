"""Defines EIP-8368 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8368 = ReferenceSpec(
    "EIPS/eip-8368.md", "582684e2d7d372c09f45777be8ea603e485e9e9d"
)


class Spec:
    """
    Constants for the EIP-8368 CPSB recalibration tests.

    The EIP leaves the new reference block gas limit and the
    recalibrated CPSB TBD. These tests apply the EIP-8037 derivation
    at a provisional 300M reference, twice the original 150M.
    """

    # EIP-8037 derivation inputs with the recalibrated reference.
    REFERENCE_BLOCK_GAS_LIMIT = 300_000_000
    TARGET_STATE_GROWTH_BYTES = 120 * 2**30  # 120 GiB per year
    BLOCKS_PER_YEAR = (86_400 // 12) * 365

    # On average half of each block's gas budget can be consumed by
    # state gas before the base fee pushes back.
    TOTAL_STATE_GAS_PER_YEAR = (
        REFERENCE_BLOCK_GAS_LIMIT // 2
    ) * BLOCKS_PER_YEAR

    # Ceiling division. Rounding up reproduces the published EIP-8037
    # value (1530) at the original 150M reference.
    COST_PER_STATE_BYTE = (
        TOTAL_STATE_GAS_PER_YEAR + TARGET_STATE_GROWTH_BYTES - 1
    ) // TARGET_STATE_GROWTH_BYTES

    # EIP-8037 byte footprints, unchanged by this EIP.
    STATE_BYTES_PER_NEW_ACCOUNT = 120
    STATE_BYTES_PER_STORAGE_SET = 64
