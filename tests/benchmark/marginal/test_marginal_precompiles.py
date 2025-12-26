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


# ============================================================================
# ECRECOVER precompile (0x01)
# Ref: tests/benchmark/compute/precompile/test_ecrecover.py
# Valid ECRECOVER input that performs full signature recovery (worst case)
# This is a valid signature that will actually recover an address
# execution-specs test also uses a valid signature - our args match
# ============================================================================
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
    step=40,  # 6 data points (improved R²)
    input_data=ECRECOVER_INPUT,
    input_size=len(ECRECOVER_INPUT),  # 128 bytes
)

# ============================================================================
# MODEXP precompile (0x05) - execution-specs benchmark worst case
# Ref: tests/benchmark/compute/precompile/test_modexp.py
# Worst case: mod_vul_nagydani_5_qube (SP1: 3600s - highest in entire benchmark!)
# Uses 512-byte (4096-bit) base and modulus with exponent = 0x03 (cubing)
# This stresses large operand memory handling rather than exponent iterations
# ============================================================================

# mod_vul_nagydani_5_qube input - 512-byte base/mod with exp=3
# Ported from test_modexp.py line 243-247
MODEXP_NAGYDANI_5_BASE = bytes.fromhex(
    "c5a1611f8be90071a43db23cc2fe01871cc4c0e8ab5743f6378e4fef77f7f6db"
    "0095c0727e20225beb665645403453e325ad5f9aeb9ba99bf3c148f63f9c07cf"
    "4fe8847ad5242d6b7d4499f93bd47056ddab8f7dee878fc2314f344dbee2a7c4"
    "1a5d3db91eff372c730c2fdd3a141a4b61999e36d549b9870cf2f4e632c4d5df"
    "5f024f81c028000073a0ed8847cfb0593d36a47142f578f05ccbe28c0c06aeb1"
    "b1da027794c48db880278f79ba78ae64eedfea3c07d10e0562668d839749dc95"
    "f40467d15cf65b9cfc52c7c4bcef1cda3596dd52631aac942f146c7cebd46065"
    "131699ce8385b0db1874336747ee020a5698a3d1a1082665721e769567f57983"
    "0f9d259cec1a836845109c21cf6b25da572512bf3c42fd4b96e43895589042ab"
    "60dd41f497db96aec102087fe784165bb45f942859268fd2ff6c012d9d00c02b"
    "a83eace047cc5f7b2c392c2955c58a49f0338d6fc58749c9db2155522ac17914"
    "ec216ad87f12e0ee95574613942fa615898c4d9e8a3be68cd6afa4e7a003dedb"
    "df8edfee31162b174f965b20ae752ad89c967b3068b6f722c16b354456ba8e28"
    "0f987c08e0a52d40a2e8f3a59b94d590aeef01879eb7a90b3ee7d772c839c855"
    "19cbeaddc0c193ec4874a463b53fcaea3271d80ebfb39b33489365fc039ae549"
    "a17a9ff898eea2f4cb27b8dbee4c17b998438575b2b8d107e4a0d66ba7fca85b"
)

MODEXP_NAGYDANI_5_MODULUS = bytes.fromhex(
    "e30049201ec12937e7ce79d0f55d9c810e20acf52212aca1d3888949e0e4830a"
    "ad88d804161230eb89d4d329cc83570fe257217d2119134048dd2ed167646975"
    "fc7d77136919a049ea74cf08ddd2b896890bb24a0ba18094a22baa351bf29ad9"
    "6c66bbb1a598f2ca391749620e62d61c3561a7d3653ccc8892c7b99baaf76bf8"
    "36e2991cb06d6bc0514568ff0d1ec8bb4b3d6984f5eaefb17d3ea2893722375d"
    "3ddb8e389a8eef7d7d198f8e687d6a513983df906099f9a2d23f4f9dec6f8ef2"
    "f11fc0a21fac45353b94e00486f5e17d386af42502d09db33cf0cf28310e049c"
    "07e88682aeeb00cb833c5174266e62407a57583f1f88b304b7c6e0c84bbe1c0f"
    "d423072d37a5bd0aacf764229e5c7cd02473460ba3645cd8e8ae144065bf02d0"
    "dd238593d8e230354f67e0b2f23012c23274f80e3ee31e35e2606a4a3f31d94a"
    "b755e6d163cff52cbb36b6d0cc67ffc512aeed1dce4d7a0d70ce82f2baba12e8"
    "d514dc92a056f994adfb17b5b9712bd5186f27a2fda1f7039c5df2c8587fdc62"
    "f5627580c13234b55be4df3056050e2d1ef3218f0dd66cb05265fe1acfb0989d"
    "8213f2c19d1735a7cf3fa65d88dad5af52dc2bba22b7abf46c3bc77b5091baab"
    "9e8f0ddc4d5e581037de91a9f8dcbc69309be29cc815cf19a20a7585b8b3073e"
    "df51fc9baeb3e509b97fa4ecfd621e0fd57bd61cac1b895c03248ff12bdbc575"
)

