"""
Marginal cost estimation tests for EVM opcodes.

This module implements the "marginal approach" for gas cost estimation as described
in the gas-cost-estimator project. The key insight is:

1. Generate a series of programs where only the number of target opcodes varies
2. Keep everything else constant (stack setup, cleanup, contract call overhead, etc)
3. The marginal per-gas cost of an opcode can be extracted via linear regression on execution times

"""

from dataclasses import dataclass
from typing import Callable, List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Bytes,
    Environment,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
)

# Success marker written to storage if execution completes without revert
SUCCESS_MARKER = 0xDEAD
SUCCESS_SLOT = 0


@dataclass
class MarginalOpcodeConfig:
    """Configuration for a marginal opcode test."""

    name: str
    """Name of the opcode for test identification."""

    opcode: Op
    """The opcode to measure."""

    max_op_count: int
    """Maximum number of opcode instances per call."""

    step: int
    """Step size for op_count increments."""

    stack_args: List[int]
    """Values to push for each opcode instance (one per argument)."""

    inputs_per_op: int
    """Number of stack inputs consumed by the opcode."""

    outputs_per_op: int
    """Number of stack outputs produced by the opcode."""

    num_calls: int = 100
    """Number of times amplifier calls target (to amplify gas usage)."""

    setup_code: Bytecode | None = None
    """Optional setup code to run before the main loop (e.g., memory init)."""


@dataclass
class CustomTargetConfig:
    """Configuration for opcodes that require custom target bytecode generators.

    Used for DUP, SWAP, LOG, JUMP - opcodes that can't use the generic
    generate_target_contract_code() and need specialized bytecode generation.
    """

    name: str
    """Name of the opcode for test identification."""

    max_op_count: int
    """Maximum number of opcode instances per call."""

    step: int
    """Step size for op_count increments."""

    num_calls: int
    """Number of times amplifier calls target (to amplify gas usage)."""

    # For DUP/SWAP: which variant (1-16)
    variant: int = 0
    """For DUP1-16 or SWAP1-16, specifies which variant."""

    # For LOG: number of topics
    topic_count: int = 0
    """For LOG0-4, specifies number of topics."""


# ============================================================================
# ARITHMETIC OPCODES
# Arguments aligned with execution-specs benchmark worst cases from:
# tests/benchmark/compute/instruction/test_arithmetic.py
# ============================================================================
MAX_U256 = (1 << 256) - 1  # Maximum uint256 value
MAX_S256_NEG = 1 << 255     # Most negative signed int256

# execution-specs benchmark DEFAULT_BINOP_ARGS from helpers.py
# These are secp256k1 field prime and BLS12-381 scalar field modulus
# Ref: tests/benchmark/compute/helpers.py
SECP256K1_FIELD_PRIME = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
BLS12_381_SCALAR_FIELD = 0x73EDA753299D7D483339D80809A1D80553BDA402FFFE5BFEFFFFFFFF00000001

# DIV worst case: divisor slightly > 2^128 triggers 3-word division path
# Ref: test_arithmetic.py opcode_DIV-0
DIV_DIVIDEND = SECP256K1_FIELD_PRIME
DIV_DIVISOR = 0x100000000000000000000000000000033  # Slightly > 2^128

# SDIV worst case: same as DIV-0 but with sign adjustments
# Ref: test_arithmetic.py opcode_SDIV-1
SDIV_DIVIDEND = 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F  # Positive
SDIV_DIVISOR = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFCD  # Negative ~2^128

# MOD/SMOD/ADDMOD/MULMOD worst case: 191-bit modulus
# execution-specs found 191-bit modulus is SLOWER than 255-bit (counterintuitive!)
# Ref: test_arithmetic.py op_MOD-mod_bits_191, op_MULMOD-mod_bits_191, etc.
MOD_191_BIT = (1 << 191) - 1  # 191-bit modulus for worst-case division

# ============================================================================
# STACK LIMIT CALCULATION:
# For POP-based padding (outputs_per_op > 0), peak stack usage is:
#   max_op_count * outputs_per_op + max_op_count * len(stack_args)
# = max_op_count * (outputs_per_op + len(stack_args))
#
# Stack limit is 1024, so:
#   max_op_count <= 1024 / (outputs_per_op + len(stack_args))
#
# Using 900 as safe limit to leave room for setup/cleanup:
# - 2-arg + 1-return ops: max = 900/3 = 300
# - 3-arg + 1-return ops: max = 900/4 = 225
# - 1-arg + 1-return ops: max = 900/2 = 450
# ============================================================================

# Ref: test_arithmetic.py opcode_ADD (uses DEFAULT_BINOP_ARGS)
ADD_CONFIG = MarginalOpcodeConfig(
    name="ADD",
    opcode=Op.ADD,
    max_op_count=300,  # 300 * 3 = 900 < 1024
    step=75,  # 5 data points
    stack_args=[BLS12_381_SCALAR_FIELD, SECP256K1_FIELD_PRIME],  # DEFAULT_BINOP_ARGS
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=600,
)

# Ref: test_arithmetic.py opcode_MUL (uses DEFAULT_BINOP_ARGS)
MUL_CONFIG = MarginalOpcodeConfig(
    name="MUL",
    opcode=Op.MUL,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[BLS12_381_SCALAR_FIELD, SECP256K1_FIELD_PRIME],  # DEFAULT_BINOP_ARGS
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=150,
)

# Ref: test_arithmetic.py opcode_SUB (uses DEFAULT_BINOP_ARGS)
SUB_CONFIG = MarginalOpcodeConfig(
    name="SUB",
    opcode=Op.SUB,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[BLS12_381_SCALAR_FIELD, SECP256K1_FIELD_PRIME],  # DEFAULT_BINOP_ARGS
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=950,
)

# Ref: test_arithmetic.py opcode_DIV-0
# Worst case: divisor slightly > 2^128 triggers 3-word division path
DIV_CONFIG = MarginalOpcodeConfig(
    name="DIV",
    opcode=Op.DIV,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[DIV_DIVISOR, DIV_DIVIDEND],  # divisor, dividend
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=100,
)

# Ref: test_arithmetic.py opcode_SDIV-1
# Worst case: positive dividend, negative ~2^128 divisor
SDIV_CONFIG = MarginalOpcodeConfig(
    name="SDIV",
    opcode=Op.SDIV,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[SDIV_DIVISOR, SDIV_DIVIDEND],  # divisor, dividend
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=100,
)

# Ref: test_arithmetic.py op_MOD-mod_bits_191
# execution-specs found 191-bit modulus is SLOWER than 255-bit (counterintuitive!)
MOD_CONFIG = MarginalOpcodeConfig(
    name="MOD",
    opcode=Op.MOD,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[MOD_191_BIT, MAX_U256],  # 191-bit modulus, MAX dividend
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=100,
)

# Ref: test_arithmetic.py op_SMOD-mod_bits_191
# execution-specs found 191-bit modulus is SLOWER than 255-bit (counterintuitive!)
SMOD_CONFIG = MarginalOpcodeConfig(
    name="SMOD",
    opcode=Op.SMOD,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[MOD_191_BIT, MAX_U256],  # 191-bit modulus, MAX dividend
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=150,
)

# Ref: test_arithmetic.py op_ADDMOD-mod_bits_191
# execution-specs found 191-bit modulus is SLOWER than 255-bit (counterintuitive!)
ADDMOD_CONFIG = MarginalOpcodeConfig(
    name="ADDMOD",
    opcode=Op.ADDMOD,
    max_op_count=200,  # 200 * 4 = 800 < 1024
    step=50,  # 5 data points
    stack_args=[MOD_191_BIT, MAX_U256, MAX_U256],  # N=191-bit mod, b=MAX, a=MAX
    inputs_per_op=3,
    outputs_per_op=1,
    num_calls=100,
)

# Ref: test_arithmetic.py op_MULMOD-mod_bits_191
# execution-specs found 191-bit modulus is SLOWER than 255-bit (counterintuitive!)
MULMOD_CONFIG = MarginalOpcodeConfig(
    name="MULMOD",
    opcode=Op.MULMOD,
    max_op_count=200,
    step=50,  # 5 data points
    stack_args=[MOD_191_BIT, MAX_U256, MAX_U256],  # N=191-bit mod, b=MAX, a=MAX
    inputs_per_op=3,
    outputs_per_op=1,
    num_calls=100,
)

# Ref: test_arithmetic.py opcode_EXP (uses MAX_U256, MAX_U256)
# EXP is expensive: 10 + 50 * byte_length_of_exponent
# With 32-byte exponent = 10 + 50 * 32 = 1610 gas
EXP_CONFIG = MarginalOpcodeConfig(
    name="EXP",
    opcode=Op.EXP,
    max_op_count=200,
    step=50,  # 5 data points
    stack_args=[MAX_U256, MAX_U256],  # execution-specs uses MAX for both - matches!
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=5,
)

