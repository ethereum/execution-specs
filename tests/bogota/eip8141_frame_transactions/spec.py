"""Defines EIP-8141 specification constants and types."""

from dataclasses import dataclass

from execution_testing import (
    LEANSPHINCS_VERIFIER,
    P256_VERIFIER,
    SECP256K1_VERIFIER,
    Address,
    FrameFlag,
    FrameMode,
    FrameStatus,
    TransactionType,
)
from execution_testing.forks.forks.eips.bogota.eip_8141 import (
    EXPIRY_VERIFIER_ADDRESS,
)


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8141 = ReferenceSpec(
    "EIPS/eip-8141.md", "03a1e136bdcdb40e83c01ce5f81474769cae61be"
)


@dataclass(frozen=True)
class Spec:
    """
    Parameters from the EIP-8141 specification as defined at
    https://eips.ethereum.org/EIPS/eip-8141.
    """

    FRAME_TX_TYPE = TransactionType.FRAME
    ENTRY_POINT = Address(0xAA)
    EXPIRY_VERIFIER = Address(EXPIRY_VERIFIER_ADDRESS)
    EXPIRY_DATA_LENGTH = 8
    MAX_FRAMES = 64
    MAX_CLAIMS = 64
    MAX_CLAIM_WITNESS_BYTES = 1_048_576
    MAX_DEPENDENCY_PROOF_BYTES = 8_388_608
    DEPENDENCY_PROOF_VERSION_RAW = b"\x00"
    POOLED_WRAPPER_VERSION = 0

    # Claim-only protocol verifiers. The EIP leaves their addresses to be
    # assigned; these are placeholders.
    SECP256K1_VERIFIER = SECP256K1_VERIFIER
    P256_VERIFIER = P256_VERIFIER
    LEANSPHINCS_VERIFIER = LEANSPHINCS_VERIFIER
    SECP256K1_VERIFICATION_GAS = 2_800
    P256_VERIFICATION_GAS = 6_700
    LEANSPHINCS_VERIFICATION_GAS = 13_200
    SECP256K1_WITNESS_LENGTH = 65
    P256_WITNESS_LENGTH = 128
    LEANSPHINCS_SIGNATURE_SIZE = 7_740

    # Frame modes, flags and receipt statuses are the framework's enums,
    # named here as the EIP names them.
    MODE_DEFAULT = FrameMode.DEFAULT
    MODE_VERIFY = FrameMode.VERIFY
    MODE_SENDER = FrameMode.SENDER

    APPROVE_NONE = FrameFlag(0)
    APPROVE_PAYMENT = FrameFlag.APPROVE_PAYMENT
    APPROVE_EXECUTION = FrameFlag.APPROVE_EXECUTION
    APPROVE_EXECUTION_AND_PAYMENT = (
        FrameFlag.APPROVE_EXECUTION | FrameFlag.APPROVE_PAYMENT
    )
    ATOMIC_BATCH_FLAG = FrameFlag.ATOMIC_BATCH

    STATUS_FAILURE = FrameStatus.FAILURE
    STATUS_SUCCESS = FrameStatus.SUCCESS
    STATUS_SKIPPED = FrameStatus.SKIPPED

    # TXPARAM selectors
    TXPARAM_TYPE = 0x00
    TXPARAM_NONCE = 0x01
    TXPARAM_SENDER = 0x02
    TXPARAM_MAX_PRIORITY_FEE_PER_GAS = 0x03
    TXPARAM_MAX_FEE = 0x04
    TXPARAM_BLOB_COUNT = 0x07
    TXPARAM_SIG_HASH = 0x08
    TXPARAM_FRAME_COUNT = 0x09
    TXPARAM_CURRENT_FRAME_INDEX = 0x0A
    TXPARAM_STATE_GAS_LEFT = 0x0C

    # FRAMEPARAM selectors
    FRAMEPARAM_RESOLVED_TARGET = 0x00
    FRAMEPARAM_EXECUTION_GAS_LIMIT = 0x01
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

    # Public mempool
    MAX_VERIFY_GAS = 100_000
