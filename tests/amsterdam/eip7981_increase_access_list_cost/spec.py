"""Defines EIP-7981 specification constants and functions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7981 = ReferenceSpec(
    "EIPS/eip-7981.md", "954963fb6315dffadd9c40d48e4dae313e20cff5"
)


# Constants
@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7981 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7981.
    """

    ACCESS_LIST_ADDRESS_COST = 2400
    ACCESS_LIST_STORAGE_KEY_COST = 1900