# Ref: test_arithmetic.py opcode_SIGNEXTEND (uses k=3, x=0xFFDADADA)
# execution-specs uses k=3 (sign-extend 4 bytes) with a negative value
SIGNEXTEND_CONFIG = MarginalOpcodeConfig(
    name="SIGNEXTEND",
    opcode=Op.SIGNEXTEND,
    max_op_count=300,  # 300 * 3 = 900 < 1024
    step=75,  # 5 data points
    stack_args=[0xFFDADADA, 3],  # x=negative value, k=3 (4-byte extend)
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=300,
)

# ============================================================================
# COMPARISON OPCODES
# ============================================================================

LT_CONFIG = MarginalOpcodeConfig(
    name="LT",
    opcode=Op.LT,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[MAX_U256, MAX_U256],
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=400,
)

GT_CONFIG = MarginalOpcodeConfig(
    name="GT",
    opcode=Op.GT,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[MAX_U256, MAX_U256],
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=400,
)

SLT_CONFIG = MarginalOpcodeConfig(
    name="SLT",
    opcode=Op.SLT,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[MAX_U256, MAX_U256],
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=650,
)

SGT_CONFIG = MarginalOpcodeConfig(
    name="SGT",
    opcode=Op.SGT,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[MAX_U256, MAX_U256],
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=450,
)

EQ_CONFIG = MarginalOpcodeConfig(
    name="EQ",
    opcode=Op.EQ,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[MAX_U256, MAX_U256],
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=300,
)

ISZERO_CONFIG = MarginalOpcodeConfig(
    name="ISZERO",
    opcode=Op.ISZERO,
    max_op_count=360,  # 360 * 2 = 720 < 1024
    step=90,  # 5 data points
    stack_args=[MAX_U256],
    inputs_per_op=1,
    outputs_per_op=1,
    num_calls=600,
)

# ============================================================================
# BITWISE OPCODES
# ============================================================================

AND_CONFIG = MarginalOpcodeConfig(
    name="AND",
    opcode=Op.AND,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[MAX_U256, MAX_U256],
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=400,
)

OR_CONFIG = MarginalOpcodeConfig(
    name="OR",
    opcode=Op.OR,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[MAX_U256, MAX_U256],
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=600,
)

XOR_CONFIG = MarginalOpcodeConfig(
    name="XOR",
    opcode=Op.XOR,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[MAX_U256, MAX_U256],
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=600,
)

NOT_CONFIG = MarginalOpcodeConfig(
    name="NOT",
    opcode=Op.NOT,
    max_op_count=360,  # 360 * 2 = 720 < 1024
    step=90,  # 5 data points
    stack_args=[MAX_U256],
    inputs_per_op=1,
    outputs_per_op=1,
    num_calls=500,
)

BYTE_CONFIG = MarginalOpcodeConfig(
    name="BYTE",
    opcode=Op.BYTE,
    max_op_count=300,  # 300 * 3 = 900 < 1024
    step=75,  # 5 data points
    stack_args=[MAX_U256, 31],  # x=MAX, i=31
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=400,
)

SHL_CONFIG = MarginalOpcodeConfig(
    name="SHL",
    opcode=Op.SHL,
    max_op_count=300,  # 300 * 3 = 900 < 1024
    step=75,  # 5 data points
    stack_args=[MAX_U256, 255],  # value=MAX, shift=255
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=400,
)

SHR_CONFIG = MarginalOpcodeConfig(
    name="SHR",
    opcode=Op.SHR,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[MAX_U256, 255],  # value=MAX, shift=255
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=400,
)

SAR_CONFIG = MarginalOpcodeConfig(
    name="SAR",
    opcode=Op.SAR,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[MAX_U256, 255],  # value=MAX, shift=255
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=300,
)

# ============================================================================
# KECCAK256 OPCODE - Variable cost based on input size
# Ref: tests/benchmark/compute/instruction/test_keccak.py
# execution-specs has test_keccak_max_permutations (dynamic sizing) and test_keccak (fixed sizes)
# We use 8KB input to maximize hash work per call - similar to max permutations approach
# ============================================================================

# KECCAK256 with 8KB input for worst-case testing (aligned with gas-cost-estimator)
def _generate_keccak256_setup() -> Bytecode:
    """Generate setup code that fills memory with 8KB (256 x 32 bytes) of data."""
    code = Bytecode()
    # Fill memory with MAX_U256 values (8KB = 256 * 32 bytes)
    for i in range(256):
        offset = i * 32
        code += Op.MSTORE(offset, MAX_U256)
    return code


KECCAK256_CONFIG = MarginalOpcodeConfig(
    name="KECCAK256",
    opcode=Op.SHA3,  # SHA3 is the opcode name for KECCAK256
    max_op_count=120,
    step=30,  # 5 data points
    stack_args=[8192, 0],  # size=8KB, offset=0
    inputs_per_op=2,
    outputs_per_op=1,
    num_calls=20,
    # Pre-allocate 8KB of memory with data to hash
    setup_code=_generate_keccak256_setup(),
)

# ============================================================================
# STACK OPCODES
# ============================================================================
# We benchmark representative samples rather than all variants:
# - PUSH: PUSH0, PUSH1, PUSH16, PUSH32 (covers zero, small, medium, max sizes)
# - POP: single variant
# - DUP/SWAP: 1, 8, 16 variants (covers shallow, mid, deep stack access)

PUSH0_CONFIG = MarginalOpcodeConfig(
    name="PUSH0",
    opcode=Op.PUSH0,  # EIP-3855, pushes 0 onto stack
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=500,
)

PUSH1_CONFIG = MarginalOpcodeConfig(
    name="PUSH1",
    opcode=Op.PUSH1(0xFF),  # Push max 1-byte value
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],  # PUSH doesn't consume stack
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=300,
)

PUSH16_CONFIG = MarginalOpcodeConfig(
    name="PUSH16",
    opcode=Op.PUSH16(MAX_U256 >> 128),  # Max 16-byte value
    max_op_count=500,
    step=125,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=500,
)

PUSH32_CONFIG = MarginalOpcodeConfig(
    name="PUSH32",
    opcode=Op.PUSH32(MAX_U256),  # Max 32-byte value
    max_op_count=280,
    step=70,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=300,
)


# For marginal testing, we need to provide values to pop
POP_CONFIG = MarginalOpcodeConfig(
    name="POP",
    opcode=Op.POP,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[0],  # Push 0 to pop (using PUSH0 is cheapest)
    inputs_per_op=1,
    outputs_per_op=0,
    num_calls=1100,
)

# ============================================================================
# CUSTOM TARGET CONFIGS - DUP, SWAP, LOG, JUMP
# These opcodes require custom target generators (not MarginalOpcodeConfig).
# ============================================================================

DUP1_CONFIG = CustomTargetConfig(
    name="DUP1", max_op_count=300, step=75, num_calls=950, variant=1  # 5 points
)
DUP8_CONFIG = CustomTargetConfig(
    name="DUP8", max_op_count=300, step=75, num_calls=950, variant=8  # 5 points
)
DUP16_CONFIG = CustomTargetConfig(
    name="DUP16", max_op_count=300, step=75, num_calls=900, variant=16  # 5 points
)

SWAP1_CONFIG = CustomTargetConfig(
    name="SWAP1", max_op_count=300, step=75, num_calls=250, variant=1  # 5 points
)
SWAP8_CONFIG = CustomTargetConfig(
    name="SWAP8", max_op_count=300, step=75, num_calls=750, variant=8  # 5 points
)
SWAP16_CONFIG = CustomTargetConfig(
    name="SWAP16", max_op_count=300, step=75, num_calls=750, variant=16  # 5 points
)

