"""
Marginal cost estimation tests for EVM precompiles.

This module implements the "marginal approach" for gas cost estimation of precompiles.
Precompiles require a different approach than opcodes since they are called via
CALL/STATICCALL rather than being executed directly.

Program layout for precompile marginal measurement:
    | Setup memory with precompile input |
    | STATICCALL to NOOP address (0xFFFF) × (max_op_count - op_count) |
    | STATICCALL to precompile × op_count |
    | SSTORE success marker |
    | STOP |

The "noop" STATICCALLs ensure the TOTAL number of STATICCALL instructions remains
constant regardless of op_count. This eliminates STATICCALL overhead from the
measurement, so we only measure the pure precompile computation cost.

This approach is based on the gas-cost-estimator project's methodology.
"""

from dataclasses import dataclass
from typing import List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    Op,
    StateTestFiller,
    Transaction,
)

# Import BLS12-381 types from the EIP-2537 test spec
from tests.prague.eip2537_bls_12_381_precompiles.spec import (
    FP,
    FP2,
    PointG1,
    PointG2,
    Scalar,
    Spec as BLS12Spec,
)

# Success marker written to storage if execution completes without revert
SUCCESS_MARKER = 0xDEAD
SUCCESS_SLOT = 0

# Precompile addresses
ECRECOVER_ADDRESS = Address(0x01)
SHA256_ADDRESS = Address(0x02)
RIPEMD160_ADDRESS = Address(0x03)
IDENTITY_ADDRESS = Address(0x04)
MODEXP_ADDRESS = Address(0x05)
BN128_ADD_ADDRESS = Address(0x06)
BN128_MUL_ADDRESS = Address(0x07)
BN128_PAIRING_ADDRESS = Address(0x08)
BLAKE2F_ADDRESS = Address(0x09)
POINT_EVALUATION_ADDRESS = Address(0x0A)

# BLS12-381 precompile addresses (EIP-2537, Prague)
BLS12_G1ADD_ADDRESS = Address(0x0B)
BLS12_G1MSM_ADDRESS = Address(0x0C)
BLS12_G2ADD_ADDRESS = Address(0x0D)
BLS12_G2MSM_ADDRESS = Address(0x0E)
BLS12_PAIRING_ADDRESS = Address(0x0F)
BLS12_MAP_FP_TO_G1_ADDRESS = Address(0x10)
BLS12_MAP_FP2_TO_G2_ADDRESS = Address(0x11)


@dataclass
class MarginalPrecompileConfig:
    """Configuration for a marginal precompile test."""

    name: str
    """Name of the precompile for test identification."""

    address: Address
    """Address of the precompile."""

    max_op_count: int
    """Maximum number of precompile calls."""

    step: int
    """Step size for op_count increments."""

    input_data: bytes
    """Input data for the precompile call."""

    input_size: int
    """Size of input data in memory."""


def create_ecrecover_input(
    msg_hash: bytes,
    v: int,
    r: bytes,
    s: bytes,
) -> bytes:
    """
    Create ECRECOVER precompile input.
    
    Input format: hash (32 bytes) | v (32 bytes) | r (32 bytes) | s (32 bytes) = 128 bytes
    """
    return (
        msg_hash
        + v.to_bytes(32, "big")
        + r
        + s
    )


def create_modexp_input(
    base: bytes,
    exponent: bytes,
    modulus: bytes,
) -> bytes:
    """
    Create MODEXP precompile input.
    
    Input format:
        base_length (32 bytes) | exponent_length (32 bytes) | modulus_length (32 bytes)
        | base (base_length bytes) | exponent (exponent_length bytes) | modulus (modulus_length bytes)
    """
    return (
        len(base).to_bytes(32, "big")
        + len(exponent).to_bytes(32, "big")
        + len(modulus).to_bytes(32, "big")
        + base
        + exponent
        + modulus
    )