MODEXP_INPUT = create_modexp_input(
    base=MODEXP_NAGYDANI_5_BASE,      # 512 bytes (4096 bits)
    exponent=bytes.fromhex("03"),      # Just cubing (1 byte)
    modulus=MODEXP_NAGYDANI_5_MODULUS, # 512 bytes (4096 bits)
)

MODEXP_CONFIG = MarginalPrecompileConfig(
    name="MODEXP",
    address=MODEXP_ADDRESS,
    max_op_count=36,  # High gas per call, need high gas limit
    step=12,
    input_data=MODEXP_INPUT,
    input_size=len(MODEXP_INPUT),  # 96 + 512 + 1 + 512 = 1121 bytes
)

# ============================================================================
# SHA256 precompile (0x02) - Using 4KB input (worst-case)
# Ref: tests/benchmark/compute/precompile/test_sha256.py
# execution-specs uses dynamic optimal_input_length calculation; we use fixed 4KB
# which is close to optimal for maximizing hash work
# Gas: 60 + 12 * ceil(input_bytes/32) = 60 + 12 * 128 = 1,596 gas per call
# Max ops limited by bytecode size (24KB), not gas: ~1500 ops fit
# ============================================================================
SHA256_INPUT = bytes.fromhex("ff" * 4096)  # 4KB of 0xff

SHA256_CONFIG = MarginalPrecompileConfig(
    name="SHA256",
    address=SHA256_ADDRESS,
    max_op_count=1500,  # 1500 * 1,596 ≈ 2.4M gas (bytecode limited)
    step=500,  # 4 data points
    input_data=SHA256_INPUT,
    input_size=len(SHA256_INPUT),  # 4096 bytes
)

# ============================================================================
# RIPEMD160 precompile (0x03) - Using 1KB input (worst-case)
# Ref: tests/benchmark/compute/precompile/test_ripemd160.py
# execution-specs uses dynamic optimal_input_length calculation; we use fixed 1KB
# Gas: 600 + 120 * ceil(input_bytes/32) = 600 + 120 * 32 = 4,440 gas per call
# Max ops limited by bytecode size (24KB), not gas: ~1500 ops fit
# ============================================================================
RIPEMD160_INPUT = bytes.fromhex("ff" * 1024)  # 1KB of 0xff