LOG0_CONFIG = MarginalOpcodeConfig(
    name="LOG0",
    opcode=Op.LOG0,
    max_op_count=100,
    step=25,  # 5 data points
    stack_args=[0, 32],  # offset, size
    inputs_per_op=2,
    outputs_per_op=0,
    num_calls=150,
    setup_code=Op.MSTORE(0, MAX_U256),  # Fill memory with data to log
)
LOG1_CONFIG = MarginalOpcodeConfig(
    name="LOG1",
    opcode=Op.LOG1,
    max_op_count=80,
    step=20,  # 5 data points
    stack_args=[0, 32, 0xFF],  # offset, size, topic0
    inputs_per_op=3,
    outputs_per_op=0,
    num_calls=125,
    setup_code=Op.MSTORE(0, MAX_U256),
)
LOG2_CONFIG = MarginalOpcodeConfig(
    name="LOG2",
    opcode=Op.LOG2,
    max_op_count=60,
    step=15,  # 5 data points
    stack_args=[0, 32, 0xFF, 0xFF],  # offset, size, topic0, topic1
    inputs_per_op=4,
    outputs_per_op=0,
    num_calls=130,
    setup_code=Op.MSTORE(0, MAX_U256),
)
LOG3_CONFIG = MarginalOpcodeConfig(
    name="LOG3",
    opcode=Op.LOG3,
    max_op_count=40,
    step=10,  # 5 data points
    stack_args=[0, 32, 0xFF, 0xFF, 0xFF],  # offset, size, topic0, topic1, topic2
    inputs_per_op=5,
    outputs_per_op=0,
    num_calls=90,
    setup_code=Op.MSTORE(0, MAX_U256),
)
LOG4_CONFIG = MarginalOpcodeConfig(
    name="LOG4",
    opcode=Op.LOG4,
    max_op_count=40,
    step=10,  # 5 data points
    stack_args=[0, 32, 0xFF, 0xFF, 0xFF, 0xFF],  # offset, size, topic0-3
    inputs_per_op=6,
    outputs_per_op=0,
    num_calls=90,
    setup_code=Op.MSTORE(0, MAX_U256),
)

JUMP_CONFIG = CustomTargetConfig(
    name="JUMP", max_op_count=200, step=50, num_calls=1250  # 5 points
)
JUMPI_CONFIG = CustomTargetConfig(
    name="JUMPI", max_op_count=200, step=50, num_calls=800  # 5 points
)

# ============================================================================
# ENVIRONMENT OPCODES - Return context/environment info (no input, push 1)
# ============================================================================

ADDRESS_CONFIG = MarginalOpcodeConfig(
    name="ADDRESS",
    opcode=Op.ADDRESS,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],  # No input
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=400,
)

ORIGIN_CONFIG = MarginalOpcodeConfig(
    name="ORIGIN",
    opcode=Op.ORIGIN,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=250,
)

CALLER_CONFIG = MarginalOpcodeConfig(
    name="CALLER",
    opcode=Op.CALLER,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=400,
)

CALLVALUE_CONFIG = MarginalOpcodeConfig(
    name="CALLVALUE",
    opcode=Op.CALLVALUE,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=250,
)

CALLDATASIZE_CONFIG = MarginalOpcodeConfig(
    name="CALLDATASIZE",
    opcode=Op.CALLDATASIZE,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=500,
)

CODESIZE_CONFIG = MarginalOpcodeConfig(
    name="CODESIZE",
    opcode=Op.CODESIZE,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=300,
)

GASPRICE_CONFIG = MarginalOpcodeConfig(
    name="GASPRICE",
    opcode=Op.GASPRICE,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=450,
)

RETURNDATASIZE_CONFIG = MarginalOpcodeConfig(
    name="RETURNDATASIZE",
    opcode=Op.RETURNDATASIZE,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=300,
)

GAS_CONFIG = MarginalOpcodeConfig(
    name="GAS",
    opcode=Op.GAS,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=300,
)

# ============================================================================
# BLOCK INFO OPCODES - Return block context (no input, push 1)
# ============================================================================

COINBASE_CONFIG = MarginalOpcodeConfig(
    name="COINBASE",
    opcode=Op.COINBASE,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=350,
)

TIMESTAMP_CONFIG = MarginalOpcodeConfig(
    name="TIMESTAMP",
    opcode=Op.TIMESTAMP,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=500,
)

NUMBER_CONFIG = MarginalOpcodeConfig(
    name="NUMBER",
    opcode=Op.NUMBER,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=300,
)

PREVRANDAO_CONFIG = MarginalOpcodeConfig(
    name="PREVRANDAO",
    opcode=Op.PREVRANDAO,  # Was DIFFICULTY pre-merge
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=100,
)

GASLIMIT_CONFIG = MarginalOpcodeConfig(
    name="GASLIMIT",
    opcode=Op.GASLIMIT,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=300,
)

CHAINID_CONFIG = MarginalOpcodeConfig(
    name="CHAINID",
    opcode=Op.CHAINID,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=300,
)

SELFBALANCE_CONFIG = MarginalOpcodeConfig(
    name="SELFBALANCE",
    opcode=Op.SELFBALANCE,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=100,
)

BASEFEE_CONFIG = MarginalOpcodeConfig(
    name="BASEFEE",
    opcode=Op.BASEFEE,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=500,
)


BLOBBASEFEE_CONFIG = MarginalOpcodeConfig(
    name="BLOBBASEFEE",
    opcode=Op.BLOBBASEFEE,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=450,
)

# ============================================================================
# MEMORY OPCODES - Memory read/write operations
# ============================================================================

# Memory is pre-expanded via setup_code to avoid memory expansion costs in measurements

MLOAD_CONFIG = MarginalOpcodeConfig(
    name="MLOAD",
    opcode=Op.MLOAD,
    max_op_count=500,
    step=125,  # 5 data points
    stack_args=[0],  # offset - read from offset 0
    inputs_per_op=1,
    outputs_per_op=1,
    num_calls=250,
    setup_code=Op.MSTORE(0, MAX_U256),  # Pre-expand memory with data
)

MSTORE_CONFIG = MarginalOpcodeConfig(
    name="MSTORE",
    opcode=Op.MSTORE,
    max_op_count=500,
    step=125,  # 5 data points
    stack_args=[MAX_U256, 0],  # value, offset (MSTORE pops offset first)
    inputs_per_op=2,
    outputs_per_op=0,
    num_calls=300,
    setup_code=Op.MSTORE(0, 0),  # Pre-expand memory
)

MSTORE8_CONFIG = MarginalOpcodeConfig(
    name="MSTORE8",
    opcode=Op.MSTORE8,
    max_op_count=500,
    step=125,  # 5 data points
    stack_args=[0xFF, 0],  # value, offset (MSTORE8 pops offset first)
    inputs_per_op=2,
    outputs_per_op=0,
    num_calls=250,
    setup_code=Op.MSTORE(0, 0),  # Pre-expand memory
)

MSIZE_CONFIG = MarginalOpcodeConfig(
    name="MSIZE",
    opcode=Op.MSIZE,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=250,
    setup_code=Op.MSTORE(0, 0),  # Pre-expand memory so MSIZE returns non-zero
)

# CALLDATACOPY: destOffset, offset, size (copies from calldata to memory)
# Use 32 bytes for worst-case cycles/gas (smaller size = higher zkVM overhead per gas)
CALLDATACOPY_CONFIG = MarginalOpcodeConfig(
    name="CALLDATACOPY",
    opcode=Op.CALLDATACOPY,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[32, 0, 0],  # size=32 bytes, offset=0, destOffset=0 (worst-case: small copy)
    inputs_per_op=3,
    outputs_per_op=0,
    num_calls=400,
    setup_code=Op.MSTORE(0, 0),  # Pre-expand memory
)


def _generate_returndatacopy_setup() -> Bytecode:
    """
    Generate setup code for RETURNDATACOPY.
    We need to make a call first to populate RETURNDATA.
    Uses STATICCALL to the IDENTITY precompile (0x04) with 64 bytes of data.
    """
    code = Bytecode()
    # Store 64 bytes of data in memory for the call
    code += Op.MSTORE(0, MAX_U256)
    code += Op.MSTORE(32, MAX_U256)
    # STATICCALL(gas, addr, argsOffset, argsSize, retOffset, retSize)
    # Call IDENTITY precompile with 64 bytes input, store 64 bytes output at offset 64
    code += Op.POP(Op.STATICCALL(Op.GAS, 0x04, 0, 64, 64, 64))
    return code


# RETURNDATACOPY: destOffset, offset, size (copies from return data to memory)
# Note: Requires a prior call to populate RETURNDATA
# Setup calls IDENTITY precompile to fill RETURNDATA buffer
# Gas per op = 3 + 3 * ceil(64/32) = 9 gas
RETURNDATACOPY_CONFIG = MarginalOpcodeConfig(
    name="RETURNDATACOPY",
    opcode=Op.RETURNDATACOPY,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[64, 0, 128],  # size=64, offset=0, destOffset=128
    inputs_per_op=3,
    outputs_per_op=0,
    num_calls=350,
    setup_code=_generate_returndatacopy_setup(),
)

