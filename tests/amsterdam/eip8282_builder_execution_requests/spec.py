"""
Reference spec and constants for [EIP-8282: Builder Execution Requests][8282].

[8282]: https://eips.ethereum.org/EIPS/eip-8282
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


# EIP-8282 is not yet merged into ethereum/EIPs (ethereum/EIPs#11760);
# pin the version once it lands.
ref_spec_8282 = ReferenceSpec(
    git_path="EIPS/eip-8282.md",
    version="0000000000000000000000000000000000000000",
)


class Spec:
    """Constants and parameters from EIP-8282."""

    BUILDER_DEPOSIT_CONTRACT_ADDRESS = (
        0x82FD414BCC3D584692B631FDFF9FADC1DFE4DDDD
    )
    BUILDER_EXIT_CONTRACT_ADDRESS = 0x82901077FE13BECC6F5B2E84CAE8072751ADEEEE

    BUILDER_DEPOSIT_REQUEST_TYPE = 0x03
    BUILDER_EXIT_REQUEST_TYPE = 0x04

    SYSTEM_ADDRESS = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
    SYSTEM_CALL_GAS_LIMIT = 30_000_000

    # Request-bus parameters.
    MAX_DEPOSIT_REQUESTS_PER_BLOCK = 64
    TARGET_DEPOSIT_REQUESTS_PER_BLOCK = 8
    MAX_EXIT_REQUESTS_PER_BLOCK = 16
    TARGET_EXIT_REQUESTS_PER_BLOCK = 2
    MIN_REQUEST_FEE = 1
    REQUEST_FEE_UPDATE_FRACTION = 17
    EXCESS_INHIBITOR = 2**256 - 1

    # Storage slot holding the excess deposit request count. Seeding it with
    # `EXCESS_INHIBITOR` disables the queue; the next system call resets it.
    EXCESS_DEPOSIT_REQUESTS_STORAGE_SLOT = 0

    # Minimum credited stake for a builder deposit, in wei (1 ETH).
    BUILDER_MIN_DEPOSIT = 1_000_000_000_000_000_000

    # Calldata input sizes accepted by each predeploy.
    DEPOSIT_REQUEST_INPUT_BYTES = 184
    EXIT_REQUEST_INPUT_BYTES = 48
