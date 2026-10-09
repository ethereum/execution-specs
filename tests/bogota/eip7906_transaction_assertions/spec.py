"""Defines EIP-7906 specification constants and types."""

from dataclasses import dataclass

from execution_testing import keccak256


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_7906 = ReferenceSpec(
    "EIPS/eip-7906.md", "7f5c2854ba1f1898e443e6d90fcf418aeb133fcc"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-7906 specification as defined at
    https://eips.ethereum.org/EIPS/eip-7906.
    """

    MODE_POST_TX = 3
    """The `POST_TX` frame mode value."""

    TXTRACE_OPCODE = 0xB6
    TXDIFF_OPCODE = 0xB7
    EVENTDATACOPY_OPCODE = 0xB8

    # `TXTRACE` parameters.
    TXTRACE_BALANCES_CHANGED = 0x00
    TXTRACE_SLOTS_CHANGED = 0x01
    TXTRACE_CONTRACTS_DEPLOYED = 0x02
    TXTRACE_BALANCE_ADDRESS = 0x03
    TXTRACE_BALANCE_BEFORE = 0x04
    TXTRACE_BALANCE_AFTER = 0x05
    TXTRACE_SLOT_ADDRESS = 0x06
    TXTRACE_SLOT_KEY = 0x07
    TXTRACE_SLOT_BEFORE = 0x08
    TXTRACE_SLOT_AFTER = 0x09
    TXTRACE_DEPLOYED_ADDRESS = 0x0A
    TXTRACE_DEPLOYED_CODEHASH = 0x0B
    TXTRACE_EVENTS_COUNT = 0x0C
    TXTRACE_EVENT_ADDRESS = 0x0D
    TXTRACE_EVENT_TOPIC_COUNT = 0x0E
    TXTRACE_EVENT_TOPIC0 = 0x0F
    TXTRACE_EVENT_TOPIC1 = 0x10
    TXTRACE_EVENT_TOPIC2 = 0x11
    TXTRACE_EVENT_TOPIC3 = 0x12
    TXTRACE_EVENT_DATA_LEN = 0x13
    TXTRACE_GAS_PRE_CHARGE = 0x14
    TXTRACE_GAS_PAYER = 0x15
    TXTRACE_UNDEFINED = 0x16
    """The first `TXTRACE` parameter the EIP does not define."""

    # `TXDIFF` parameters.
    TXDIFF_SLOT_BEFORE = 0x00
    TXDIFF_SLOT_AFTER = 0x01
    TXDIFF_BALANCE_BEFORE = 0x02
    TXDIFF_BALANCE_AFTER = 0x03
    TXDIFF_CODEHASH_BEFORE = 0x04
    TXDIFF_CODEHASH_AFTER = 0x05
    TXDIFF_ADDRESS_SLOTS_COUNT = 0x06
    TXDIFF_ADDRESS_SLOT_INDEX = 0x07
    TXDIFF_ADDRESS_EVENTS_COUNT = 0x08
    TXDIFF_ADDRESS_EVENT_INDEX = 0x09
    TXDIFF_ACCOUNT_CHANGE_FLAGS = 0x0A
    TXDIFF_TOPIC_EVENTS_COUNT = 0x0B
    TXDIFF_TOPIC_EVENT_INDEX = 0x0C
    TXDIFF_UNDEFINED = 0x0D
    """The first `TXDIFF` parameter the EIP does not define."""

    # `account_change_flags` bits, in account tuple field order.
    CHANGE_FLAG_NONCE = 0b0001
    CHANGE_FLAG_BALANCE = 0b0010
    CHANGE_FLAG_STORAGE = 0b0100
    CHANGE_FLAG_CODE = 0b1000

    EMPTY_CODE_HASH = int.from_bytes(keccak256(b""), "big")
    """Code hash `TXDIFF` reports for an account without code."""