# CODECOPY: destOffset, offset, size (copies from code to memory)
# Use 32 bytes for worst-case cycles/gas (smaller size = higher zkVM overhead per gas)
CODECOPY_CONFIG = MarginalOpcodeConfig(
    name="CODECOPY",
    opcode=Op.CODECOPY,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[32, 0, 0],  # size=32 bytes, offset=0, destOffset=0 (worst-case: small copy)
    inputs_per_op=3,
    outputs_per_op=0,
    num_calls=200,
    setup_code=Op.MSTORE(0, 0),  # Pre-expand memory
)

# MCOPY: destOffset, srcOffset, size (copies within memory) - EIP-5656
MCOPY_CONFIG = MarginalOpcodeConfig(
    name="MCOPY",
    opcode=Op.MCOPY,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[1024, 0, 4096],  # size=1KB, srcOffset=0, destOffset=4096
    inputs_per_op=3,
    outputs_per_op=0,
    num_calls=50,
    setup_code=Op.MSTORE(0, MAX_U256) + Op.MSTORE(4096, 0),  # Pre-expand memory regions
)

# ============================================================================
# DATA ACCESS OPCODES
# ============================================================================

# CALLDATALOAD: pops offset, pushes 32 bytes from calldata
CALLDATALOAD_CONFIG = MarginalOpcodeConfig(
    name="CALLDATALOAD",
    opcode=Op.CALLDATALOAD,
    max_op_count=500,
    step=125,  # 5 data points
    stack_args=[0],  # Load from offset 0
    inputs_per_op=1,
    outputs_per_op=1,
    num_calls=150,
)

# BLOCKHASH: pops block number, pushes hash (or 0 if out of range)
BLOCKHASH_CONFIG = MarginalOpcodeConfig(
    name="BLOCKHASH",
    opcode=Op.BLOCKHASH,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[0],  # Block 0
    inputs_per_op=1,
    outputs_per_op=1,
    num_calls=250,
)

# BLOBHASH: pops blob index, pushes versioned hash (or 0 if out of range)
BLOBHASH_CONFIG = MarginalOpcodeConfig(
    name="BLOBHASH",
    opcode=Op.BLOBHASH,
    max_op_count=500,
    step=125,  # 5 data points
    stack_args=[0],  # Blob index 0 (will return 0 if no blobs)
    inputs_per_op=1,
    outputs_per_op=1,
    num_calls=400,
)

# ============================================================================
# STORAGE OPCODES - SLOAD, SSTORE, TLOAD, TSTORE
# ============================================================================

# SLOAD: First access to cold slot costs 2100 gas, warm access costs 100 gas
# For marginal testing, we warm up the slot first to measure consistent warm access cost
SLOAD_CONFIG = MarginalOpcodeConfig(
    name="SLOAD",
    opcode=Op.SLOAD,
    max_op_count=100,
    step=25,  # 5 data points
    stack_args=[100],  # Storage slot 100 (different from SUCCESS_SLOT)
    inputs_per_op=1,
    outputs_per_op=1,
    num_calls=150,
    setup_code=Op.POP(Op.SLOAD(100)),  # Warm up slot 100 first
)

# SSTORE: Complex gas rules (cold access, dirty/clean, refunds)
# Slot 100, value MAX_U256 - repeated writes to same slot
# Note: SSTORE pops slot first, then value, so push order is [value, slot]
# We warm up the slot first by doing an SLOAD to get consistent warm access cost
SSTORE_CONFIG = MarginalOpcodeConfig(
    name="SSTORE",
    opcode=Op.SSTORE,
    max_op_count=40,
    step=10,  # 5 data points
    stack_args=[MAX_U256, 100],  # value, slot (SSTORE pops slot first)
    inputs_per_op=2,
    outputs_per_op=0,
    num_calls=100,
    setup_code=Op.POP(Op.SLOAD(100)),  # Warm up slot 100 first
)

# TLOAD: Transient storage load (EIP-1153) - 100 gas
TLOAD_CONFIG = MarginalOpcodeConfig(
    name="TLOAD",
    opcode=Op.TLOAD,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[0],  # Transient slot 0
    inputs_per_op=1,
    outputs_per_op=1,
    num_calls=300,
)

# TSTORE: Transient storage store (EIP-1153) - 100 gas
# Note: TSTORE pops slot first, then value, so push order is [value, slot]
TSTORE_CONFIG = MarginalOpcodeConfig(
    name="TSTORE",
    opcode=Op.TSTORE,
    max_op_count=100,
    step=25,  # 5 data points
    stack_args=[MAX_U256, 0],  # value, slot (TSTORE pops slot first)
    inputs_per_op=2,
    outputs_per_op=0,
    num_calls=150,
)

# ============================================================================
# CONTROL FLOW OPCODES
# ============================================================================

# JUMPDEST is just a marker (1 gas) - essentially a no-op
# Note: JUMPDEST has outputs_per_op=0, inputs_per_op=0, so uses noop-padding
# which doesn't add any overhead - each JUMPDEST just costs 1 gas
JUMPDEST_CONFIG = MarginalOpcodeConfig(
    name="JUMPDEST",
    opcode=Op.JUMPDEST,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=0,
    num_calls=1950,
)

# PC pushes the program counter value
PC_CONFIG = MarginalOpcodeConfig(
    name="PC",
    opcode=Op.PC,
    max_op_count=600,
    step=150,  # 5 data points
    stack_args=[],
    inputs_per_op=0,
    outputs_per_op=1,
    num_calls=500,
)

# ============================================================================
# EXTERNAL ACCOUNT OPCODES - BALANCE, EXTCODESIZE, EXTCODEHASH, EXTCODECOPY
# These have cold/warm access patterns like storage
# ============================================================================

# BALANCE: pops address, pushes balance
# Cold access: 2600 gas, warm access: 100 gas
# Warm up the target address first for consistent marginal measurement
BALANCE_CONFIG = MarginalOpcodeConfig(
    name="BALANCE",
    opcode=Op.BALANCE,
    max_op_count=300,
    step=75,  # 5 data points
    stack_args=[0xDEAD],  # Query balance of address 0xDEAD
    inputs_per_op=1,
    outputs_per_op=1,
    num_calls=100,
    setup_code=Op.POP(Op.BALANCE(0xDEAD)),  # Warm up address 0xDEAD first
)

# EXTCODESIZE: pops address, pushes code size
# Cold access: 2600 gas, warm access: 100 gas
# Warm up the target address first for consistent marginal measurement
EXTCODESIZE_CONFIG = MarginalOpcodeConfig(
    name="EXTCODESIZE",
    opcode=Op.EXTCODESIZE,
    max_op_count=100,
    step=25,  # 5 data points
    stack_args=[0xDEAD],  # Query code size of address 0xDEAD
    inputs_per_op=1,
    outputs_per_op=1,
    num_calls=150,
    setup_code=Op.POP(Op.EXTCODESIZE(0xDEAD)),  # Warm up address 0xDEAD first
)

# EXTCODEHASH: pops address, pushes code hash
# Cold access: 2600 gas, warm access: 100 gas
# Warm up the target address first for consistent marginal measurement
EXTCODEHASH_CONFIG = MarginalOpcodeConfig(
    name="EXTCODEHASH",
    opcode=Op.EXTCODEHASH,
    max_op_count=100,
    step=25,  # 5 data points
    stack_args=[0xDEAD],  # Query code hash of address 0xDEAD
    inputs_per_op=1,
    outputs_per_op=1,
    num_calls=150,
    setup_code=Op.POP(Op.EXTCODEHASH(0xDEAD)),  # Warm up address 0xDEAD first
)

# EXTCODECOPY: address, destOffset, offset, size (4 args, copies external code to memory)
# Warm up both memory and target address for consistent marginal measurement
EXTCODECOPY_CONFIG = MarginalOpcodeConfig(
    name="EXTCODECOPY",
    opcode=Op.EXTCODECOPY,
    max_op_count=40,
    step=10,  # 5 data points
    stack_args=[256, 0, 0, 0xDEAD],  # size=256, offset=0, destOffset=0, address
    inputs_per_op=4,
    outputs_per_op=0,
    num_calls=150,
    setup_code=Op.MSTORE(0, 0) + Op.POP(Op.EXTCODESIZE(0xDEAD)),  # Pre-expand memory + warm up address
)


def push_value(value: int) -> Bytecode:
    """Generate appropriate PUSH opcode for a value based on its size."""
    if value == 0:
        return Op.PUSH0
    # Calculate byte length needed
    byte_len = (value.bit_length() + 7) // 8
    if byte_len <= 1:
        return Op.PUSH1(value)
    elif byte_len <= 2:
        return Op.PUSH2(value)
    elif byte_len <= 4:
        return Op.PUSH4(value)
    elif byte_len <= 8:
        return Op.PUSH8(value)
    elif byte_len <= 16:
        return Op.PUSH16(value)
    else:
        return Op.PUSH32(value)