# Valid ECRECOVER input that performs full signature recovery (worst case)
# This is a valid signature that will actually recover an address
# Taken from gas-cost-estimator's ECRECOVER test case
ECRECOVER_INPUT = create_ecrecover_input(
    msg_hash=bytes.fromhex("456e9aea5e197a1f1af7a3e85a3212fa4049a3ba34c2289b4c860fc0b0c64ef3"),
    v=28,  # 0x1c
    r=bytes.fromhex("9242685bf161793cc25603c231bc2f568eb630ea16aa137d2664ac8038825608"),
    s=bytes.fromhex("4f8ae3bd7535248d0bd448298cc2e2071e56992d0774dc340c368ae950852ada"),
)

ECRECOVER_CONFIG = MarginalPrecompileConfig(
    name="ECRECOVER",
    address=ECRECOVER_ADDRESS,
    max_op_count=200,  # Increased for ~1M gas (3000 gas/call)
    step=50,  # ~5 data points
    input_data=ECRECOVER_INPUT,
    input_size=len(ECRECOVER_INPUT),  # 128 bytes
)

# MODEXP true worst-case input: 256-byte (2048-bit) inputs
# B = 2^2048 - 1 (all 0xff for 256 bytes)
# E = 2^2048 - 1 (all 0xff for 256 bytes)
# M = 2^2048 - 3 (all 0xff except last byte is 0xfd for odd modulus)
# This costs ~698,709 gas per call (EIP-2565)
MODEXP_INPUT = create_modexp_input(
    base=bytes.fromhex("ff" * 256),      # 2^2048 - 1
    exponent=bytes.fromhex("ff" * 256),  # 2^2048 - 1
    modulus=bytes.fromhex("ff" * 255 + "fd"),  # 2^2048 - 3 (odd)
)

MODEXP_CONFIG = MarginalPrecompileConfig(
    name="MODEXP",
    address=MODEXP_ADDRESS,
    max_op_count=3,  # ~699K gas per call, need high gas limit
    step=1,
    input_data=MODEXP_INPUT,
    input_size=len(MODEXP_INPUT),  # 96 + 256 + 256 + 256 = 864 bytes
)

# ============================================================================
# SHA256 precompile (0x02) - Using 4KB input (worst-case)
# Gas: 60 + 12 * ceil(input_bytes/32) = 60 + 12 * 128 = 1,596 gas per call
# Max ops limited by bytecode size (24KB), not gas: ~1500 ops fit
# ============================================================================
SHA256_INPUT = bytes.fromhex("ff" * 4096)  # 4KB of 0xff

SHA256_CONFIG = MarginalPrecompileConfig(
    name="SHA256",
    address=SHA256_ADDRESS,
    max_op_count=1500,  # 1500 * 1,596 ≈ 2.4M gas (bytecode limited)
    step=150,
    input_data=SHA256_INPUT,
    input_size=len(SHA256_INPUT),  # 4096 bytes
)

# ============================================================================
# RIPEMD160 precompile (0x03) - Using 1KB input (worst-case)
# Gas: 600 + 120 * ceil(input_bytes/32) = 600 + 120 * 32 = 4,440 gas per call
# Max ops limited by bytecode size (24KB), not gas: ~1500 ops fit
# ============================================================================
RIPEMD160_INPUT = bytes.fromhex("ff" * 1024)  # 1KB of 0xff

RIPEMD160_CONFIG = MarginalPrecompileConfig(
    name="RIPEMD160",
    address=RIPEMD160_ADDRESS,
    max_op_count=1500,  # 1500 * 4,440 ≈ 6.7M gas (bytecode limited)
    step=375,  # ~5 data points
    input_data=RIPEMD160_INPUT,
    input_size=len(RIPEMD160_INPUT),  # 1024 bytes
)

# ============================================================================
# IDENTITY precompile (0x04) - Using 128 bytes input (same as ECRECOVER)
# Gas: 15 + 3 * ceil(input_bytes/32) = 15 + 3 * 4 = 27 gas per call
# Note: Using smaller input to match working precompile test structure
# ============================================================================
IDENTITY_INPUT = bytes.fromhex("ff" * 128)  # 128 bytes of 0xff

