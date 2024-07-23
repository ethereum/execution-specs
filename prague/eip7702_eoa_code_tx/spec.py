"""
Defines EIP-7702 specification constants and functions.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """
    Defines the reference spec version and git path.
    """

    git_path: str
    version: str


ref_spec_7702 = ReferenceSpec("EIPS/eip-7702.md", "7357ff1f3f176aada6d350d6e42a292a3dec27f4")


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7702 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7702
    """

    SET_CODE_TX_TYPE = 0x04
    MAGIC = 0x05
    PER_AUTH_BASE_COST = 2500