def generate_op_counts(max_op_count: int, step: int) -> List[int]:
    """Generate list of op_counts from 0 to max_op_count with given step.

    IMPORTANT: max_op_count must be divisible by step to ensure evenly spaced points.
    """
    counts = list(range(0, max_op_count + 1, step))
    assert counts[-1] == max_op_count, (
        f"max_op_count={max_op_count} must be divisible by step={step}. "
        f"Got {len(counts)} points ending at {counts[-1]} instead of {max_op_count}"
    )
    return counts


# ============================================================================
# AMPLIFIER-TARGET APPROACH
# ============================================================================
# The amplifier-target pattern amplifies op_count by having an amplifier contract
# call a target contract N times. This allows much higher effective op_counts
# while keeping individual contract sizes within limits.
#
# Effective op_count = num_calls × op_count_per_call
#
# Each opcode has its own num_calls value calculated to achieve >= 500K max gas.
# ============================================================================

# Legacy constant for backward compatibility (new tests use config.num_calls)
NUM_CALLS = 100
AMPLIFIER_GAS_LIMIT = 500_000_000  # High gas limit for scaled benchmarking (500M)


def generate_target_contract_code(
    config: MarginalOpcodeConfig,
    op_count: int,
) -> Bytecode:
    """
    Generate a target contract for amplifier-target approach.

    Uses the same marginal testing strategies (POP-based or noop-based padding)
    but WITHOUT SSTORE (since it's called via CALL from amplifier). Just ends with STOP.
    """
    assert 0 <= op_count <= config.max_op_count

    code = Bytecode()

    # 1. Optional setup code (e.g., memory initialization)
    if config.setup_code is not None:
        code += config.setup_code

    if config.outputs_per_op > 0:
        # Strategy 1: POP-based padding for opcodes that push results onto stack.
        # Interleave POPs to consume results and prevent stack overflow.
        # This applies to PUSH, arithmetic ops (ADD, MUL, etc.), and others.
        total_result_pops = config.max_op_count * config.outputs_per_op
        for _ in range(total_result_pops):
            code += Op.PUSH0

        for _ in range(config.max_op_count):
            for arg in config.stack_args:
                code += push_value(arg)

        if op_count == 0:
            for _ in range(total_result_pops):
                code += Op.POP
        else:
            code += config.opcode
            interleaved_count = op_count - 1
            for _ in range(interleaved_count):
                for _ in range(config.outputs_per_op):
                    code += Op.POP
                code += config.opcode
            end_pops = total_result_pops - interleaved_count * config.outputs_per_op
            for _ in range(end_pops):
                code += Op.POP
    else:
        # Strategy 2: Noop-based padding for non-returning opcodes
        for _ in range(op_count):
            for arg in config.stack_args:
                code += push_value(arg)
            code += config.opcode

        noop_count = config.max_op_count - op_count
        for _ in range(noop_count):
            for arg in config.stack_args:
                code += push_value(arg)

    code += Op.STOP

    return code


def generate_amplifier_contract_code(target_address: Address, num_calls: int) -> Bytecode:
    """
    Generate amplifier contract that calls target num_calls times using a loop to
    amplify the op_count. The loop overhead is constant across all test variants,
    so it gets eliminated in the marginal cost regression.

    Structure:
        PUSH num_calls          ; Initialize counter
        JUMPDEST (loop_start)   ; Loop label
        CALL to target          ; Call target contract
        PUSH2 continue          ; Push continue offset
        JUMPI                   ; Jump if success (non-zero)
        REVERT                  ; Revert if call failed
        JUMPDEST (continue)     ; Continue if success
        PUSH 1                  ;
        SWAP1                   ;
        SUB                     ; counter -= 1
        DUP1                    ; Duplicate counter for check
        PUSH2 loop_start        ;
        JUMPI                   ; Jump if counter > 0
        POP                     ; Pop counter (now 0)
        SSTORE + STOP           ; Success marker
    """
    code = Bytecode()

    # Push loop counter (use appropriate PUSH based on num_calls size)
    if num_calls <= 0xFF:
        code += Op.PUSH1(num_calls)
    elif num_calls <= 0xFFFF:
        code += Op.PUSH2(num_calls)
    else:
        code += Op.PUSH3(num_calls)

    # Loop start - we need to calculate the offset for JUMPDEST
    # The PUSH for counter takes 2-4 bytes, JUMPDEST is at that offset
    loop_start_offset = len(bytes(code))
    code += Op.JUMPDEST

    # Call target contract (CALL: gas, addr, value, argsOffset, argsSize, retOffset, retSize)
    code += Op.PUSH1(0)                   # retSize
    code += Op.PUSH1(0)                   # retOffset
    code += Op.PUSH1(0)                   # argsSize
    code += Op.PUSH1(0)                   # argsOffset
    code += Op.PUSH1(0)                   # value (no ETH transfer)
    code += Op.PUSH20(target_address)     # address
    code += Op.GAS                        # gas (forward all)
    code += Op.CALL                       # Returns success flag on stack

    # Check success and revert if call failed
    current_pc = len(bytes(code))
    continue_offset = current_pc + 9      # PUSH2(3) + JUMPI(1) + PUSH1(2) + PUSH1(2) + REVERT(1)
    code += Op.PUSH2(continue_offset)     # Push continue offset
    code += Op.JUMPI                      # Jump if success (non-zero)
    # Revert path (only executed if CALL returned 0)
    code += Op.PUSH1(0)                   # revert data size
    code += Op.PUSH1(0)                   # revert data offset
    code += Op.REVERT                     # Revert immediately on failure
    code += Op.JUMPDEST                   # Continue path

    # Decrement counter: counter -= 1
    code += Op.PUSH1(1)
    code += Op.SWAP1
    code += Op.SUB

    # Check if counter > 0 and loop
    code += Op.DUP1                       # Duplicate counter for JUMPI check
    code += Op.PUSH2(loop_start_offset)   # Push loop start offset
    code += Op.JUMPI                      # Jump back if counter > 0

    # Counter is 0, pop it and write success marker
    code += Op.POP
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP

    return code


TargetGenerator = Callable[[int, int], Bytecode]
"""Target generator signature: (op_count, max_op_count) -> Bytecode."""

AmplifierGenerator = Callable[[Address, int], Bytecode]
"""Amplifier generator signature: (target_address, num_calls) -> Bytecode."""


def _create_amplifier_test(
    cfg: MarginalOpcodeConfig | CustomTargetConfig,
    target_generator: TargetGenerator | None = None,
):
    """
    Single factory for all amplifier-target marginal tests.

    - If cfg is MarginalOpcodeConfig: defaults to generate_target_contract_code(cfg, op_count)
    - If cfg is CustomTargetConfig: requires target_generator(op_count, max_op_count)
    """
    if isinstance(cfg, MarginalOpcodeConfig):
        max_op_count = cfg.max_op_count
        step = cfg.step
        num_calls = cfg.num_calls
        if target_generator is None:
            target_generator = lambda oc, _moc: generate_target_contract_code(cfg, oc)
    elif isinstance(cfg, CustomTargetConfig):
        max_op_count = cfg.max_op_count
        step = cfg.step
        num_calls = cfg.num_calls
        if target_generator is None:
            raise ValueError("CustomTargetConfig requires a target_generator")
    else:
        raise TypeError(f"Unsupported config type: {type(cfg)}")

    amplifier_gen: AmplifierGenerator = generate_amplifier_contract_code

    op_counts = generate_op_counts(max_op_count, step)

    @pytest.mark.valid_from("Prague")
    @pytest.mark.parametrize(
        "op_count",
        op_counts,
        ids=lambda x: f"op_count_{x * num_calls}",
    )
    def test_func(
        state_test: StateTestFiller,
        pre: Alloc,
        op_count: int,
    ) -> None:
        target_code = target_generator(op_count, max_op_count)
        target_contract = pre.deploy_contract(code=target_code)

        amplifier_code = amplifier_gen(target_contract, num_calls)
        amplifier_contract = pre.deploy_contract(code=amplifier_code)

        sender = pre.fund_eoa()

        tx = Transaction(
            to=amplifier_contract,
            gas_limit=AMPLIFIER_GAS_LIMIT,
            sender=sender,
        )

        post = {amplifier_contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}

        # Provide realistic block hashes for BLOCKHASH opcode
        # Generate hash for block 0 using keccak256
        block_hashes = {
            0: Bytes(b"block_0").keccak256(),
        }
        env = Environment(
            gas_limit=AMPLIFIER_GAS_LIMIT,
            block_hashes=block_hashes,
        )

        state_test(env=env, pre=pre, post=post, tx=tx)

    return test_func


