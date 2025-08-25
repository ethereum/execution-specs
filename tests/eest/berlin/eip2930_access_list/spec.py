"""Defines EIP-2930 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_2930 = ReferenceSpec("EIPS/eip-2930.md", "c9db53a936c5c9cbe2db32ba0d1b86c4c6e73534")


# Constants
@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-2930 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-2930#specification.
    """

    ACCESS_LIST_ADDRESS_COST = 2400
    ACCESS_LIST_STORAGE_KEY_COST = 1900

    """From EIP-2028"""
    TX_BASE_INTRINSIC_GAS = 21_000
    TX_DATA_ZERO_BYTE_GAS = 4
    TX_DATA_NON_ZERO_BYTE_GAS = 16