IDENTITY_CONFIG = MarginalPrecompileConfig(
    name="IDENTITY",
    address=IDENTITY_ADDRESS,
    max_op_count=312,  # Increased for ~1M gas (cheap precompile)
    step=78,  # ~5 data points
    input_data=IDENTITY_INPUT,
    input_size=len(IDENTITY_INPUT),  # 128 bytes
)

# ============================================================================
# BN128_ADD precompile (0x06) - Valid curve points
# Gas: 150 (fixed)
# Input: Two G1 points (64 bytes each = 128 bytes total)
# ============================================================================
# Valid G1 points on the alt_bn128 curve
BN128_ADD_INPUT = bytes.fromhex(
    # Point 1 (x, y) - valid curve point
    "18b18acfb4c2c30276db5411368e7185b311dd124691610c5d3b74034e093dc9"
    "063c909c4720840cb5134cb9f59fa749755796819658d32efc0d288198f37266"
    # Point 2 (x, y) - valid curve point
    "07c2b7f58a84bd6145f00c9c2bc0bb1a187f20ff2c92963a88019e7c6a014eed"
    "06614e20c147e940f2d70da3f74c9a17df361706a4485c742bd6788478fa17d7"
)

BN128_ADD_CONFIG = MarginalPrecompileConfig(
    name="BN128_ADD",
    address=BN128_ADD_ADDRESS,
    max_op_count=457,  # Increased for ~1M gas (150 gas/call)
    step=114,  # ~5 data points
    input_data=BN128_ADD_INPUT,
    input_size=len(BN128_ADD_INPUT),  # 128 bytes
)

# ============================================================================
# BN128_MUL precompile (0x07) - Worst case: maximum 32-byte scalar
# Gas: 6,000 (fixed)
# Input: G1 point (64 bytes) + scalar (32 bytes) = 96 bytes
# ============================================================================
BN128_MUL_INPUT = bytes.fromhex(
    # G1 point (x, y) - valid curve point
    "1a87b0584ce92f4593d161480614f2989035225609f08058ccfa3d0f940febe3"
    "1a2f3c951f6dadcc7ee9007dff81504b0fcd6d7cf59996efdc33d92bf7f9f8f6"
    # Scalar - maximum value (32 bytes of 0xff) for worst case
    "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
)

BN128_MUL_CONFIG = MarginalPrecompileConfig(
    name="BN128_MUL",
    address=BN128_MUL_ADDRESS,
    max_op_count=73,  # Increased for ~1M gas (6000 gas/call)
    step=18,  # ~5 data points
    input_data=BN128_MUL_INPUT,
    input_size=len(BN128_MUL_INPUT),  # 96 bytes
)

# ============================================================================
# BN128_PAIRING precompile (0x08) - Worst case: multiple pairs
# Gas: 45,000 + 34,000 * num_pairs = 113,000 for 2 pairs
# Input: Each pair is 192 bytes (G1 point 64 bytes + G2 point 128 bytes)
# ============================================================================
BN128_PAIRING_INPUT = bytes.fromhex(
    # Pair 1: G1 point + G2 point
    "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f59"
    "3034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41"
    "209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf7"
    "04bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a41678"
    "2bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d"
    "120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550"
    # Pair 2: G1 point + G2 point
    "111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c"
    "103188585e2364128fe25c70558f1560f4f9350baf3959e603cc91486e110936"
    "198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2"
    "1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed"
    "090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b"
    "12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa"
)

BN128_PAIRING_CONFIG = MarginalPrecompileConfig(
    name="BN128_PAIRING",
    address=BN128_PAIRING_ADDRESS,
    max_op_count=8,  # Increased for ~1M gas (113K gas/call)
    step=2,
    input_data=BN128_PAIRING_INPUT,
    input_size=len(BN128_PAIRING_INPUT),  # 384 bytes (2 pairs * 192)
)