# ============================================================================
# JUMP / JUMPI - Special handling required (control flow opcodes)
# These require custom target generators since they change control flow.
# We use a loop-based approach where we control the iteration count.
# ============================================================================

def generate_jump_target(op_count: int, max_op_count: int) -> Bytecode:
    """
    Generate JUMP target contract for amplifier-target approach.
    No SSTORE (called via CALL from amplifier).
    """
    code = Bytecode()

    for i in range(max_op_count):
        current_pc = len(bytes(code))

        if i < op_count:
            # Real combo: PUSH3(dest) + JUMP + JUMPDEST = 6 bytes
            jumpdest_pc = current_pc + 1 + 3 + 1
            code += Op.PUSH3(jumpdest_pc)
            code += Op.JUMP
            code += Op.JUMPDEST
        else:
            # Noop combo: PUSH3(dest) + JUMPDEST = 5 bytes
            jumpdest_pc = current_pc + 1 + 3
            code += Op.PUSH3(jumpdest_pc)
            code += Op.JUMPDEST

    # Just STOP (no SSTORE - called via CALL from amplifier)
    code += Op.STOP

    return code


def generate_jumpi_target(op_count: int, max_op_count: int) -> Bytecode:
    """
    Generate JUMPI target contract for amplifier-target approach.
    No SSTORE (called via CALL from amplifier).
    """
    code = Bytecode()

    # Push max_op_count conditions upfront
    for _ in range(max_op_count):
        code += Op.PUSH1(1)  # Push true condition

    for i in range(max_op_count):
        current_pc = len(bytes(code))

        if i < op_count:
            # Real combo: PUSH3(dest) + JUMPI + JUMPDEST = 6 bytes
            jumpdest_pc = current_pc + 1 + 3 + 1
            code += Op.PUSH3(jumpdest_pc)
            code += Op.JUMPI
            code += Op.JUMPDEST
        else:
            # Noop combo: PUSH3(dest) + JUMPDEST = 5 bytes
            jumpdest_pc = current_pc + 1 + 3
            code += Op.PUSH3(jumpdest_pc)
            code += Op.JUMPDEST

    # Just STOP (no SSTORE - called via CALL from amplifier)
    code += Op.STOP

    return code


# ============================================================================
# CALL-FAMILY OPCODES - Using loop-based amplifier contract approach
# CALL, CALLCODE, DELEGATECALL, STATICCALL
# ============================================================================
# Special handling required: CALL opcodes need dynamic arguments (deployed contract
# address via Op.PUSH20(inner_target) and current gas via Op.GAS) that can't be
# represented as constants in MarginalOpcodeConfig.stack_args.

# Configuration for CALL-family opcodes with simplified noop approach
# Stack-limited but amplifier-amplified for high total op counts
# Stack limit: 1024, each noop leaves +5 or +6 items
# Safe max_op_count: ~150 (with buffer), amplifier amplifies to 150 × N total ops
CALL_NUM_CALLS = 75
CALL_MAX_OP_COUNT = 100  # Target contract executes up to 100 CALLs per invocation
CALL_STEP = 25  # 5 data points


