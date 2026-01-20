"""Defines EIP-7708 specification constants and functions."""

from dataclasses import dataclass

from execution_testing import Address, Hash, keccak256


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7708 = ReferenceSpec(
    "EIPS/eip-7708.md", "a7c5b2ff5697d5a0be5ea804a89d98a7fd0dce60"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7708 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7708.
    """

    SYSTEM_ADDRESS: Address = Address(
        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
    )
    TRANSFER_TOPIC: Hash = Hash(
        keccak256(b"Transfer(address,address,uint256)")
    )
    SELFDESTRUCT_TOPIC: Hash = Hash(
        keccak256(b"Selfdestruct(address,uint256)")
    )
