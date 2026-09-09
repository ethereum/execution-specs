"""Defines EIP-8037 specification constants and functions."""

from dataclasses import dataclass

from execution_testing.vm import Bytecode, Op


def init_code_at_high_bytes(
    init_code: Op | Bytecode | bytes,
) -> tuple[int, int]:
    """Return (mstore_value, size) to place init_code at memory[0:size]."""
    code_bytes = bytes(init_code)
    size = len(code_bytes)
    return int.from_bytes(code_bytes, "big") << (256 - 8 * size), size


@dataclass(frozen=True)
class ReferenceSpec:
    """Defines the reference spec version and git path."""

    git_path: str
    version: str


ref_spec_8037 = ReferenceSpec(
    "EIPS/eip-8037.md", "052029f3625328d6f51dec8e62a7090201e66f17"
)


class Spec:
    """
    Constants and helpers for the EIP-8037 State Creation Gas Cost
    Increase tests.
    """

    # EIP-7825 transaction gas limit cap
    TX_MAX_GAS_LIMIT = 2**24  # 16,777,216

    # CPSB is a fixed parameter derived from a 150M reference block
    # gas limit and a 120 GiB/year target state growth.
    COST_PER_STATE_BYTE = 1530

    # State bytes per operation
    STATE_BYTES_PER_NEW_ACCOUNT = 120
    STATE_BYTES_PER_STORAGE_SET = 64
    STATE_BYTES_PER_AUTH_BASE = 23

    # Execution gas constants. EIP-8037 separated state from execution gas;
    # EIP-8038 then repriced them.
    EXECUTION_GAS_CREATE = 12000
    # Total execution intrinsic per EIP-7702 authorization:
    # ACCOUNT_WRITE + EXECUTION_PER_AUTH_BASE_COST.
    PER_AUTH_BASE_COST = 16816
    GAS_COLD_STORAGE_WRITE = 12100