# ============================================================================
# BLAKE2F precompile (0x09) - Worst case: maximum rounds (0xFFFF = 65,535)
# Gas: 1 * rounds = 65,535 gas per call
# Input: 213 bytes (4 rounds + 64 h + 128 m + 8 t + 8 t + 1 f)
# ============================================================================
def create_blake2f_input(rounds: int, f: bool = True) -> bytes:
    """Create BLAKE2F precompile input."""
    # Rounds (4 bytes, big endian)
    rounds_bytes = rounds.to_bytes(4, "big")
    # h state vector (64 bytes) - using standard IV
    h = bytes.fromhex(
        "48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5"
        "d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b"
    )
    # m message block (128 bytes)
    m = bytes.fromhex("61626300" + "00" * 124)  # "abc" + padding
    # t offset counters (8 + 8 = 16 bytes)
    t = bytes.fromhex("0300000000000000" + "0000000000000000")
    # f final block flag (1 byte)
    f_byte = bytes([1 if f else 0])
    return rounds_bytes + h + m + t + f_byte

BLAKE2F_INPUT = create_blake2f_input(rounds=0xFFFF, f=True)  # 65,535 rounds

BLAKE2F_CONFIG = MarginalPrecompileConfig(
    name="BLAKE2F",
    address=BLAKE2F_ADDRESS,
    max_op_count=14,  # Increased for ~1M gas (65K gas/call)
    step=3,  # ~5 data points
    input_data=BLAKE2F_INPUT,
    input_size=len(BLAKE2F_INPUT),  # 213 bytes
)

# ============================================================================
# POINT_EVALUATION precompile (0x0A) - KZG point evaluation (EIP-4844)
# Gas: 50,000 (fixed)
# Input: 192 bytes (versioned_hash + z + y + commitment + proof)
# ============================================================================
# Valid KZG proof input from execution-specs benchmark
POINT_EVALUATION_INPUT = bytes.fromhex(
    # versioned_hash (32 bytes)
    "01e798154708fe7789429634053cbf9f99b619f9f084048927333fce637f549b"
    # z (32 bytes) - evaluation point
    "564c0a11a0f704f4fc3e8acfe0f8245f0ad1347b378fbf96e206da11a5d36306"
    # y (32 bytes) - claimed value
    "24d25032e67a7e6a4910df5834b8fe70e6bcfeeac0352434196bdf4b2485d5a1"
    # commitment (48 bytes)
    "8f59a8d2a1a625a17f3fea0fe5eb8c896db3764f3185481bc22f91b4aaffcca25f26936857bc3a7c2539ea8ec3a952b7"
    # proof (48 bytes)
    "873033e038326e87ed3e1276fd140253fa08e9fc25fb2d9a98527fc22a2c9612fbeafdad446cbc7bcdbdcd780af2c16a"
)

POINT_EVALUATION_CONFIG = MarginalPrecompileConfig(
    name="POINT_EVALUATION",
    address=POINT_EVALUATION_ADDRESS,
    max_op_count=16,  # Increased for ~1M gas (50K gas/call)
    step=4,
    input_data=POINT_EVALUATION_INPUT,
    input_size=len(POINT_EVALUATION_INPUT),  # 192 bytes
)

# ============================================================================
# BLS12-381 Precompiles (EIP-2537, Prague)
# ============================================================================

# BLS12_G1ADD (0x0B) - Add two G1 points
# Gas: 375 (fixed)
# Input: 256 bytes (two 128-byte G1 points)
# Output: 128 bytes (one G1 point)
# Using G1 generator + P1 (random test point) from EIP-2537 spec
BLS12_G1ADD_INPUT = bytes(BLS12Spec.G1 + BLS12Spec.P1)

BLS12_G1ADD_CONFIG = MarginalPrecompileConfig(
    name="BLS12_G1ADD",
    address=BLS12_G1ADD_ADDRESS,
    max_op_count=772,  # Increased for ~1M gas (375 gas/call)
    step=193,  # ~5 data points
    input_data=BLS12_G1ADD_INPUT,
    input_size=len(BLS12_G1ADD_INPUT),  # 256 bytes
)

# BLS12_G1MSM (0x0C) - Multi-scalar multiplication on G1
# Gas: variable based on k (number of pairs)
# Input: k × 160 bytes (k pairs of G1 point + scalar)
# Using k=2 with G1 generator and P1 points, scalar=1
BLS12_G1MSM_INPUT = bytes(
    BLS12Spec.G1 + Scalar(1) + BLS12Spec.P1 + Scalar(1)
)

