"""Defines EIP-7906 specification constants and types."""

from dataclasses import dataclass

from execution_testing import keccak256


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7906 = ReferenceSpec(
    "EIPS/eip-7906.md", "57b71a63125088fe6927a6346be4225b98d84ced"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7906 specification as defined at
    https://eips.ethereum.org/EIPS/eip-7906.
    """

    MODE_ASSERT = 3
    """The `ASSERT` frame mode value."""

    TXTRACE_OPCODE = 0xB6
    EVENTDATACOPY_OPCODE = 0xB7
    UNDEFINED_OPCODE = 0xB8
    """The opcode `EVENTDATACOPY` held before it moved to `0xB7`."""

    # `TXTRACE` parameters.
    TXTRACE_BALANCES_CHANGED = 0x00
    TXTRACE_SLOTS_CHANGED = 0x01
    TXTRACE_CODES_CHANGED = 0x02
    TXTRACE_NONCES_CHANGED = 0x03
    TXTRACE_BALANCE_ADDRESS = 0x04
    TXTRACE_BALANCE_BEFORE = 0x05
    TXTRACE_BALANCE_AFTER = 0x06
    TXTRACE_SLOT_ADDRESS = 0x07
    TXTRACE_SLOT_BEFORE = 0x08
    TXTRACE_SLOT_AFTER = 0x09
    TXTRACE_SLOT_KEY = 0x0A
    TXTRACE_CODE_ADDRESS = 0x0B
    TXTRACE_CODE_BEFORE = 0x0C
    TXTRACE_CODE_AFTER = 0x0D
    TXTRACE_NONCE_ADDRESS = 0x0E
    TXTRACE_NONCE_BEFORE = 0x0F
    TXTRACE_NONCE_AFTER = 0x10
    TXTRACE_EVENTS_COUNT = 0x11
    TXTRACE_EVENT_ADDRESS = 0x12
    TXTRACE_EVENT_TOPIC_COUNT = 0x13
    TXTRACE_EVENT_TOPIC0 = 0x14
    TXTRACE_EVENT_TOPIC1 = 0x15
    TXTRACE_EVENT_TOPIC2 = 0x16
    TXTRACE_EVENT_TOPIC3 = 0x17
    TXTRACE_EVENT_DATA_LEN = 0x18
    TXTRACE_GAS_PRE_CHARGE = 0x19
    TXTRACE_GAS_PAYER = 0x1A
    TXTRACE_UNDEFINED = 0x1B
    """The first `TXTRACE` parameter the EIP does not define."""

    EMPTY_CODE_HASH = int.from_bytes(keccak256(b""), "big")
    """Code hash `TXTRACE` reports for an account without code."""
