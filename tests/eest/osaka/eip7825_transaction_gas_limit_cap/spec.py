"""Defines EIP-7825 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


# EIP-7825 reference specification
ref_spec_7825 = ReferenceSpec("EIPS/eip-7825.md", "47cbfed315988c0bd4d10002c110ae402504cd94")


@dataclass(frozen=True)
class Spec:
    """Constants and helpers for the EIP-7825 Transaction Gas Limit Cap tests."""

    # Gas limit constants
    tx_gas_limit_cap = 2**24  # 16,777,216

    # Blob transaction constants
    blob_commitment_version_kzg = 1