BLS12_G1MSM_CONFIG = MarginalPrecompileConfig(
    name="BLS12_G1MSM",
    address=BLS12_G1MSM_ADDRESS,
    max_op_count=40,  # Reduced to fit within 1M gas limit (40 × ~22500 = 900K)
    step=10,  # ~5 data points
    input_data=BLS12_G1MSM_INPUT,
    input_size=len(BLS12_G1MSM_INPUT),  # 320 bytes (2 × 160)
)

# BLS12_G2ADD (0x0D) - Add two G2 points
# Gas: 600 (fixed)
# Input: 512 bytes (two 256-byte G2 points)
# Output: 256 bytes (one G2 point)
# Using G2 generator + P2 (random test point) from EIP-2537 spec
BLS12_G2ADD_INPUT = bytes(BLS12Spec.G2 + BLS12Spec.P2)

BLS12_G2ADD_CONFIG = MarginalPrecompileConfig(
    name="BLS12_G2ADD",
    address=BLS12_G2ADD_ADDRESS,
    max_op_count=451,  # Increased for ~1M gas (600 gas/call)
    step=112,  # ~5 data points
    input_data=BLS12_G2ADD_INPUT,
    input_size=len(BLS12_G2ADD_INPUT),  # 512 bytes
)

# BLS12_G2MSM (0x0E) - Multi-scalar multiplication on G2
# Gas: variable based on k
# Input: k × 288 bytes (k pairs of G2 point + scalar)
# Using k=2 with G2 generator and P2 points, scalar=1
BLS12_G2MSM_INPUT = bytes(
    BLS12Spec.G2 + Scalar(1) + BLS12Spec.P2 + Scalar(1)
)

BLS12_G2MSM_CONFIG = MarginalPrecompileConfig(
    name="BLS12_G2MSM",
    address=BLS12_G2MSM_ADDRESS,
    max_op_count=23,  # Increased for ~1M gas
    step=5,  # ~5 data points
    input_data=BLS12_G2MSM_INPUT,
    input_size=len(BLS12_G2MSM_INPUT),  # 576 bytes (2 × 288)
)

# BLS12_PAIRING (0x0F) - Pairing check
# Gas: 37700 + 32600 * k (k = number of pairs)
# Input: k × 384 bytes (k pairs of G1 + G2 points)
# Using k=2: e(G1, G2) * e(G1, -G2) = 1 (TRUE) - valid pairing from EIP-2537 spec
BLS12_PAIRING_INPUT = bytes(
    BLS12Spec.G1 + BLS12Spec.G2 + BLS12Spec.G1 + (-BLS12Spec.G2)
)

BLS12_PAIRING_CONFIG = MarginalPrecompileConfig(
    name="BLS12_PAIRING",
    address=BLS12_PAIRING_ADDRESS,
    max_op_count=10,  # Variable gas, k=2
    step=2,
    input_data=BLS12_PAIRING_INPUT,
    input_size=len(BLS12_PAIRING_INPUT),  # 768 bytes (2 × 384)
)

# BLS12_MAP_FP_TO_G1 (0x10) - Map field element to G1
# Gas: 5,500 (fixed)
# Input: 64 bytes (one Fp element, padded)
# Output: 128 bytes (one G1 point)
# Using FP(P-1) from EIP-2537 spec - non-trivial input for worst case
BLS12_MAP_FP_TO_G1_INPUT = bytes(FP(BLS12Spec.P - 1))

BLS12_MAP_FP_TO_G1_CONFIG = MarginalPrecompileConfig(
    name="BLS12_MAP_FP_TO_G1",
    address=BLS12_MAP_FP_TO_G1_ADDRESS,
    max_op_count=169,  # Increased for ~1M gas (5500 gas/call)
    step=42,  # ~5 data points
    input_data=BLS12_MAP_FP_TO_G1_INPUT,
    input_size=len(BLS12_MAP_FP_TO_G1_INPUT),  # 64 bytes
)

