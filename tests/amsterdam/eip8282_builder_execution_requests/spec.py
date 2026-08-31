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


ref_spec_8282 = ReferenceSpec(
    git_path="EIPS/eip-8282.md",
    version="35ab20cb31a416c50600da00125d262e1756850c",
)


class Spec:
    """Constants and parameters from EIP-8282."""

    BUILDER_DEPOSIT_CONTRACT_ADDRESS = (
        0x0000BFF46984E3725691FA540A8C7589300D8282
    )
    BUILDER_EXIT_CONTRACT_ADDRESS = 0x000064D678505AD48F8CCB093BC65613800E8282

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

    # Storage layout shared by both predeploys (the EIP-7002 request-bus
    # pattern): queued records are stored as 32-byte words from the queue
    # offset onward. Seeding the excess slot with `EXCESS_INHIBITOR` disables
    # the queue; the next system call resets it.
    EXCESS_STORAGE_SLOT = 0
    COUNT_STORAGE_SLOT = 1
    QUEUE_HEAD_STORAGE_SLOT = 2
    QUEUE_TAIL_STORAGE_SLOT = 3
    QUEUE_STORAGE_OFFSET = 4
    # Slots each queued record occupies: the 184 deposit input bytes fill
    # six words; an exit's 20-byte source address and 48-byte pubkey fill
    # three.
    DEPOSIT_REQUEST_QUEUE_SLOTS_PER_REQUEST = 6
    EXIT_REQUEST_QUEUE_SLOTS_PER_REQUEST = 3

    # Minimum credited stake for a builder deposit, in wei (1 ETH).
    BUILDER_MIN_DEPOSIT = 1_000_000_000_000_000_000

    # Calldata input sizes accepted by each predeploy.
    DEPOSIT_REQUEST_INPUT_BYTES = 184
    EXIT_REQUEST_INPUT_BYTES = 48
