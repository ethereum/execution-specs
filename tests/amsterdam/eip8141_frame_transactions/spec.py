"""Defines EIP-8141 specification constants and types."""

from dataclasses import dataclass

from execution_testing import Address


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8141 = ReferenceSpec(
    "EIPS/eip-8141.md", "9c915ee494c05069945f4e1018fa0854e2d3fb38"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-8141 specification as defined at
    https://eips.ethereum.org/EIPS/eip-8141.
    """

    FRAME_TX_TYPE = 0x06
    FRAME_TX_INTRINSIC_COST = 12_000
    FRAME_TX_PER_FRAME_COST = 475
    ENTRY_POINT = Address(0xAA)
    EXPIRY_VERIFIER = Address(0x8141)
    EXPIRY_VERIFIER_CODE = bytes.fromhex(
        "60083614600a575f5ffd5b5f3560c01c4211601657005b5f5ffd"
    )
    EXPIRY_DATA_LENGTH = 8
    MAX_FRAMES = 64

    # Frame modes
    MODE_DEFAULT = 0
    MODE_VERIFY = 1
    MODE_SENDER = 2

    # Frame flags
    APPROVE_NONE = 0x0
    APPROVE_PAYMENT = 0x1
    APPROVE_EXECUTION = 0x2
    APPROVE_EXECUTION_AND_PAYMENT = 0x3
    ATOMIC_BATCH_FLAG = 0x4

    # Signature schemes
    SCHEME_ARBITRARY = 0x0
    SCHEME_SECP256K1 = 0x1
    SCHEME_P256 = 0x2

    # Frame receipt statuses
    STATUS_FAILURE = 0
    STATUS_SUCCESS = 1
    STATUS_SKIPPED = 2

    # TXPARAM selectors
    TXPARAM_TYPE = 0x00
    TXPARAM_NONCE = 0x01
    TXPARAM_SENDER = 0x02
    TXPARAM_MAX_PRIORITY_FEE = 0x03
    TXPARAM_MAX_FEE = 0x04
    TXPARAM_MAX_BLOB_FEE = 0x05
    TXPARAM_MAX_COST = 0x06
    TXPARAM_BLOB_COUNT = 0x07
    TXPARAM_SIG_HASH = 0x08
    TXPARAM_FRAME_COUNT = 0x09
    TXPARAM_FRAME_INDEX = 0x0A
    TXPARAM_SIGNATURE_COUNT = 0x0B
    TXPARAM_STATE_GAS_LEFT = 0x0C

    # FRAMEPARAM selectors
    FRAMEPARAM_TARGET = 0x00
    FRAMEPARAM_GAS_LIMIT = 0x01
    FRAMEPARAM_MODE = 0x02
    FRAMEPARAM_FLAGS = 0x03
    FRAMEPARAM_DATA_LENGTH = 0x04
    FRAMEPARAM_STATUS = 0x05
    FRAMEPARAM_ALLOWED_SCOPE = 0x06
    FRAMEPARAM_ATOMIC_BATCH = 0x07
    FRAMEPARAM_VALUE = 0x08
    FRAMEPARAM_STATE_GAS_LIMIT = 0x09
    FRAMEPARAM_EXECUTION_GAS_USED = 0x0A
    FRAMEPARAM_STATE_GAS_USED = 0x0B

    # SIGPARAM selectors
    SIGPARAM_RESOLVED_SIGNER = 0x00
    SIGPARAM_SCHEME = 0x01
    SIGPARAM_MSG = 0x02
    SIGPARAM_SIGNATURE_LENGTH = 0x03
    SIGPARAM_COPY = 0x04