# BLS12_MAP_FP2_TO_G2 (0x11) - Map Fp2 element to G2
# Gas: 23,800 (fixed)
# Input: 128 bytes (one Fp2 element)
# Output: 256 bytes (one G2 point)
# Using FP2(P-1, P-1) from EIP-2537 spec - non-trivial input for worst case
BLS12_MAP_FP2_TO_G2_INPUT = bytes(FP2((BLS12Spec.P - 1, BLS12Spec.P - 1)))

BLS12_MAP_FP2_TO_G2_CONFIG = MarginalPrecompileConfig(
    name="BLS12_MAP_FP2_TO_G2",
    address=BLS12_MAP_FP2_TO_G2_ADDRESS,
    max_op_count=36,  # Reduced to fit within 1M gas limit (36 × 23800 = 857K + overhead)
    step=9,  # ~5 data points
    input_data=BLS12_MAP_FP2_TO_G2_INPUT,
    input_size=len(BLS12_MAP_FP2_TO_G2_INPUT),  # 128 bytes
)


# Address for "noop" STATICCALL - an invalid precompile address that fails immediately
# Using 0xFFFF as per gas-cost-estimator approach
NOOP_PRECOMPILE_ADDRESS = Address(0xFFFF)


def generate_marginal_precompile_program(
    config: MarginalPrecompileConfig,
    op_count: int,
) -> tuple[Bytecode, bytes]:
    """
    Generate a marginal program for a precompile.

    Uses the gas-cost-estimator technique: keep TOTAL STATICCALL count constant
    by padding with noop STATICCALLs to an invalid address (0xFFFF).
    
    This ensures STATICCALL overhead is constant and cancels out in regression,
    leaving only the pure precompile computation cost as the measured slope.

    Returns:
        Tuple of (bytecode, calldata) where calldata contains the precompile input
    """
    assert 0 <= op_count <= config.max_op_count

    code = Bytecode()

    # 1. Copy calldata (precompile input) to memory at offset 0
    code += Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)

    # Calculate ret_offset after input data to avoid corrupting it
    ret_offset = config.input_size

    # 2. "Noop" STATICCALLs to invalid address 0xFFFF
    # These fail immediately (no valid precompile) but still incur STATICCALL overhead
    # Total STATICCALL count = max_op_count + 1 (constant across all op_count values)
    noop_count = config.max_op_count - op_count + 1
    for _ in range(noop_count):
        code += Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=NOOP_PRECOMPILE_ADDRESS,
                args_offset=0,
                args_size=config.input_size,
                ret_offset=ret_offset,
                ret_size=32,
            )
        )

    # 3. Real precompile calls - op_count times
    # Each call: STATICCALL(gas, addr, argsOffset, argsSize, retOffset, retSize)
    # Pass all available gas - unused gas is returned after the call
    for _ in range(op_count):
        code += Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=config.address,
                args_offset=0,
                args_size=config.input_size,
                ret_offset=ret_offset,
                ret_size=32,
            )
        )

    # 4. Write success marker to storage
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)

    # 5. Stop
    code += Op.STOP

    return code, config.input_data


def generate_op_counts(max_op_count: int, step: int) -> List[int]:
    """Generate list of op_counts from 0 to max_op_count with given step."""
    counts = list(range(0, max_op_count + 1, step))
    # Ensure max_op_count is included even if not aligned with step
    if counts[-1] != max_op_count:
        counts.append(max_op_count)
    return counts


