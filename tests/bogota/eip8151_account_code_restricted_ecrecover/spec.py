"""Defines EIP-8151 specification constants."""

from dataclasses import dataclass

from execution_testing import Address


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8151 = ReferenceSpec(
    "EIPS/eip-8151.md", "18a19423634c07c8cc10308da9dcee966ff2e3c3"
)


class Spec:
    """
    Parameters from the EIP-8151 specifications.

    The gas is read from the fork.
    """

    ECRECOVER = Address(0x01)
    DELEGATION_MARKER = bytes.fromhex("ef0100")
    DELEGATED_CODE_LENGTH = 23
