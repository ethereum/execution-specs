"""Defines EIP-8250 specification constants and types."""

from dataclasses import dataclass

from execution_testing import Address


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8250 = ReferenceSpec(
    "EIPS/eip-8250.md", "e49b435eb2ddab14b15c56eea93f719d75886f38"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-8250 specification as defined at
    https://eips.ethereum.org/EIPS/eip-8250.
    """

    NONCE_MANAGER = Address(0x8250)
    NONCE_MANAGER_CODE = bytes.fromhex("60006000fd")
    KEYED_NONCE_FIRST_USE_STATE_GAS = 64 * 1530
    MAX_NONCE_SEQ = 2**64 - 1
    MAX_NONCE_KEYS = 16
    LEGACY_NONCE_KEYS = (0,)

    TXPARAM_NONCE_SEQ = 0x01
    TXPARAM_LEGACY_NONCE = 0x0D
    TXPARAM_NONCE_KEY_COUNT = 0x0E
    TXPARAM_NONCE_KEYS_HASH = 0x0F
    TXPARAM_NONCE_KEY_0 = 0x10
