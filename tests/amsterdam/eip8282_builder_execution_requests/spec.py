"""
Reference spec and constants for
[EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


# EIP-8282 is a Draft; its addresses, request-type bytes, and predeploy
# bytecode are placeholders pending the EIP's final, audit-frozen values.
ref_spec_8282 = ReferenceSpec(
    git_path="EIPS/eip-8282.md",
    version="0000000000000000000000000000000000000000",
)


@dataclass(frozen=True)
class Spec:
    """
    Constants and parameters from EIP-8282. Addresses and request-type bytes
    are placeholders pending the EIP's final allocation.
    """

    BUILDER_DEPOSIT_CONTRACT_ADDRESS = (
        0x0000000000000000000000000000000000007732
    )
    BUILDER_EXIT_CONTRACT_ADDRESS = 0x0000000000000000000000000000000000007733

    BUILDER_DEPOSIT_REQUEST_TYPE = 0x03
    BUILDER_EXIT_REQUEST_TYPE = 0x04

    SYSTEM_ADDRESS = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
    SYSTEM_CALL_GAS_LIMIT = 30_000_000

    # Shared request-bus parameters (identical to EIP-7002 / EIP-7251).
    MAX_DEPOSIT_REQUESTS_PER_BLOCK = 256
    TARGET_DEPOSIT_REQUESTS_PER_BLOCK = 32
    MAX_EXIT_REQUESTS_PER_BLOCK = 16
    TARGET_EXIT_REQUESTS_PER_BLOCK = 2
    MIN_REQUEST_FEE = 1
    REQUEST_FEE_UPDATE_FRACTION = 17
    EXCESS_INHIBITOR = 2**256 - 1

    # Minimum credited stake for a builder deposit, in wei (1 ETH).
    BUILDER_MIN_DEPOSIT = 1_000_000_000_000_000_000

    # Calldata input sizes accepted by each predeploy.
    DEPOSIT_REQUEST_INPUT_BYTES = 184
    EXIT_REQUEST_INPUT_BYTES = 48