RIPEMD160_CONFIG = MarginalPrecompileConfig(
    name="RIPEMD160",
    address=RIPEMD160_ADDRESS,
    max_op_count=1500,  # 1500 * 4,440 ≈ 6.7M gas (bytecode limited)
    step=500,  # 4 data points
    input_data=RIPEMD160_INPUT,
    input_size=len(RIPEMD160_INPUT),  # 1024 bytes
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
    max_op_count=801,
    step=267,  # 4 data points
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
    max_op_count=72,  # Increased for ~1M gas (6000 gas/call)
    step=24,  # 4 data points
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
    max_op_count=12,  # Increased for ~1M gas (65K gas/call)
    step=4,  # ~5 data points
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
    max_op_count=9,  # Increased for ~1M gas (50K gas/call)
    step=3,
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
    max_op_count=771,  # Increased for ~1M gas (375 gas/call)
    step=257,  # 4 data points
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
    max_op_count=39,  # Reduced to fit within 1M gas limit (39 × ~22500 = 877K)
    step=13,  # 4 data points
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
    max_op_count=450,  # Increased for ~1M gas (600 gas/call)
    step=150,  # 4 data points
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
    max_op_count=24,  # Increased for ~1M gas
    step=8,  # 4 data points
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
    max_op_count=9,  # Variable gas, k=2
    step=3,
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
    max_op_count=75,  # Increased for ~1M gas (5500 gas/call)
    step=25,  # ~5 data points
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
    max_op_count=27,
    step=9,
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
# IDENTITY precompile tests (0x04) - Using caller-contract approach for amplification
# The identity precompile is very cheap, so we need high call counts for good data
# ============================================================================

# Caller-based approach constants
IDENTITY_NUM_CALLS = 5000  # Number of caller loop iterations
IDENTITY_MAX_OP_COUNT = 300  # Target executes op_count IDENTITY calls per invocation
IDENTITY_STEP = 60  # 6 data points (improved R²)
IDENTITY_GAS_LIMIT = 500_000_000  # High gas limit for many calls


def _generate_identity_target(op_count: int, max_op_count: int, input_size: int = 128) -> Bytecode:
    """
    Generate a target contract with proper marginal padding.
    
    Uses the gas-cost-estimator technique: keep TOTAL STATICCALL count constant
    by padding with noop STATICCALLs to an invalid address (0xFFFF).
    
    Total STATICCALLs = (max_op_count - op_count + 1) noops + op_count real = max_op_count + 1
    
    This ensures STATICCALL overhead is constant and cancels out in regression.
    """
    code = Bytecode()
    
    # Store input data in memory (128 bytes of 0xff)
    # We store it in 4 chunks of 32 bytes each
    for i in range(4):
        code += Op.MSTORE(i * 32, (1 << 256) - 1)  # 32 bytes of 0xff
    
    ret_offset = input_size  # Return data goes after input
    
    # First loop: noop STATICCALLs to invalid address 0xFFFF
    # These fail immediately but still incur STATICCALL overhead
    noop_count = max_op_count - op_count + 1
    if noop_count > 0:
        if noop_count <= 0xFF:
            code += Op.PUSH1(noop_count)
        elif noop_count <= 0xFFFF:
            code += Op.PUSH2(noop_count)
        else:
            code += Op.PUSH3(noop_count)
        
        noop_loop_start = len(bytes(code))
        code += Op.JUMPDEST
        
        # STATICCALL to invalid address 0xFFFF (noop)
        code += Op.PUSH1(32)                  # retSize
        code += Op.PUSH1(ret_offset)          # retOffset
        code += Op.PUSH1(input_size)          # argsSize
        code += Op.PUSH1(0)                   # argsOffset
        code += Op.PUSH2(0xFFFF)              # address (invalid - noop)
        code += Op.GAS                        # gas
        code += Op.STATICCALL
        code += Op.POP                        # pop success flag (will be 0)
        
        # Decrement counter and loop
        code += Op.PUSH1(1)
        code += Op.SWAP1
        code += Op.SUB
        code += Op.DUP1
        code += Op.PUSH2(noop_loop_start)
        code += Op.JUMPI
        code += Op.POP
    
    # Second loop: real STATICCALLs to IDENTITY precompile
    if op_count > 0:
        if op_count <= 0xFF:
            code += Op.PUSH1(op_count)
        elif op_count <= 0xFFFF:
            code += Op.PUSH2(op_count)
        else:
            code += Op.PUSH3(op_count)
        
        real_loop_start = len(bytes(code))
        code += Op.JUMPDEST
        
        # STATICCALL to IDENTITY (0x04)
        code += Op.PUSH1(32)                  # retSize
        code += Op.PUSH1(ret_offset)          # retOffset
        code += Op.PUSH1(input_size)          # argsSize
        code += Op.PUSH1(0)                   # argsOffset
        code += Op.PUSH1(0x04)                # address (IDENTITY)
        code += Op.GAS                        # gas
        code += Op.STATICCALL
        code += Op.POP                        # pop success flag
        
        # Decrement counter and loop
        code += Op.PUSH1(1)
        code += Op.SWAP1
        code += Op.SUB
        code += Op.DUP1
        code += Op.PUSH2(real_loop_start)
        code += Op.JUMPI
        code += Op.POP
    
    code += Op.STOP
    
    return code


def _generate_identity_caller(target_address: Address, num_calls: int) -> Bytecode:
    """
    Generate a caller contract that calls the target num_calls times using a loop.
    Uses STATICCALL since target doesn't modify state.
    """
    code = Bytecode()
    
    # Push loop counter
    if num_calls <= 0xFF:
        code += Op.PUSH1(num_calls)
    elif num_calls <= 0xFFFF:
        code += Op.PUSH2(num_calls)
    else:
        code += Op.PUSH3(num_calls)
    
    loop_start_offset = len(bytes(code))
    code += Op.JUMPDEST
    
    # STATICCALL to target
    code += Op.PUSH1(0)                   # retSize
    code += Op.PUSH1(0)                   # retOffset
    code += Op.PUSH1(0)                   # argsSize
    code += Op.PUSH1(0)                   # argsOffset
    code += Op.PUSH20(target_address)     # address
    code += Op.GAS                        # gas
    code += Op.STATICCALL
    code += Op.POP                        # pop success flag
    
    # Decrement counter and loop
    code += Op.PUSH1(1)
    code += Op.SWAP1
    code += Op.SUB
    code += Op.DUP1
    code += Op.PUSH2(loop_start_offset)
    code += Op.JUMPI
    
    # Done - write success marker
    code += Op.POP
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(IDENTITY_MAX_OP_COUNT, IDENTITY_STEP),
    ids=lambda x: f"op_count_{x * IDENTITY_NUM_CALLS}",
)
def test_marginal_identity(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for IDENTITY precompile using caller-contract approach.
    
    Uses a two-level structure:
    - Caller contract loops IDENTITY_NUM_CALLS times
    - Target contract calls IDENTITY precompile op_count times per invocation
    - Total IDENTITY calls = IDENTITY_NUM_CALLS × op_count
    
    This amplifies the cheap IDENTITY precompile to generate meaningful ZK cycles.
    """
    # Target contract calls IDENTITY op_count times with noop padding
    target_code = _generate_identity_target(op_count, IDENTITY_MAX_OP_COUNT)
    target = pre.deploy_contract(code=target_code)
    
    # Caller contract loops IDENTITY_NUM_CALLS times
    caller_code = _generate_identity_caller(target, IDENTITY_NUM_CALLS)
    caller = pre.deploy_contract(code=caller_code)
    
    sender = pre.fund_eoa()
    
    tx = Transaction(
        to=caller,
        gas_limit=IDENTITY_GAS_LIMIT,
        sender=sender,
    )
    
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    
    state_test(env=Environment(gas_limit=IDENTITY_GAS_LIMIT), pre=pre, post=post, tx=tx)


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
