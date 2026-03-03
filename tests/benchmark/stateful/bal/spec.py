"""Reference spec for [EIP-7928: Block-level Access Lists.](https://eips.ethereum.org/EIPS/eip-7928)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Reference specification."""

    git_path: str
    version: str


ref_spec_7928 = ReferenceSpec(
    git_path="EIPS/eip-7928.md",
    version="e7f0963a024b3d0dedc4488a7553bf7c70dedb3e",
)


@dataclass(frozen=True)
class Spec:
    """Constants and parameters from EIP-7928."""

    # RLP encoding is used for block access list data structures
    BAL_ENCODING_FORMAT: str = "RLP"

    # Maximum limits for block access list data structures
    TARGET_MAX_GAS_LIMIT = 600_000_000
    MAX_TXS: int = 30_000
    MAX_SLOTS: int = 300_000
    MAX_ACCOUNTS: int = 300_000
    # TODO: Use this as a function of the current fork.
    MAX_CODE_SIZE: int = 24_576  # 24 KiB

    # Type size constants
    ADDRESS_SIZE: int = 20  # Ethereum address size in bytes
    STORAGE_KEY_SIZE: int = 32  # Storage slot key size in bytes
    STORAGE_VALUE_SIZE: int = 32  # Storage value size in bytes
    HASH_SIZE: int = 32  # Hash size in bytes

    # Numeric type limits
    MAX_TX_INDEX: int = 2**16 - 1  # uint16 max value
    MAX_BALANCE: int = 2**128 - 1  # uint128 max value
    MAX_NONCE: int = 2**64 - 1  # uint64 max value
