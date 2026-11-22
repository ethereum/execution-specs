"""Defines EIP-7666 specification constants and types."""

from dataclasses import dataclass

from execution_testing import Address


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7666 = ReferenceSpec(
    "EIPS/eip-7666.md", "6b0b4a6d131d9a24ef90b455739dde0c46f524a3"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7666 specification as defined at
    https://eips.ethereum.org/EIPS/eip-7666.
    """

    IDENTITY_PRECOMPILE_ADDRESS = Address(0x04)
    EVM_CODE = bytes.fromhex("365f5f37365ff3")
    """`CALLDATASIZE PUSH0 PUSH0 CALLDATACOPY CALLDATASIZE PUSH0 RETURN`."""
