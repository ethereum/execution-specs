"""
Defines EIP-1153 specification constants and functions.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """
    Defines the reference spec version and git path.
    """

    git_path: str
    version: str


ref_spec_1153 = ReferenceSpec("EIPS/eip-1153.md", "6f0be621c76a05a7b3aaf0e9297afd425c26e9d0")


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-1153 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-1153
    """

    TLOAD_OPCODE_BYTE = 0x5C
    TSTORE_OPCODE_BYTE = 0x5D
    TLOAD_GAS_COST = 100
    TSTORE_GAS_COST = 100