# ============================================================================
# ECRECOVER precompile tests (3000 gas per call)
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(ECRECOVER_CONFIG.max_op_count, ECRECOVER_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_ecrecover(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for ECRECOVER precompile.

    Generates a program with exactly `op_count` ECRECOVER calls.
    Uses a valid signature input that performs full EC recovery (worst case).
    ECRECOVER has a fixed gas cost of 3000 per call.

    The test verifies execution completed successfully via storage marker.
    """
    code, calldata = generate_marginal_precompile_program(ECRECOVER_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        data=calldata,
        sender=sender,
    )

    # Verify execution completed successfully (didn't revert)
    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# MODEXP precompile tests (variable gas cost based on input sizes)
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(MODEXP_CONFIG.max_op_count, MODEXP_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_modexp(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for MODEXP precompile.

    Generates a program with exactly `op_count` MODEXP calls.
    Uses true worst-case input: 256-byte (2048-bit) base, exponent, and modulus,
    all set to maximum values for maximum computational work.
    - B = 2^2048 - 1, E = 2^2048 - 1, M = 2^2048 - 3
    - Gas cost: ~698,709 per call (EIP-2565)

    The test verifies execution completed successfully via storage marker.
    """
    code, calldata = generate_marginal_precompile_program(MODEXP_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=10_000_000,  # High limit for worst-case MODEXP (~700K gas per call)
        data=calldata,
        sender=sender,
    )

    # Verify execution completed successfully (didn't revert)
    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(gas_limit=100_000_000), pre=pre, post=post, tx=tx)


# ============================================================================
# SHA256 precompile tests (0x02) - ~1,596 gas per call with 4KB input
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SHA256_CONFIG.max_op_count, SHA256_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_sha256(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for SHA256 precompile.

    Uses worst-case input: 4KB of data for maximum computational work.
    Gas cost: 60 + 12 * ceil(4096/32) = 60 + 12 * 128 = 1,596 gas per call.
    """
    code, calldata = generate_marginal_precompile_program(SHA256_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=50_000_000,  # High limit for worst-case benchmarking
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# RIPEMD160 precompile tests (0x03) - ~4,440 gas per call with 1KB input
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(RIPEMD160_CONFIG.max_op_count, RIPEMD160_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_ripemd160(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for RIPEMD160 precompile.

    Uses worst-case input: 1KB of data for maximum computational work.
    Gas cost: 600 + 120 * ceil(1024/32) = 600 + 120 * 32 = 4,440 gas per call.
    """
    code, calldata = generate_marginal_precompile_program(RIPEMD160_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=50_000_000,  # High limit for worst-case benchmarking
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# IDENTITY precompile tests (0x04) - ~399 gas per call with 4KB input
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(IDENTITY_CONFIG.max_op_count, IDENTITY_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_identity(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for IDENTITY precompile.

    Uses worst-case input: 4KB of data for maximum memory operations.
    Gas cost: 15 + 3 * ceil(4096/32) = 15 + 3 * 128 = 399 gas per call.
    """
    code, calldata = generate_marginal_precompile_program(IDENTITY_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# BN128_ADD precompile tests (0x06) - 150 gas per call
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BN128_ADD_CONFIG.max_op_count, BN128_ADD_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_bn128_add(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for BN128_ADD (ecAdd) precompile.

    Uses valid curve points to ensure full computation is performed.
    Gas cost: 150 (fixed).
    """
    code, calldata = generate_marginal_precompile_program(BN128_ADD_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# BN128_MUL precompile tests (0x07) - 6,000 gas per call
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BN128_MUL_CONFIG.max_op_count, BN128_MUL_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_bn128_mul(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for BN128_MUL (ecMul) precompile.

    Uses worst-case input: maximum scalar (32 bytes of 0xff) for maximum
    computational work in the scalar multiplication.
    Gas cost: 6,000 (fixed).
    """
    code, calldata = generate_marginal_precompile_program(BN128_MUL_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# BN128_PAIRING precompile tests (0x08) - 113,000 gas per call (2 pairs)
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BN128_PAIRING_CONFIG.max_op_count, BN128_PAIRING_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_bn128_pairing(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for BN128_PAIRING (ecPairing) precompile.

    Uses 2 valid pairing pairs for substantial computational work.
    Gas cost: 45,000 + 34,000 * 2 = 113,000 per call.
    """
    code, calldata = generate_marginal_precompile_program(BN128_PAIRING_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# BLAKE2F precompile tests (0x09) - 65,535 gas per call (max rounds)
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BLAKE2F_CONFIG.max_op_count, BLAKE2F_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_blake2f(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for BLAKE2F precompile.

    Uses worst-case input: 0xFFFF (65,535) rounds for maximum computational work.
    Gas cost: 1 * rounds = 65,535 per call.
    """
    code, calldata = generate_marginal_precompile_program(BLAKE2F_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# POINT_EVALUATION precompile tests (0x0A) - 50,000 gas per call
# ============================================================================


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(POINT_EVALUATION_CONFIG.max_op_count, POINT_EVALUATION_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_point_evaluation(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for POINT_EVALUATION (KZG) precompile.

    Uses a valid KZG proof for point evaluation.
    Gas cost: 50,000 (fixed).
    """
    code, calldata = generate_marginal_precompile_program(POINT_EVALUATION_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# BLS12_G1ADD precompile tests (0x0B) - 375 gas per call
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BLS12_G1ADD_CONFIG.max_op_count, BLS12_G1ADD_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_bls12_g1add(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for BLS12_G1ADD precompile.

    Adds two G1 points on the BLS12-381 curve.
    Gas cost: 375 (fixed).
    """
    code, calldata = generate_marginal_precompile_program(BLS12_G1ADD_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# BLS12_G1MSM precompile tests (0x0C) - variable gas per call
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BLS12_G1MSM_CONFIG.max_op_count, BLS12_G1MSM_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_bls12_g1msm(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for BLS12_G1MSM precompile.

    Multi-scalar multiplication on G1 with k=2 pairs for worst-case marginal cost.
    Gas cost: variable based on k.
    """
    code, calldata = generate_marginal_precompile_program(BLS12_G1MSM_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# BLS12_G2ADD precompile tests (0x0D) - 600 gas per call
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BLS12_G2ADD_CONFIG.max_op_count, BLS12_G2ADD_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_bls12_g2add(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for BLS12_G2ADD precompile.

    Adds two G2 points on the BLS12-381 curve.
    Gas cost: 600 (fixed).
    """
    code, calldata = generate_marginal_precompile_program(BLS12_G2ADD_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# BLS12_G2MSM precompile tests (0x0E) - variable gas per call
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BLS12_G2MSM_CONFIG.max_op_count, BLS12_G2MSM_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_bls12_g2msm(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for BLS12_G2MSM precompile.

    Multi-scalar multiplication on G2 with k=2 pairs for worst-case marginal cost.
    Gas cost: variable based on k.
    """
    code, calldata = generate_marginal_precompile_program(BLS12_G2MSM_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=10_000_000,  # High limit for G2MSM
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# BLS12_PAIRING precompile tests (0x0F) - variable gas per call
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BLS12_PAIRING_CONFIG.max_op_count, BLS12_PAIRING_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_bls12_pairing(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for BLS12_PAIRING precompile.

    Pairing check with k=2 pairs for worst-case marginal cost.
    Gas cost: variable based on k.
    """
    code, calldata = generate_marginal_precompile_program(BLS12_PAIRING_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=10_000_000,  # Higher limit for pairing
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# BLS12_MAP_FP_TO_G1 precompile tests (0x10) - 5,500 gas per call
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BLS12_MAP_FP_TO_G1_CONFIG.max_op_count, BLS12_MAP_FP_TO_G1_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_bls12_map_fp_to_g1(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for BLS12_MAP_FP_TO_G1 precompile.

    Maps a field element to a G1 point.
    Gas cost: 5,500 (fixed).
    """
    code, calldata = generate_marginal_precompile_program(BLS12_MAP_FP_TO_G1_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# BLS12_MAP_FP2_TO_G2 precompile tests (0x11) - 23,800 gas per call
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BLS12_MAP_FP2_TO_G2_CONFIG.max_op_count, BLS12_MAP_FP2_TO_G2_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_bls12_map_fp2_to_g2(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for BLS12_MAP_FP2_TO_G2 precompile.

    Maps an Fp2 element to a G2 point.
    Gas cost: 23,800 (fixed).
    """
    code, calldata = generate_marginal_precompile_program(BLS12_MAP_FP2_TO_G2_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        data=calldata,
        sender=sender,
    )

    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