def _generate_target_with_inner_calls(
    inner_target: Address, op_count: int, max_op_count: int, call_op
) -> Bytecode:
    """
    Generate a target contract that makes op_count calls to inner_target,
    with simplified noop padding to ensure perfect marginal property.
    - Noops: Push args + POP one (stack accumulates, but no call)
    - Real calls: Push args + CALL + POP result
    """
    code = Bytecode()

    # Calculate noop count
    noop_count = max_op_count - op_count

    # Determine arg count based on call type
    if call_op in (Op.CALL, Op.CALLCODE):
        args_count = 7  # gas, addr, value, argsOffset, argsSize, retOffset, retSize
    else:
        args_count = 6  # gas, addr, argsOffset, argsSize, retOffset, retSize

    # ========== NOOPS (push args + pop one, stack accumulates) ==========
    for _ in range(noop_count):
        # Push same arguments as real call
        if call_op in (Op.CALL, Op.CALLCODE):
            code += Op.PUSH1(0)                   # retSize
            code += Op.PUSH1(0)                   # retOffset
            code += Op.PUSH1(0)                   # argsSize
            code += Op.PUSH1(0)                   # argsOffset
            code += Op.PUSH1(0)                   # value
            code += Op.PUSH20(inner_target)       # address
            code += Op.GAS                        # gas
        else:
            code += Op.PUSH1(0)                   # retSize
            code += Op.PUSH1(0)                   # retOffset
            code += Op.PUSH1(0)                   # argsSize
            code += Op.PUSH1(0)                   # argsOffset
            code += Op.PUSH20(inner_target)       # address
            code += Op.GAS                        # gas

        # Just pop one item - NO call, stack accumulates
        code += Op.POP

    # ========== REAL CALLS (push args + call + pop result) ==========
    for _ in range(op_count):
        if call_op in (Op.CALL, Op.CALLCODE):
            code += Op.PUSH1(0)                   # retSize
            code += Op.PUSH1(0)                   # retOffset
            code += Op.PUSH1(0)                   # argsSize
            code += Op.PUSH1(0)                   # argsOffset
            code += Op.PUSH1(0)                   # value
            code += Op.PUSH20(inner_target)       # address
            code += Op.GAS                        # gas
            code += call_op                       # CALL/CALLCODE
        else:
            code += Op.PUSH1(0)                   # retSize
            code += Op.PUSH1(0)                   # retOffset
            code += Op.PUSH1(0)                   # argsSize
            code += Op.PUSH1(0)                   # argsOffset
            code += Op.PUSH20(inner_target)       # address
            code += Op.GAS                        # gas
            code += call_op                       # STATICCALL/DELEGATECALL

        code += Op.POP  # pop success flag

    code += Op.STOP
    return code


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALL_MAX_OP_COUNT, CALL_STEP),
    ids=lambda x: f"op_count_{x * CALL_NUM_CALLS}",
)
def test_marginal_call(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CALL opcode using loop-based amplifier."""
    # Inner target: just stops
    inner_target = pre.deploy_contract(code=Op.STOP)

    # Target contract: makes op_count CALLs to inner_target per invocation
    # With noop padding for proper marginality
    target_code = _generate_target_with_inner_calls(
        inner_target, op_count, CALL_MAX_OP_COUNT, Op.CALL
    )
    target = pre.deploy_contract(code=target_code)

    # Amplifier contract: loops CALL_NUM_CALLS times, calling target
    amplifier_code = generate_amplifier_contract_code(target, CALL_NUM_CALLS)
    amplifier = pre.deploy_contract(code=amplifier_code)

    sender = pre.fund_eoa()
    tx = Transaction(to=amplifier, gas_limit=AMPLIFIER_GAS_LIMIT, sender=sender)
    post = {amplifier: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(gas_limit=AMPLIFIER_GAS_LIMIT), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALL_MAX_OP_COUNT, CALL_STEP),
    ids=lambda x: f"op_count_{x * CALL_NUM_CALLS}",
)
def test_marginal_callcode(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CALLCODE opcode using loop-based amplifier."""
    inner_target = pre.deploy_contract(code=Op.STOP)
    # With noop padding for proper marginality
    target_code = _generate_target_with_inner_calls(
        inner_target, op_count, CALL_MAX_OP_COUNT, Op.CALLCODE
    )
    target = pre.deploy_contract(code=target_code)
    amplifier_code = generate_amplifier_contract_code(target, CALL_NUM_CALLS)
    amplifier = pre.deploy_contract(code=amplifier_code)

    sender = pre.fund_eoa()
    tx = Transaction(to=amplifier, gas_limit=AMPLIFIER_GAS_LIMIT, sender=sender)
    post = {amplifier: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(gas_limit=AMPLIFIER_GAS_LIMIT), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALL_MAX_OP_COUNT, CALL_STEP),
    ids=lambda x: f"op_count_{x * CALL_NUM_CALLS}",
)
def test_marginal_delegatecall(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for DELEGATECALL opcode using loop-based amplifier."""
    inner_target = pre.deploy_contract(code=Op.STOP)
    # With noop padding for proper marginality
    target_code = _generate_target_with_inner_calls(
        inner_target, op_count, CALL_MAX_OP_COUNT, Op.DELEGATECALL
    )
    target = pre.deploy_contract(code=target_code)
    amplifier_code = generate_amplifier_contract_code(target, CALL_NUM_CALLS)
    amplifier = pre.deploy_contract(code=amplifier_code)

    sender = pre.fund_eoa()
    tx = Transaction(to=amplifier, gas_limit=AMPLIFIER_GAS_LIMIT, sender=sender)
    post = {amplifier: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(gas_limit=AMPLIFIER_GAS_LIMIT), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALL_MAX_OP_COUNT, CALL_STEP),
    ids=lambda x: f"op_count_{x * CALL_NUM_CALLS}",
)
def test_marginal_staticcall(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for STATICCALL opcode using loop-based amplifier."""
    inner_target = pre.deploy_contract(code=Op.STOP)
    # With noop padding for proper marginality
    target_code = _generate_target_with_inner_calls(
        inner_target, op_count, CALL_MAX_OP_COUNT, Op.STATICCALL
    )
    target = pre.deploy_contract(code=target_code)
    amplifier_code = generate_amplifier_contract_code(target, CALL_NUM_CALLS)
    amplifier = pre.deploy_contract(code=amplifier_code)

    sender = pre.fund_eoa()
    tx = Transaction(to=amplifier, gas_limit=AMPLIFIER_GAS_LIMIT, sender=sender)
    post = {amplifier: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(gas_limit=AMPLIFIER_GAS_LIMIT), pre=pre, post=post, tx=tx)


# ============================================================================
# CREATE OPCODES - CREATE, CREATE2 (simplified noop approach)
# These deploy new contracts
# ============================================================================

# For CREATE: Each call to target increments nonce, so each CREATE gets unique address
# For CREATE2: We use a storage counter as salt to generate unique addresses

# Stack-limited: each noop leaves +2 items (3 pushed, 1 popped)
# Safe max_op_count: ~400 (with buffer), amplifier amplifies total
CREATE_NUM_CALLS = 50
CREATE_MAX_OP_COUNT = 20  # Target executes up to 20 CREATEs per call
CREATE_STEP = 5  # 5 data points


def _generate_target_with_creates(op_count: int, max_op_count: int) -> Bytecode:
    """
    Generate a target contract that executes op_count CREATE operations,
    with simplified noop padding to ensure perfect marginal property.
    - Noops: Push 3 args + POP one (stack accumulates, but no CREATE)
    - Real calls: Push 3 args + CREATE + POP result
    """
    code = Bytecode()

    # Store minimal initcode in memory: 0x600080f3 (PUSH1 0, DUP1, RETURN)
    code += Op.MSTORE(0, 0x600080f3 << (28 * 8))

    noop_count = max_op_count - op_count

    # ========== NOOPS (push args + pop one, stack accumulates) ==========
    for _ in range(noop_count):
        # Push same arguments as real CREATE
        code += Op.PUSH1(4)                   # size
        code += Op.PUSH1(0)                   # offset
        code += Op.PUSH1(0)                   # value
        # Just pop one item - NO CREATE, stack accumulates
        code += Op.POP

    # ========== REAL CREATEs (push args + CREATE + pop result) ==========
    for _ in range(op_count):
        code += Op.PUSH1(4)                   # size
        code += Op.PUSH1(0)                   # offset
        code += Op.PUSH1(0)                   # value
        code += Op.CREATE                     # CREATE(value, offset, size) -> address
        code += Op.POP                        # pop created address

    code += Op.STOP
    return code


def _generate_target_with_create2s(op_count: int, max_op_count: int) -> Bytecode:
    """
    Generate a target contract that executes op_count CREATE2 operations,
    with noop padding to ensure perfect marginal property.

    Key insight: Load salt AFTER noops so it sits on top of accumulated junk,
    making it accessible via DUP1 for real CREATE2s.

    Structure:
    - Noops first
    - Real CREATE2s
    """
    code = Bytecode()

    # Store minimal initcode in memory
    code += Op.MSTORE(0, 0x600080f3 << (28 * 8))

    salt_slot = 0x100
    noop_count = max_op_count - op_count

    # ========== NOOPS FIRST ==========
    for i in range(noop_count):
        code += Op.PUSH2(0)                   # dummy base (3 gas, same as DUP1)
        code += Op.PUSH2(i)                   # add offset (same as real)
        code += Op.ADD                        # calculate dummy salt (same overhead)
        code += Op.PUSH1(4)                   # size
        code += Op.PUSH1(0)                   # offset
        code += Op.PUSH1(0)                   # value
        # Pop calculated value (no CREATE2)
        code += Op.POP                        # leaves 3 args on stack

    # ========== LOAD SALT ==========
    code += Op.SLOAD(salt_slot)

    # ========== REAL CREATE2s ==========
    for i in range(op_count):
        code += Op.DUP1                       # duplicate salt
        code += Op.PUSH2(noop_count + i)      # add offset for unique salt
        code += Op.ADD                        # salt = counter + i
        code += Op.PUSH1(4)                   # size
        code += Op.PUSH1(0)                   # offset
        code += Op.PUSH1(0)                   # value
        code += Op.CREATE2                    # CREATE2(value, offset, size, salt) -> address
        code += Op.POP                        # pop created address

    # Update salt counter (still on stack)
    code += Op.PUSH2(max_op_count)
    code += Op.ADD                            # new counter = old + max_op_count
    code += Op.PUSH2(salt_slot)
    code += Op.SSTORE                         # save updated counter

    code += Op.STOP
    return code


# ============================================================================
# DUP/SWAP TARGET GENERATORS
# ============================================================================


def generate_dup_target(dup_n: int, op_count: int, max_op_count: int) -> Bytecode:
    """
    Generate DUP target with CONSTANT overhead (true marginal).

    Following gas-cost-estimator's approach:
    - TOTAL PUSHES = constant (max_op_count empty + dup_n initial)
    - TOTAL POPS = constant (max_op_count for DUP results + dup_n for cleanup)
    - Only DUP count varies

    Pattern:
      1. Pre-push max_op_count zeros (CONSTANT)
      2. Push dup_n values (CONSTANT)
      3. DUP + (POP + DUP)*(op_count-1) - op_count DUPs with interleaved POPs
      4. End POPs to reach constant total
      5. Pop dup_n initial values (CONSTANT)

    Gas calculation:
      op_count=0:  constant pushes + 0 DUPs + constant pops
      op_count=N:  constant pushes + N DUPs + constant pops
      Marginal = N*3 / N = 3 gas per DUP ✓
    """
    code = Bytecode()

    # 1. ALWAYS pre-push max_op_count zeros (CONSTANT overhead)
    for _ in range(max_op_count):
        code += Op.PUSH0

    # 2. ALWAYS push dup_n initial values (CONSTANT overhead)
    for i in range(dup_n):
        code += Op.PUSH1[i]

    # 3. Execute DUP operations with interleaved POPs
    # Pattern: DUP + (POP + DUP) * (op_count-1)
    interleaved_pops = max(op_count - 1, 0)
    dup_opcode = getattr(Op, f"DUP{dup_n}")
    if op_count >= 1:
        code += dup_opcode  # First DUP
        for _ in range(interleaved_pops):
            code += Op.POP
            code += dup_opcode

    # 4. End POPs = max_op_count - interleaved_pops (to reach CONSTANT total)
    end_pops = max_op_count - interleaved_pops
    for _ in range(end_pops):
        code += Op.POP

    # 5. ALWAYS pop dup_n initial values (CONSTANT overhead)
    for _ in range(dup_n):
        code += Op.POP

    code += Op.STOP
    return code


def generate_swap_target(swap_n: int, op_count: int, max_op_count: int) -> Bytecode:
    """Generate SWAP target for amplifier (no SSTORE, just STOP)."""
    code = Bytecode()

    # Push swap_n+1 initial values
    for i in range(swap_n + 1):
        code += Op.PUSH1[i]

    # Execute op_count SWAP operations
    swap_opcode = getattr(Op, f"SWAP{swap_n}")
    for _ in range(op_count):
        code += swap_opcode

    # Pop the initial values
    for _ in range(swap_n + 1):
        code += Op.POP

    code += Op.STOP
    return code


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CREATE_MAX_OP_COUNT, CREATE_STEP),
    ids=lambda x: f"op_count_{x * CREATE_NUM_CALLS}",
)
def test_marginal_create(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CREATE opcode using loop-based amplifier."""
    # Target contract executes op_count CREATEs per call
    # With noop padding for proper marginality
    target_code = _generate_target_with_creates(op_count, CREATE_MAX_OP_COUNT)
    target = pre.deploy_contract(code=target_code)

    # Amplifier loops CREATE_NUM_CALLS times, calling target
    amplifier_code = generate_amplifier_contract_code(target, CREATE_NUM_CALLS)
    amplifier = pre.deploy_contract(code=amplifier_code)

    sender = pre.fund_eoa()
    tx = Transaction(to=amplifier, gas_limit=AMPLIFIER_GAS_LIMIT, sender=sender)
    post = {amplifier: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(gas_limit=AMPLIFIER_GAS_LIMIT), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CREATE_MAX_OP_COUNT, CREATE_STEP),
    ids=lambda x: f"op_count_{x * CREATE_NUM_CALLS}",
)
def test_marginal_create2(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CREATE2 opcode using loop-based amplifier."""
    # Target contract executes op_count CREATE2s per call with unique salts
    # With noop padding for proper marginality
    target_code = _generate_target_with_create2s(op_count, CREATE_MAX_OP_COUNT)
    target = pre.deploy_contract(code=target_code)

    # Amplifier loops CREATE_NUM_CALLS times, calling target
    amplifier_code = generate_amplifier_contract_code(target, CREATE_NUM_CALLS)
    amplifier = pre.deploy_contract(code=amplifier_code)

    sender = pre.fund_eoa()
    tx = Transaction(to=amplifier, gas_limit=AMPLIFIER_GAS_LIMIT, sender=sender)
    post = {amplifier: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(gas_limit=AMPLIFIER_GAS_LIMIT), pre=pre, post=post, tx=tx)


# ============================================================================
# AMPLIFIER-TARGET TESTS FOR LOW-GAS OPCODES
# ============================================================================
# These use the amplifier-target approach to amplify effective op_count.
# Effective op_count = NUM_CALLS × op_count_per_call
#
# This is useful for opcodes with low gas costs where single-contract tests
# don't provide enough gas variation for meaningful linear regression.
# ============================================================================

# Arithmetic opcodes
test_add = _create_amplifier_test(ADD_CONFIG)
test_sub = _create_amplifier_test(SUB_CONFIG)
test_mul = _create_amplifier_test(MUL_CONFIG)
test_div = _create_amplifier_test(DIV_CONFIG)
test_sdiv = _create_amplifier_test(SDIV_CONFIG)
test_mod = _create_amplifier_test(MOD_CONFIG)
test_smod = _create_amplifier_test(SMOD_CONFIG)
test_addmod = _create_amplifier_test(ADDMOD_CONFIG)
test_mulmod = _create_amplifier_test(MULMOD_CONFIG)
test_signextend = _create_amplifier_test(SIGNEXTEND_CONFIG)

# Comparison opcodes
test_lt = _create_amplifier_test(LT_CONFIG)
test_gt = _create_amplifier_test(GT_CONFIG)
test_slt = _create_amplifier_test(SLT_CONFIG)
test_sgt = _create_amplifier_test(SGT_CONFIG)
test_eq = _create_amplifier_test(EQ_CONFIG)
test_iszero = _create_amplifier_test(ISZERO_CONFIG)

# Bitwise opcodes
test_and = _create_amplifier_test(AND_CONFIG)
test_or = _create_amplifier_test(OR_CONFIG)
test_xor = _create_amplifier_test(XOR_CONFIG)
test_not = _create_amplifier_test(NOT_CONFIG)
test_byte = _create_amplifier_test(BYTE_CONFIG)
test_shl = _create_amplifier_test(SHL_CONFIG)
test_shr = _create_amplifier_test(SHR_CONFIG)
test_sar = _create_amplifier_test(SAR_CONFIG)

# Stack opcodes
test_push0 = _create_amplifier_test(PUSH0_CONFIG)
test_push1 = _create_amplifier_test(PUSH1_CONFIG)
test_push16 = _create_amplifier_test(PUSH16_CONFIG)
test_push32 = _create_amplifier_test(PUSH32_CONFIG)
test_pop = _create_amplifier_test(POP_CONFIG)

# Environment opcodes
test_address = _create_amplifier_test(ADDRESS_CONFIG)
test_origin = _create_amplifier_test(ORIGIN_CONFIG)
test_caller = _create_amplifier_test(CALLER_CONFIG)
test_callvalue = _create_amplifier_test(CALLVALUE_CONFIG)
test_calldatasize = _create_amplifier_test(CALLDATASIZE_CONFIG)
test_codesize = _create_amplifier_test(CODESIZE_CONFIG)
test_gasprice = _create_amplifier_test(GASPRICE_CONFIG)
test_returndatasize = _create_amplifier_test(RETURNDATASIZE_CONFIG)
test_gas = _create_amplifier_test(GAS_CONFIG)

# Block info opcodes
test_coinbase = _create_amplifier_test(COINBASE_CONFIG)
test_timestamp = _create_amplifier_test(TIMESTAMP_CONFIG)
test_number = _create_amplifier_test(NUMBER_CONFIG)
test_prevrandao = _create_amplifier_test(PREVRANDAO_CONFIG)
test_gaslimit = _create_amplifier_test(GASLIMIT_CONFIG)
test_chainid = _create_amplifier_test(CHAINID_CONFIG)
test_selfbalance = _create_amplifier_test(SELFBALANCE_CONFIG)
test_caller_basefee = _create_amplifier_test(BASEFEE_CONFIG)
test_blobbasefee = _create_amplifier_test(BLOBBASEFEE_CONFIG)
test_pc = _create_amplifier_test(PC_CONFIG)

# Memory opcodes
test_mload = _create_amplifier_test(MLOAD_CONFIG)
test_mstore = _create_amplifier_test(MSTORE_CONFIG)
test_mstore8 = _create_amplifier_test(MSTORE8_CONFIG)
test_msize = _create_amplifier_test(MSIZE_CONFIG)
test_mcopy = _create_amplifier_test(MCOPY_CONFIG)
test_codecopy = _create_amplifier_test(CODECOPY_CONFIG)
test_calldatacopy = _create_amplifier_test(CALLDATACOPY_CONFIG)
test_calldataload = _create_amplifier_test(CALLDATALOAD_CONFIG)
test_returndatacopy = _create_amplifier_test(RETURNDATACOPY_CONFIG)

# Storage opcodes (SLOAD, TLOAD work with STATICCALL)
test_sload = _create_amplifier_test(SLOAD_CONFIG)
test_tload = _create_amplifier_test(TLOAD_CONFIG)

# External code opcodes
test_balance = _create_amplifier_test(BALANCE_CONFIG)
test_extcodesize = _create_amplifier_test(EXTCODESIZE_CONFIG)
test_extcodehash = _create_amplifier_test(EXTCODEHASH_CONFIG)
test_extcodecopy = _create_amplifier_test(EXTCODECOPY_CONFIG)
test_blockhash = _create_amplifier_test(BLOCKHASH_CONFIG)
test_blobhash = _create_amplifier_test(BLOBHASH_CONFIG)

# Hash opcodes
test_keccak256 = _create_amplifier_test(KECCAK256_CONFIG)

# Misc opcodes
test_jumpdest = _create_amplifier_test(JUMPDEST_CONFIG)
test_exp = _create_amplifier_test(EXP_CONFIG)

# Control flow opcodes
test_jump = _create_amplifier_test(JUMP_CONFIG, generate_jump_target)
test_jumpi = _create_amplifier_test(JUMPI_CONFIG, generate_jumpi_target)

# State-modifying opcodes
test_sstore = _create_amplifier_test(SSTORE_CONFIG)
test_tstore = _create_amplifier_test(TSTORE_CONFIG)

# DUP opcodes
test_dup1 = _create_amplifier_test(
    DUP1_CONFIG, lambda oc, moc: generate_dup_target(DUP1_CONFIG.variant, oc, moc)
)
test_dup8 = _create_amplifier_test(
    DUP8_CONFIG, lambda oc, moc: generate_dup_target(DUP8_CONFIG.variant, oc, moc)
)
test_dup16 = _create_amplifier_test(
    DUP16_CONFIG, lambda oc, moc: generate_dup_target(DUP16_CONFIG.variant, oc, moc)
)

# SWAP opcodes
test_swap1 = _create_amplifier_test(
    SWAP1_CONFIG, lambda oc, moc: generate_swap_target(SWAP1_CONFIG.variant, oc, moc)
)
test_swap8 = _create_amplifier_test(
    SWAP8_CONFIG, lambda oc, moc: generate_swap_target(SWAP8_CONFIG.variant, oc, moc)
)
test_swap16 = _create_amplifier_test(
    SWAP16_CONFIG, lambda oc, moc: generate_swap_target(SWAP16_CONFIG.variant, oc, moc)
)

# LOG opcodes (require CALL instead of STATICCALL)
test_log0 = _create_amplifier_test(LOG0_CONFIG)
test_log1 = _create_amplifier_test(LOG1_CONFIG)
test_log2 = _create_amplifier_test(LOG2_CONFIG)
test_log3 = _create_amplifier_test(LOG3_CONFIG)
test_log4 = _create_amplifier_test(LOG4_CONFIG)