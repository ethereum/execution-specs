"""Defines EIP-7251 specification constants and functions."""

from dataclasses import dataclass

from execution_testing import Address


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7251 = ReferenceSpec(
    "EIPS/eip-7251.md", "f29c0eda1e7495c071ef5b25fbd850dc3ef6bfdf"
)


# Constants
class Spec:
    """
    Parameters from the EIP-7251 specifications as defined at
    https://eips.ethereum.org/EIPS/eip-7251#execution-layer.

    The request queue parameters live on the framework's
    `ConsolidationRequest`.
    """

    CONSOLIDATION_REQUEST_PREDEPLOY_SENDER = Address(
        0x13D1913D623E6A9D8811736359E50FD31FE54FCA
    )
    SYSTEM_ADDRESS = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE

    SYSTEM_CALL_GAS_LIMIT = 30_000_000
    EXCESS_INHIBITOR = 1181
