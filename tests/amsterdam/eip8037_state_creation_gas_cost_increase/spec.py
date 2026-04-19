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


# TODO: update version once
# https://github.com/ethereum/EIPs/pull/11328 is merged
ref_spec_8037 = ReferenceSpec(
    "EIPS/eip-8037.md", "a12902ae1b811c45a81b51bfce671cf7a1fb27f3"
)


@dataclass(frozen=True)
class Spec:
    """
    Constants and helpers for the EIP-8037 State Creation Gas Cost
    Increase tests.
    """

    # EIP-7825 transaction gas limit cap
    TX_MAX_GAS_LIMIT = 2**24  # 16,777,216

    # TODO: replace with dynamic cost_per_state_byte(gas_limit) once
    # non-default block gas limits are supported in the test framework.
    COST_PER_STATE_BYTE = 1174  # at 100M–120M gas limit

    # State bytes per operation
    STATE_BYTES_PER_NEW_ACCOUNT = 112
    STATE_BYTES_PER_STORAGE_SET = 32
    STATE_BYTES_PER_AUTH_BASE = 23

    # Regular gas constants (EIP-8037 replaces old combined costs)
    REGULAR_GAS_CREATE = 9000
    PER_AUTH_BASE_COST = 7500
    GAS_COLD_STORAGE_WRITE = 5000

    # EIP-8037 state gas pricing parameters
    TARGET_STATE_GROWTH_PER_YEAR = 100 * 1024**3
    BLOCKS_PER_YEAR = 2_628_000
    COST_PER_STATE_BYTE_SIGNIFICANT_BITS = 5
    COST_PER_STATE_BYTE_OFFSET = 9578

    @staticmethod
    def cost_per_state_byte(gas_limit: int) -> int:
        """Calculate the dynamic state gas cost per byte."""
        numerator = gas_limit * Spec.BLOCKS_PER_YEAR
        denominator = 2 * Spec.TARGET_STATE_GROWTH_PER_YEAR
        raw = (numerator + denominator - 1) // denominator
        shifted = raw + Spec.COST_PER_STATE_BYTE_OFFSET
        shift = max(
            shifted.bit_length() - Spec.COST_PER_STATE_BYTE_SIGNIFICANT_BITS,
            0,
        )
        quantized = (shifted >> shift) << shift
        if quantized > Spec.COST_PER_STATE_BYTE_OFFSET:
            return quantized - Spec.COST_PER_STATE_BYTE_OFFSET
        return 1
