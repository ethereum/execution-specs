"""
Defines EIP-6110 specification constants and functions.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """
    Defines the reference spec version and git path.
    """

    git_path: str
    version: str


ref_spec_6110 = ReferenceSpec("EIPS/eip-6110.md", "70a6ec21f62937caf665d98db2b41633e9287871")


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-6110 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-6110
    """

    DEPOSIT_CONTRACT_ADDRESS = 0x00000000219AB540356CBB839CBE05303D7705FA
