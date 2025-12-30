"""
Marginal cost estimation tests for EVM opcodes.

This module implements the "marginal approach" for gas cost estimation as described
in the gas-cost-estimator project. The key insight is:

1. Generate a series of programs where only the number of target opcodes varies
2. Keep everything else constant (stack setup, cleanup, or noop padding)
3. The marginal cost of an opcode can be extracted via linear regression on execution times

"""

from dataclasses import dataclass
from typing import Callable, List

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

    pops_per_op: int
    """Number of values the opcode pops from stack."""

    pushes_per_op: int
    """Number of values the opcode pushes to stack."""

    num_calls: int = 100
    """Number of times caller calls target (to amplify gas usage)."""

    setup_code: Bytecode | None = None
    """Optional setup code to run before the main loop (e.g., memory init)."""


@dataclass
class CustomOpcodeConfig:
    """Configuration for opcodes that use custom target generators (DUP, SWAP, LOG, JUMP)."""

    name: str
    """Name of the opcode for test identification."""

    max_op_count: int
    """Maximum number of opcode instances per call."""

    step: int
    """Step size for op_count increments."""

    num_calls: int
    """Number of times caller calls target (to amplify gas usage)."""

    # For DUP/SWAP: which variant (1-16)
    variant: int = 0
    """For DUP1-16 or SWAP1-16, specifies which variant."""

    # For LOG: number of topics
    topic_count: int = 0
    """For LOG0-4, specifies number of topics."""

    # Whether target needs CALL instead of STATICCALL (e.g., LOG modifies state)
    needs_call: bool = False
    """If True, use CALL instead of STATICCALL for the caller contract."""


# Define opcode configurations
# Low-cost opcodes: 200 max_op_count, step of 20
# High-cost opcodes: 20 max_op_count, step of 5

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
# For POP-based padding (pushes_per_op > 0), peak stack usage is:
#   max_op_count * pushes_per_op + max_op_count * len(stack_args)
# = max_op_count * (pushes_per_op + len(stack_args))
#
# Stack limit is 1024, so:
#   max_op_count <= 1024 / (pushes_per_op + len(stack_args))
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
    step=100,  # 4 data points
    stack_args=[BLS12_381_SCALAR_FIELD, SECP256K1_FIELD_PRIME],  # DEFAULT_BINOP_ARGS
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=3000,
)

# Ref: test_arithmetic.py opcode_MUL (uses DEFAULT_BINOP_ARGS)
MUL_CONFIG = MarginalOpcodeConfig(
    name="MUL",
    opcode=Op.MUL,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[BLS12_381_SCALAR_FIELD, SECP256K1_FIELD_PRIME],  # DEFAULT_BINOP_ARGS
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=2000,  # Doubled for ~1M gas
)

# Ref: test_arithmetic.py opcode_SUB (uses DEFAULT_BINOP_ARGS)
SUB_CONFIG = MarginalOpcodeConfig(
    name="SUB",
    opcode=Op.SUB,
    max_op_count=300,
    step=50,  # 7 data points (improved R²)
    stack_args=[BLS12_381_SCALAR_FIELD, SECP256K1_FIELD_PRIME],  # DEFAULT_BINOP_ARGS
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=10000,  # 2x for short proving time
)

# Ref: test_arithmetic.py opcode_DIV-0
# Worst case: divisor slightly > 2^128 triggers 3-word division path
DIV_CONFIG = MarginalOpcodeConfig(
    name="DIV",
    opcode=Op.DIV,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[DIV_DIVISOR, DIV_DIVIDEND],  # divisor, dividend (pushed in reverse pop order)
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=700,
)

# Ref: test_arithmetic.py opcode_SDIV-1
# Worst case: positive dividend, negative ~2^128 divisor
SDIV_CONFIG = MarginalOpcodeConfig(
    name="SDIV",
    opcode=Op.SDIV,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[SDIV_DIVISOR, SDIV_DIVIDEND],  # divisor, dividend (pushed in reverse pop order)
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=700,
)

# Ref: test_arithmetic.py op_MOD-mod_bits_191
# execution-specs found 191-bit modulus is SLOWER than 255-bit (counterintuitive!)
MOD_CONFIG = MarginalOpcodeConfig(
    name="MOD",
    opcode=Op.MOD,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[MOD_191_BIT, MAX_U256],  # 191-bit modulus, MAX dividend
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=700,
)

# Ref: test_arithmetic.py op_SMOD-mod_bits_191
# execution-specs found 191-bit modulus is SLOWER than 255-bit (counterintuitive!)
SMOD_CONFIG = MarginalOpcodeConfig(
    name="SMOD",
    opcode=Op.SMOD,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[MOD_191_BIT, MAX_U256],  # 191-bit modulus, MAX dividend
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=2000,  # Scaled for 150M cycles
)

# Ref: test_arithmetic.py op_ADDMOD-mod_bits_191
# execution-specs found 191-bit modulus is SLOWER than 255-bit (counterintuitive!)
ADDMOD_CONFIG = MarginalOpcodeConfig(
    name="ADDMOD",
    opcode=Op.ADDMOD,
    max_op_count=201,  # 201 * 4 = 804 < 1024
    step=67,  # 4 data points
    stack_args=[MOD_191_BIT, MAX_U256, MAX_U256],  # N=191-bit mod, b=MAX, a=MAX
    pops_per_op=3,
    pushes_per_op=1,
    num_calls=1000,  # Calculated for 500K+ gas
)

# Ref: test_arithmetic.py op_MULMOD-mod_bits_191
# execution-specs found 191-bit modulus is SLOWER than 255-bit (counterintuitive!)
MULMOD_CONFIG = MarginalOpcodeConfig(
    name="MULMOD",
    opcode=Op.MULMOD,
    max_op_count=210,
    step=70,  # ~5 data points
    stack_args=[MOD_191_BIT, MAX_U256, MAX_U256],  # N=191-bit mod, b=MAX, a=MAX
    pops_per_op=3,
    pushes_per_op=1,
    num_calls=1000,  # Calculated for 500K+ gas
)

# Ref: test_arithmetic.py opcode_EXP (uses MAX_U256, MAX_U256)
# EXP is expensive: 10 + 50 * byte_length_of_exponent
# With 32-byte exponent = 10 + 50 * 32 = 1610 gas
EXP_CONFIG = MarginalOpcodeConfig(
    name="EXP",
    opcode=Op.EXP,
    max_op_count=150,
    step=50,  # 4 data points
    stack_args=[MAX_U256, MAX_U256],  # execution-specs uses MAX for both - matches!
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=15,  # Doubled for ~1M gas
)

# Ref: test_arithmetic.py opcode_SIGNEXTEND (uses k=3, x=0xFFDADADA)
# execution-specs uses k=3 (sign-extend 4 bytes) with a negative value
SIGNEXTEND_CONFIG = MarginalOpcodeConfig(
    name="SIGNEXTEND",
    opcode=Op.SIGNEXTEND,
    max_op_count=300,  # 300 * 3 = 900 < 1024
    step=100,  # ~5 data points
    stack_args=[0xFFDADADA, 3],  # x=negative value, k=3 (4-byte extend)
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=5000,  # Scaled for 150M cycles target
)

# ============================================================================
# COMPARISON OPCODES
# ============================================================================

LT_CONFIG = MarginalOpcodeConfig(
    name="LT",
    opcode=Op.LT,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

GT_CONFIG = MarginalOpcodeConfig(
    name="GT",
    opcode=Op.GT,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

SLT_CONFIG = MarginalOpcodeConfig(
    name="SLT",
    opcode=Op.SLT,
    max_op_count=300,
    step=50,  # 7 data points (improved R²)
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=7000,
)

SGT_CONFIG = MarginalOpcodeConfig(
    name="SGT",
    opcode=Op.SGT,
    max_op_count=300,
    step=50,  # 7 data points (improved R²)
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=6000,  # 2x for short proving time
)

EQ_CONFIG = MarginalOpcodeConfig(
    name="EQ",
    opcode=Op.EQ,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=1500,  # Calculated for 500K+ gas
)

ISZERO_CONFIG = MarginalOpcodeConfig(
    name="ISZERO",
    opcode=Op.ISZERO,
    max_op_count=450,  # 450 * 2 = 900 < 1024
    step=90,  # 6 data points (improved R²)
    stack_args=[MAX_U256],
    pops_per_op=1,
    pushes_per_op=1,
    num_calls=6000,  # 2x for low R² (0.86)
)

# ============================================================================
# BITWISE OPCODES
# ============================================================================

AND_CONFIG = MarginalOpcodeConfig(
    name="AND",
    opcode=Op.AND,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

OR_CONFIG = MarginalOpcodeConfig(
    name="OR",
    opcode=Op.OR,
    max_op_count=300,
    step=60,  # 6 data points (improved R²)
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=3000,
)

XOR_CONFIG = MarginalOpcodeConfig(
    name="XOR",
    opcode=Op.XOR,
    max_op_count=300,
    step=100,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=5000,  # Calculated for 500K+ gas
)

NOT_CONFIG = MarginalOpcodeConfig(
    name="NOT",
    opcode=Op.NOT,
    max_op_count=450,  # 450 * 2 = 900 < 1024
    step=90,  # 6 data points (improved R²)
    stack_args=[MAX_U256],
    pops_per_op=1,
    pushes_per_op=1,
    num_calls=4000,  # 2x for short proving time
)

BYTE_CONFIG = MarginalOpcodeConfig(
    name="BYTE",
    opcode=Op.BYTE,
    max_op_count=300,  # 300 * 3 = 900 < 1024
    step=100,  # 4 data points
    stack_args=[MAX_U256, 31],  # x=MAX, i=31 (pushed in reverse pop order)
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=2000,
)

SHL_CONFIG = MarginalOpcodeConfig(
    name="SHL",
    opcode=Op.SHL,
    max_op_count=300,  # 300 * 3 = 900 < 1024
    step=100,  # 4 data points
    stack_args=[MAX_U256, 255],  # value=MAX, shift=255 (pushed in reverse pop order)
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=1500,  # Calculated for 500K+ gas
)

SHR_CONFIG = MarginalOpcodeConfig(
    name="SHR",
    opcode=Op.SHR,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[MAX_U256, 255],  # value=MAX, shift=255 (pushed in reverse pop order)
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=2000,  # Scaled for 150M cycles
)

SAR_CONFIG = MarginalOpcodeConfig(
    name="SAR",
    opcode=Op.SAR,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[MAX_U256, 255],  # value=MAX, shift=255 (pushed in reverse pop order)
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=1500,  # Calculated for 500K+ gas
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
    step=40,
    stack_args=[8192, 0],  # size=8KB, offset=0 (pushed in reverse pop order)
    pops_per_op=2,
    pushes_per_op=1,
    num_calls=200,  # Calculated for 500K+ gas
    # Pre-allocate 8KB of memory with data to hash
    setup_code=_generate_keccak256_setup(),
)

# ============================================================================
# STACK OPCODES - Representative samples (PUSH1, PUSH16, PUSH32, DUP, SWAP)
# ============================================================================

# Note: PUSH opcodes need special handling - they don't pop anything
# and we need to pop their result to balance the stack

PUSH0_CONFIG = MarginalOpcodeConfig(
    name="PUSH0",
    opcode=Op.PUSH0,  # EIP-3855, pushes 0 onto stack
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

PUSH1_CONFIG = MarginalOpcodeConfig(
    name="PUSH1",
    opcode=Op.PUSH1(0xFF),  # Push max 1-byte value
    max_op_count=600,
    step=120,  # 6 data points (improved R²)
    stack_args=[],  # PUSH doesn't consume stack
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

PUSH16_CONFIG = MarginalOpcodeConfig(
    name="PUSH16",
    opcode=Op.PUSH16(MAX_U256 >> 128),  # Max 16-byte value
    max_op_count=501,
    step=167,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=4000,  # 2x for short proving time
)

PUSH32_CONFIG = MarginalOpcodeConfig(
    name="PUSH32",
    opcode=Op.PUSH32(MAX_U256),  # Max 32-byte value
    max_op_count=350,
    step=70,  # 6 data points (improved R²)
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=3000,  # 2x for short proving time
)

# ============================================================================
# CUSTOM OPCODE CONFIGS - DUP, SWAP, LOG, JUMP
# These opcodes require custom target generators
# ============================================================================

DUP1_CONFIG = CustomOpcodeConfig(
    name="DUP1", max_op_count=300, step=60, num_calls=6000, variant=1
)
DUP8_CONFIG = CustomOpcodeConfig(
    name="DUP8", max_op_count=300, step=60, num_calls=6000, variant=8
)
DUP16_CONFIG = CustomOpcodeConfig(
    name="DUP16", max_op_count=300, step=60, num_calls=4000, variant=16
)

SWAP1_CONFIG = CustomOpcodeConfig(
    name="SWAP1", max_op_count=300, step=60, num_calls=2000, variant=1
)
SWAP8_CONFIG = CustomOpcodeConfig(
    name="SWAP8", max_op_count=300, step=100, num_calls=2000, variant=8
)
SWAP16_CONFIG = CustomOpcodeConfig(
    name="SWAP16", max_op_count=300, step=100, num_calls=2000, variant=16
)

LOG0_CONFIG = CustomOpcodeConfig(
    name="LOG0", max_op_count=100, step=20, num_calls=2400, topic_count=0, needs_call=True
)
LOG1_CONFIG = CustomOpcodeConfig(
    name="LOG1", max_op_count=81, step=27, num_calls=2000, topic_count=1, needs_call=True
)
LOG2_CONFIG = CustomOpcodeConfig(
    name="LOG2", max_op_count=60, step=20, num_calls=1400, topic_count=2, needs_call=True
)
LOG3_CONFIG = CustomOpcodeConfig(
    name="LOG3", max_op_count=51, step=17, num_calls=1400, topic_count=3, needs_call=True
)
LOG4_CONFIG = CustomOpcodeConfig(
    name="LOG4", max_op_count=39, step=13, num_calls=1400, topic_count=4, needs_call=True
)

JUMP_CONFIG = CustomOpcodeConfig(
    name="JUMP", max_op_count=200, step=40, num_calls=6000
)
JUMPI_CONFIG = CustomOpcodeConfig(
    name="JUMPI", max_op_count=201, step=67, num_calls=5000
)

# POP opcode: pops 1 value, pushes 0 (2 gas)
# For marginal testing, we need to provide values to pop
POP_CONFIG = MarginalOpcodeConfig(
    name="POP",
    opcode=Op.POP,
    max_op_count=600,
    step=120,  # 6 data points (improved R²)
    stack_args=[0],  # Push 0 to pop (using PUSH0 is cheapest)
    pops_per_op=1,
    pushes_per_op=0,
    num_calls=6000,  # 2x for short proving time
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


def generate_marginal_program(
    config: MarginalOpcodeConfig,
    op_count: int,
) -> Bytecode:
    """
    Generate a marginal program for the given opcode configuration.

    Following the gas-cost-estimator approach, there are two strategies:

    1. For opcodes that RETURN values (pushes_per_op > 0):
       - Push "empty" values first to ensure POPs always have something
       - Push all arguments upfront
       - Interleave opcodes with result POPs
       - Total POPs = max_op_count * pushes_per_op (CONSTANT)

    2. For opcodes that DON'T return values (pushes_per_op == 0):
       - Use "noop" padding instead of POPs
       - For op_count executions: push args + execute opcode
       - For remaining (max_op_count - op_count): just push args (no opcode)
       - This keeps total PUSH count constant while varying only opcode count

    Args:
        config: The opcode configuration
        op_count: Number of times to execute the opcode

    Returns:
        Bytecode for the marginal program
    """
    assert 0 <= op_count <= config.max_op_count

    code = Bytecode()

    # 1. Optional setup code (e.g., memory initialization)
    if config.setup_code is not None:
        code += config.setup_code

    if config.pushes_per_op > 0:
        # ================================================================
        # Strategy 1: POP-based padding for opcodes that return values
        # ================================================================
        
        # 2. Push "empty" values to ensure there's always something to POP
        total_result_pops = config.max_op_count * config.pushes_per_op
        for _ in range(total_result_pops):
            code += Op.PUSH0

        # 3. Push stack arguments for ALL potential opcode instances
        for _ in range(config.max_op_count):
            for arg in config.stack_args:
                code += push_value(arg)

        # 4. Execute opcodes with interleaved POPs
        if op_count == 0:
            # No opcodes, just POP all the empty values
            for _ in range(total_result_pops):
                code += Op.POP
        else:
            # Execute first opcode
            code += config.opcode
            # Interleave remaining opcodes with result POPs
            interleaved_count = op_count - 1
            for _ in range(interleaved_count):
                for _ in range(config.pushes_per_op):
                    code += Op.POP
                code += config.opcode
            # POP remaining results at the end
            end_pops = total_result_pops - interleaved_count * config.pushes_per_op
            for _ in range(end_pops):
                code += Op.POP
    else:
        # ================================================================
        # Strategy 2: Noop-based padding for non-returning opcodes
        # (Following gas-cost-estimator's MSTORE/CALLDATACOPY approach)
        # ================================================================
        
        # Structure (matching gas-cost-estimator):
        # 1. For op_count iterations: PUSH args + OPCODE
        # 2. For (max_op_count - op_count) iterations: PUSH args only (no opcode)
        #
        # This ensures:
        # - Total PUSH count is constant (max_op_count * len(stack_args))
        # - Only the opcode execution count varies
        # - Stack may be unbalanced at end (that's OK - STOP doesn't require it)
        
        # 1. Real operations: push args + execute opcode
        for _ in range(op_count):
            for arg in config.stack_args:
                code += push_value(arg)
            code += config.opcode
        
        # 2. Noops: just push args (no opcode, no pop)
        # These values stay on stack - that's fine
        noop_count = config.max_op_count - op_count
        for _ in range(noop_count):
            for arg in config.stack_args:
                code += push_value(arg)

    # 5. Write success marker to storage (proves execution didn't revert)
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)

    # 6. Stop execution
    code += Op.STOP

    return code


def generate_op_counts(max_op_count: int, step: int) -> List[int]:
    """Generate list of op_counts from 0 to max_op_count with given step."""
    counts = list(range(0, max_op_count + 1, step))
    # Ensure max_op_count is included even if not aligned with step
    if counts[-1] != max_op_count:
        counts.append(max_op_count)
    return counts


# ============================================================================
# CALLER-CONTRACT APPROACH
# ============================================================================
# The caller-contract pattern amplifies op_count by having a caller contract
# call a target contract N times. This allows much higher effective op_counts
# while keeping individual contract sizes within limits.
#
# Effective op_count = num_calls × op_count_per_call
#
# Each opcode has its own num_calls value calculated to achieve >= 500K max gas.
# ============================================================================

# Legacy constant for backward compatibility (new tests use config.num_calls)
NUM_CALLS = 100
CALLER_GAS_LIMIT = 500_000_000  # High gas limit for scaled benchmarking (500M)


def generate_target_contract_code(
    config: MarginalOpcodeConfig,
    op_count: int,
) -> Bytecode:
    """
    Generate a target contract for caller-contract approach.
    
    Same as generate_marginal_program but WITHOUT SSTORE (since it's called
    via STATICCALL which doesn't allow state changes). Just ends with STOP.
    """
    assert 0 <= op_count <= config.max_op_count

    code = Bytecode()

    # 1. Optional setup code (e.g., memory initialization)
    if config.setup_code is not None:
        code += config.setup_code

    if config.pushes_per_op > 0:
        # Strategy 1: POP-based padding for opcodes that return values
        total_result_pops = config.max_op_count * config.pushes_per_op
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
                for _ in range(config.pushes_per_op):
                    code += Op.POP
                code += config.opcode
            end_pops = total_result_pops - interleaved_count * config.pushes_per_op
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

    # Just STOP (no SSTORE since called via STATICCALL)
    code += Op.STOP

    return code


def generate_caller_contract_code(target_address: Address, num_calls: int) -> Bytecode:
    """
    Generate caller contract that calls target num_calls times using a loop.
    
    Uses a loop structure instead of unrolled calls to keep bytecode size constant.
    The loop overhead is constant across all test variants, so it gets eliminated
    in the marginal cost regression.
    
    Structure:
        PUSH num_calls          ; Initialize counter
        JUMPDEST (loop_start)   ; Loop label
        STATICCALL to target    ; Call target contract
        POP                     ; Pop success flag
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
    
    # Call target contract (STATICCALL: gas, addr, argsOffset, argsSize, retOffset, retSize)
    code += Op.PUSH1(0)                   # retSize
    code += Op.PUSH1(0)                   # retOffset  
    code += Op.PUSH1(0)                   # argsSize
    code += Op.PUSH1(0)                   # argsOffset
    code += Op.PUSH20(target_address)     # address
    code += Op.GAS                        # gas (forward all)
    code += Op.STATICCALL
    code += Op.POP                        # pop success flag
    
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


def generate_caller_contract_code_call(target_address: Address, num_calls: int) -> Bytecode:
    """
    Generate caller contract using CALL instead of STATICCALL (loop version).
    Required for state-modifying opcodes (TSTORE, LOG, SSTORE).

    Uses a loop structure instead of unrolled calls to keep bytecode size constant.
    """
    code = Bytecode()

    # Push loop counter
    if num_calls <= 0xFF:
        code += Op.PUSH1(num_calls)
    elif num_calls <= 0xFFFF:
        code += Op.PUSH2(num_calls)
    else:
        code += Op.PUSH3(num_calls)

    # Loop start
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
    code += Op.CALL
    code += Op.POP                        # pop success flag

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

CallerGenerator = Callable[[Address, int], Bytecode]
"""Caller generator signature: (target_address, num_calls) -> Bytecode."""


def _create_caller_test(
    cfg: MarginalOpcodeConfig | CustomOpcodeConfig,
    target_generator: TargetGenerator | None = None,
    *,
    needs_call: bool | None = None,
):
    """
    Single factory for all caller-contract marginal tests.

    - If cfg is MarginalOpcodeConfig: defaults to generate_target_contract_code(cfg, op_count)
    - If cfg is CustomOpcodeConfig: requires target_generator(op_count, max_op_count)

    `needs_call=True` forces using CALL-based caller (required for state-modifying opcodes).
    """
    if isinstance(cfg, MarginalOpcodeConfig):
        max_op_count = cfg.max_op_count
        step = cfg.step
        num_calls = cfg.num_calls
        if target_generator is None:
            target_generator = lambda oc, _moc: generate_target_contract_code(cfg, oc)
        if needs_call is None:
            needs_call = False
    elif isinstance(cfg, CustomOpcodeConfig):
        max_op_count = cfg.max_op_count
        step = cfg.step
        num_calls = cfg.num_calls
        if target_generator is None:
            raise ValueError("CustomOpcodeConfig requires a target_generator")
        if needs_call is None:
            needs_call = cfg.needs_call
    else:
        raise TypeError(f"Unsupported config type: {type(cfg)}")

    caller_gen: CallerGenerator = (
        generate_caller_contract_code_call if needs_call else generate_caller_contract_code
    )

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

        caller_code = caller_gen(target_contract, num_calls)
        caller_contract = pre.deploy_contract(code=caller_code)

        sender = pre.fund_eoa()

        tx = Transaction(
            to=caller_contract,
            gas_limit=CALLER_GAS_LIMIT,
            sender=sender,
        )

        post = {caller_contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}

        state_test(env=Environment(gas_limit=CALLER_GAS_LIMIT), pre=pre, post=post, tx=tx)
    
    return test_func


# ============================================================================
# NOTE
# Most opcodes in this file use the caller-contract pattern:
#   - a target contract whose opcode count varies with op_count
#   - a caller contract that loops num_calls times (amplifies total work)
# This keeps marginal regression well-conditioned for low-gas opcodes.
# ============================================================================


# ============================================================================
# ENVIRONMENT OPCODES - Return context/environment info (no input, push 1)
# ============================================================================

ADDRESS_CONFIG = MarginalOpcodeConfig(
    name="ADDRESS",
    opcode=Op.ADDRESS,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],  # No input
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=1500,  # Calculated for 500K+ gas
)

ORIGIN_CONFIG = MarginalOpcodeConfig(
    name="ORIGIN",
    opcode=Op.ORIGIN,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

CALLER_CONFIG = MarginalOpcodeConfig(
    name="CALLER",
    opcode=Op.CALLER,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

CALLVALUE_CONFIG = MarginalOpcodeConfig(
    name="CALLVALUE",
    opcode=Op.CALLVALUE,
    max_op_count=600,
    step=150,  # ~5 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

CALLDATASIZE_CONFIG = MarginalOpcodeConfig(
    name="CALLDATASIZE",
    opcode=Op.CALLDATASIZE,
    max_op_count=600,
    step=120,  # 6 data points (improved R²)
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

CODESIZE_CONFIG = MarginalOpcodeConfig(
    name="CODESIZE",
    opcode=Op.CODESIZE,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

GASPRICE_CONFIG = MarginalOpcodeConfig(
    name="GASPRICE",
    opcode=Op.GASPRICE,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

RETURNDATASIZE_CONFIG = MarginalOpcodeConfig(
    name="RETURNDATASIZE",
    opcode=Op.RETURNDATASIZE,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

GAS_CONFIG = MarginalOpcodeConfig(
    name="GAS",
    opcode=Op.GAS,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

# ============================================================================
# BLOCK INFO OPCODES - Return block context (no input, push 1)
# ============================================================================

COINBASE_CONFIG = MarginalOpcodeConfig(
    name="COINBASE",
    opcode=Op.COINBASE,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

TIMESTAMP_CONFIG = MarginalOpcodeConfig(
    name="TIMESTAMP",
    opcode=Op.TIMESTAMP,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

NUMBER_CONFIG = MarginalOpcodeConfig(
    name="NUMBER",
    opcode=Op.NUMBER,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

PREVRANDAO_CONFIG = MarginalOpcodeConfig(
    name="PREVRANDAO",
    opcode=Op.PREVRANDAO,  # Was DIFFICULTY pre-merge
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=1500,  # Calculated for 500K+ gas
)

GASLIMIT_CONFIG = MarginalOpcodeConfig(
    name="GASLIMIT",
    opcode=Op.GASLIMIT,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

CHAINID_CONFIG = MarginalOpcodeConfig(
    name="CHAINID",
    opcode=Op.CHAINID,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

SELFBALANCE_CONFIG = MarginalOpcodeConfig(
    name="SELFBALANCE",
    opcode=Op.SELFBALANCE,
    max_op_count=600,
    step=200,  # ~5 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=1000, 
)

BASEFEE_CONFIG = MarginalOpcodeConfig(
    name="BASEFEE",
    opcode=Op.BASEFEE,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)


BLOBBASEFEE_CONFIG = MarginalOpcodeConfig(
    name="BLOBBASEFEE",
    opcode=Op.BLOBBASEFEE,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)

# ============================================================================
# MEMORY OPCODES - Memory read/write operations
# ============================================================================

# Memory is pre-expanded via setup_code to avoid memory expansion costs in measurements

MLOAD_CONFIG = MarginalOpcodeConfig(
    name="MLOAD",
    opcode=Op.MLOAD,
    max_op_count=501,
    step=167,  # 4 data points
    stack_args=[0],  # offset - read from offset 0
    pops_per_op=1,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
    setup_code=Op.MSTORE(0, MAX_U256),  # Pre-expand memory with data
)

MSTORE_CONFIG = MarginalOpcodeConfig(
    name="MSTORE",
    opcode=Op.MSTORE,
    max_op_count=501,
    step=167,  # 4 data points
    stack_args=[MAX_U256, 0],  # value, offset (MSTORE pops offset first)
    pops_per_op=2,
    pushes_per_op=0,
    num_calls=1000,  # Calculated for 500K+ gas
    setup_code=Op.MSTORE(0, 0),  # Pre-expand memory
)

MSTORE8_CONFIG = MarginalOpcodeConfig(
    name="MSTORE8",
    opcode=Op.MSTORE8,
    max_op_count=501,
    step=167,  # 4 data points
    stack_args=[0xFF, 0],  # value, offset (MSTORE8 pops offset first)
    pops_per_op=2,
    pushes_per_op=0,
    num_calls=4000,  # 2x for short proving time
    setup_code=Op.MSTORE(0, 0),  # Pre-expand memory
)

MSIZE_CONFIG = MarginalOpcodeConfig(
    name="MSIZE",
    opcode=Op.MSIZE,
    max_op_count=600,
    step=150,  # ~5 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=4000,  # 2x for short proving time
    setup_code=Op.MSTORE(0, 0),  # Pre-expand memory so MSIZE returns non-zero
)

# CALLDATACOPY: destOffset, offset, size (copies from calldata to memory)
# Use 32 bytes for worst-case cycles/gas (smaller size = higher zkVM overhead per gas)
CALLDATACOPY_CONFIG = MarginalOpcodeConfig(
    name="CALLDATACOPY",
    opcode=Op.CALLDATACOPY,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[32, 0, 0],  # size=32 bytes, offset=0, destOffset=0 (worst-case: small copy)
    pops_per_op=3,
    pushes_per_op=0,
    num_calls=2000,  # Scaled for 150M cycles target
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
    step=100,  # 4 data points
    stack_args=[64, 0, 128],  # size=64, offset=0, destOffset=128 (pushed in reverse pop order)
    pops_per_op=3,
    pushes_per_op=0,
    num_calls=600,  # Calculated for 500K+ gas: 170 × (200 setup + 300×9) ≈ 493K
    setup_code=_generate_returndatacopy_setup(),
)

# CODECOPY: destOffset, offset, size (copies from code to memory)
# Use 32 bytes for worst-case cycles/gas (smaller size = higher zkVM overhead per gas)
CODECOPY_CONFIG = MarginalOpcodeConfig(
    name="CODECOPY",
    opcode=Op.CODECOPY,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[32, 0, 0],  # size=32 bytes, offset=0, destOffset=0 (worst-case: small copy)
    pops_per_op=3,
    pushes_per_op=0,
    num_calls=3000,
    setup_code=Op.MSTORE(0, 0),  # Pre-expand memory
)

# MCOPY: destOffset, srcOffset, size (copies within memory) - EIP-5656
MCOPY_CONFIG = MarginalOpcodeConfig(
    name="MCOPY",
    opcode=Op.MCOPY,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[1024, 0, 4096],  # size=1KB, srcOffset=0, destOffset=4096 (pushed in reverse pop order)
    pops_per_op=3,
    pushes_per_op=0,
    num_calls=400,  # 2x for short proving time
    setup_code=Op.MSTORE(0, MAX_U256) + Op.MSTORE(4096, 0),  # Pre-expand memory regions
)


# ============================================================================
# DATA ACCESS OPCODES
# ============================================================================

# CALLDATALOAD: pops offset, pushes 32 bytes from calldata
CALLDATALOAD_CONFIG = MarginalOpcodeConfig(
    name="CALLDATALOAD",
    opcode=Op.CALLDATALOAD,
    max_op_count=501,
    step=167,  # 4 data points
    stack_args=[0],  # Load from offset 0
    pops_per_op=1,
    pushes_per_op=1,
    num_calls=2000,  # 2x for short proving time
)

# BLOCKHASH: pops block number, pushes hash (or 0 if out of range)
BLOCKHASH_CONFIG = MarginalOpcodeConfig(
    name="BLOCKHASH",
    opcode=Op.BLOCKHASH,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[0],  # Block 0 (will return 0 but still executes)
    pops_per_op=1,
    pushes_per_op=1,
    num_calls=400,  # Keep at 100
)

# BLOBHASH: pops blob index, pushes versioned hash (or 0 if out of range)
BLOBHASH_CONFIG = MarginalOpcodeConfig(
    name="BLOBHASH",
    opcode=Op.BLOBHASH,
    max_op_count=501,
    step=167,  # 4 data points
    stack_args=[0],  # Blob index 0 (will return 0 if no blobs)
    pops_per_op=1,
    pushes_per_op=1,
    num_calls=3000,
)


@pytest.mark.skip(reason="BLOCKHASH requires proper block history in test environment")
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BLOCKHASH_CONFIG.max_op_count, BLOCKHASH_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_blockhash(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for BLOCKHASH opcode."""
    code = generate_marginal_program(BLOCKHASH_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(gas_limit=CALLER_GAS_LIMIT), pre=pre, post=post, tx=tx)


# ============================================================================
# STORAGE OPCODES - SLOAD, SSTORE, TLOAD, TSTORE
# ============================================================================

# SLOAD: First access to cold slot costs 2100 gas, warm access costs 100 gas
# For marginal testing, we warm up the slot first to measure consistent warm access cost
SLOAD_CONFIG = MarginalOpcodeConfig(
    name="SLOAD",
    opcode=Op.SLOAD,
    max_op_count=99,
    step=33,  # 4 data points
    stack_args=[100],  # Storage slot 100 (different from SUCCESS_SLOT)
    pops_per_op=1,
    pushes_per_op=1,
    num_calls=2000,  # Scaled for 150M cycles target
    setup_code=Op.POP(Op.SLOAD(100)),  # Warm up slot 100 first
)

# SSTORE: Complex gas rules (cold access, dirty/clean, refunds)
# Slot 100, value MAX_U256 - repeated writes to same slot
# Note: SSTORE pops slot first, then value, so push order is [value, slot]
# We warm up the slot first by doing an SLOAD to get consistent warm access cost
SSTORE_CONFIG = MarginalOpcodeConfig(
    name="SSTORE",
    opcode=Op.SSTORE,
    max_op_count=51,
    step=17,  # 4 data points
    stack_args=[MAX_U256, 100],  # value, slot (SSTORE pops slot first)
    pops_per_op=2,
    pushes_per_op=0,
    num_calls=1200,  # Scaled for 150M cycles target
    setup_code=Op.POP(Op.SLOAD(100)),  # Warm up slot 100 first
)

# TLOAD: Transient storage load (EIP-1153) - 100 gas
TLOAD_CONFIG = MarginalOpcodeConfig(
    name="TLOAD",
    opcode=Op.TLOAD,
    max_op_count=300,
    step=100,  # 4 data points
    stack_args=[0],  # Transient slot 0
    pops_per_op=1,
    pushes_per_op=1,
    num_calls=5000,  # Calculated for 500K+ gas
)

# TSTORE: Transient storage store (EIP-1153) - 100 gas
# Note: TSTORE pops slot first, then value, so push order is [value, slot]
TSTORE_CONFIG = MarginalOpcodeConfig(
    name="TSTORE",
    opcode=Op.TSTORE,
    max_op_count=99,
    step=33,  # 4 data points
    stack_args=[MAX_U256, 0],  # value, slot (TSTORE pops slot first)
    pops_per_op=2,
    pushes_per_op=0,
    num_calls=2000,  # Scaled for 150M cycles target
)


# ============================================================================
# CONTROL FLOW OPCODES
# ============================================================================

# JUMPDEST is just a marker (1 gas) - essentially a no-op
# Note: JUMPDEST has pushes_per_op=0, pops_per_op=0, so uses noop-padding
# which doesn't add any overhead - each JUMPDEST just costs 1 gas
JUMPDEST_CONFIG = MarginalOpcodeConfig(
    name="JUMPDEST",
    opcode=Op.JUMPDEST,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=0,
    num_calls=8000,  # 2x for short proving time
)

# PC pushes the program counter value
PC_CONFIG = MarginalOpcodeConfig(
    name="PC",
    opcode=Op.PC,
    max_op_count=600,
    step=200,  # 4 data points
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
)


# ============================================================================
# JUMP / JUMPI - Special handling required (control flow opcodes)
# These cannot use generate_marginal_program directly since they change control flow.
# We use a loop-based approach where we control the iteration count.
# ============================================================================

def generate_jump_program(op_count: int, max_op_count: int) -> Bytecode:
    """
    Generate a JUMP program following gas-cost-estimator's approach EXACTLY.
    
    Each combo is self-contained - JUMP jumps to its own JUMPDEST:
    - Real combo: PUSH3(dest) + JUMP + JUMPDEST = 6 bytes, gas = 3+8+1 = 12
      (dest points to the JUMPDEST in this same combo)
    - Noop combo: PUSH3(dest) + JUMPDEST = 5 bytes, gas = 3+1 = 4
      (dest points to the JUMPDEST in this combo, no JUMP executed)
    
    Note: Combo sizes differ (6 vs 5 bytes), but positions are calculated dynamically.
    Marginal gas = 12 - 4 = 8 (exactly JUMP gas!)
    """
    # Build bytecode by calculating positions dynamically (like gas-cost-estimator)
    bytecode_hex = ""
    
    for i in range(max_op_count):
        current_pc = len(bytecode_hex) // 2
        
        if i < op_count:
            # Real combo: PUSH3(dest) + JUMP + JUMPDEST = 6 bytes
            # JUMPDEST is at: current_pc + 1 (PUSH3 opcode) + 3 (value) + 1 (JUMP) = current_pc + 5
            jumpdest_pc = current_pc + 1 + 3 + 1
            # PUSH3 = 0x62, JUMP = 0x56, JUMPDEST = 0x5b
            bytecode_hex += f"62{jumpdest_pc:06x}565b"
        else:
            # Noop combo: PUSH3(dest) + JUMPDEST = 5 bytes (no JUMP!)
            # JUMPDEST is at: current_pc + 1 (PUSH3 opcode) + 3 (value) = current_pc + 4
            jumpdest_pc = current_pc + 1 + 3
            bytecode_hex += f"62{jumpdest_pc:06x}5b"
    
    # Add epilogue as hex:
    # SSTORE(SUCCESS_SLOT=0, SUCCESS_MARKER=0xdead)
    # PUSH2 0xdead = 61dead, PUSH1 0 = 6000, SSTORE = 55, STOP = 00
    bytecode_hex += "61dead60005500"
    
    # Return as raw bytes wrapped in Bytecode container
    # For raw bytes, must specify stack items (0 pops, 0 pushes for complete program)
    return Bytecode(bytes.fromhex(bytecode_hex), popped_stack_items=0, pushed_stack_items=0, terminating=True)


def generate_jumpi_program(op_count: int, max_op_count: int) -> Bytecode:
    """
    Generate a JUMPI program with CONSTANT overhead (true marginal).
    
    Following gas-cost-estimator's approach:
    - Push max_op_count conditions upfront (CONSTANT)
    - Each JUMPI consumes one condition
    - Unused conditions stay on stack (fine for gas measurement)
    
    Structure:
    1. Push max_op_count conditions (CONSTANT)
    2. Run max_op_count combos:
       - Real combo (i < op_count): PUSH3(dest) + JUMPI + JUMPDEST
       - Noop combo (i >= op_count): PUSH3(dest) + JUMPDEST
    
    Gas breakdown:
      Condition pushes: max_op_count * PUSH1(3) = CONSTANT
      Real combo: PUSH3(3) + JUMPI(10) + JUMPDEST(1) = 14 gas
      Noop combo: PUSH3(3) + JUMPDEST(1) = 4 gas
      
      op_count=0:  max*3 (conditions) + max*4 (noops) = constant
      op_count=N:  max*3 (conditions) + N*14 + (max-N)*4
                 = max*3 + N*14 + max*4 - N*4
                 = max*3 + max*4 + N*10
                 
      Marginal = N*10 / N = 10 gas per JUMPI ✓
    """
    bytecode_hex = ""
    
    # 1. Push max_op_count conditions upfront (CONSTANT overhead)
    for _ in range(max_op_count):
        bytecode_hex += "6001"  # PUSH1 1 (true condition)
    
    # 2. Run combos
    for i in range(max_op_count):
        current_pc = len(bytecode_hex) // 2
        
        if i < op_count:
            # Real combo: PUSH3(dest) + JUMPI + JUMPDEST = 6 bytes
            jumpdest_pc = current_pc + 1 + 3 + 1
            bytecode_hex += f"62{jumpdest_pc:06x}575b"
        else:
            # Noop combo: PUSH3(dest) + JUMPDEST = 5 bytes
            jumpdest_pc = current_pc + 1 + 3
            bytecode_hex += f"62{jumpdest_pc:06x}5b"
    
    # 3. Epilogue (POPs for unused conditions not needed - stack cleanup is optional)
    bytecode_hex += "61dead60005500"
    
    return Bytecode(bytes.fromhex(bytecode_hex), popped_stack_items=0, pushed_stack_items=0, terminating=True)


def generate_jump_target(op_count: int, max_op_count: int) -> Bytecode:
    """
    Generate JUMP target contract for caller-contract approach.
    Similar to generate_jump_program but without SSTORE (compatible with STATICCALL).
    """
    bytecode_hex = ""
    
    for i in range(max_op_count):
        current_pc = len(bytecode_hex) // 2
        
        if i < op_count:
            # Real combo: PUSH3(dest) + JUMP + JUMPDEST = 6 bytes
            jumpdest_pc = current_pc + 1 + 3 + 1
            bytecode_hex += f"62{jumpdest_pc:06x}565b"
        else:
            # Noop combo: PUSH3(dest) + JUMPDEST = 5 bytes
            jumpdest_pc = current_pc + 1 + 3
            bytecode_hex += f"62{jumpdest_pc:06x}5b"
    
    # Just STOP (no SSTORE - called via STATICCALL)
    bytecode_hex += "00"
    
    return Bytecode(bytes.fromhex(bytecode_hex), popped_stack_items=0, pushed_stack_items=0, terminating=True)


def generate_jumpi_target(op_count: int, max_op_count: int) -> Bytecode:
    """
    Generate JUMPI target contract for caller-contract approach.
    Similar to generate_jumpi_program but without SSTORE (compatible with STATICCALL).
    """
    bytecode_hex = ""
    
    # Push max_op_count conditions upfront
    for _ in range(max_op_count):
        bytecode_hex += "6001"  # PUSH1 1 (true condition)
    
    for i in range(max_op_count):
        current_pc = len(bytecode_hex) // 2
        
        if i < op_count:
            # Real combo: PUSH3(dest) + JUMPI + JUMPDEST = 6 bytes
            jumpdest_pc = current_pc + 1 + 3 + 1
            bytecode_hex += f"62{jumpdest_pc:06x}575b"
        else:
            # Noop combo: PUSH3(dest) + JUMPDEST = 5 bytes
            jumpdest_pc = current_pc + 1 + 3
            bytecode_hex += f"62{jumpdest_pc:06x}5b"
    
    # Just STOP (no SSTORE - called via STATICCALL)
    bytecode_hex += "00"
    
    return Bytecode(bytes.fromhex(bytecode_hex), popped_stack_items=0, pushed_stack_items=0, terminating=True)


# ============================================================================
# LOG OPCODES - LOG0 through LOG4
# Gas: 375 + 8*size + 375*num_topics
# ============================================================================

# LOG opcodes with 1KB data for worst-case (aligned with gas-cost-estimator)
def _generate_log_setup() -> Bytecode:
    """Generate setup code that fills memory with 1KB (32 x 32 bytes) of data."""
    code = Bytecode()
    for i in range(32):
        offset = i * 32
        code += Op.MSTORE(offset, MAX_U256)
    return code


def generate_log_program(
    opcode: Op,
    num_topics: int,
    op_count: int,
    max_op_count: int,
) -> Bytecode:
    """
    Generate a LOG program EXACTLY like gas-cost-estimator's pg_marginal.py.
    
    Structure:
    1. Fill 32 bytes of memory: PUSH32 0xff...ff, PUSH1 0, MSTORE
    2. Push arguments for ALL max_op_count operations:
       - For each: (PUSH1 0xff) * num_topics + PUSH1 0x20 (size) + PUSH1 0x00 (offset)
    3. Execute op_count LOG opcodes
    4. STOP
    
    Note: No success marker - we verify via gas_used instead.
    """
    code = Bytecode()
    
    # 1. Fill first 32 bytes of memory with 0xff
    code += Op.MSTORE(0, MAX_U256)
    
    # 2. Push arguments for ALL max_op_count operations
    # LOG* takes: offset, size, topic0, topic1, ... (bottom to top on stack)
    # So we push: offset, size, topics (in that order)
    # Each LOG will pop from top: topics first, then size, then offset
    for _ in range(max_op_count):
        code += Op.PUSH1[0]      # offset = 0
        code += Op.PUSH1[32]     # size = 32 bytes
        for _ in range(num_topics):
            code += Op.PUSH1[0xFF]  # topic = 0xff
    
    # 3. Execute op_count LOG opcodes
    for _ in range(op_count):
        code += opcode
    
    # 4. Just STOP - remaining stack values are fine
    code += Op.STOP
    
    return code


def generate_dup_program(
    dup_n: int,
    op_count: int,
    max_op_count: int,
) -> Bytecode:
    """
    Generate a DUP program following gas-cost-estimator's approach EXACTLY.
    
    Structure (matching gas-cost-estimator):
    1. Push empty_push_count values (max_op_count POPs worth) as padding
    2. Push dup_n initial values onto stack (for DUP to work on)
    3. Interleaved: [DUP] + ([POP] + [DUP]) * (op_count - 1) if op_count >= 1
       OR just POPs if op_count == 0
    4. End with remaining POPs to balance stack
    
    Key insight: Total POPs is CONSTANT (max_op_count), only DUP count varies.
    Marginal gas = DUP gas (3 gas)
    """
    code = Bytecode()
    
    nreturns = 1  # DUP returns 1 value
    total_pop_count = max_op_count * nreturns  # Constant number of POPs
    
    # 1. Push padding values so POPs have something to pop
    for _ in range(total_pop_count):
        code += Op.PUSH0
    
    # 2. Push dup_n initial values for DUP to duplicate from
    for i in range(dup_n):
        code += Op.PUSH1[i]
    
    dup_opcode = getattr(Op, f"DUP{dup_n}")
    
    # 3. Interleaved DUP + POP pattern (matching gas-cost-estimator)
    if op_count == 0:
        # No DUPs, just all POPs
        for _ in range(total_pop_count):
            code += Op.POP
    else:
        # Pattern: DUP + (POP + DUP) * (op_count - 1) + end_pops
        interleaved_count = op_count - 1
        end_pop_count = total_pop_count - interleaved_count * nreturns
        
        # First DUP
        code += dup_opcode
        
        # Interleaved POP + DUP
        for _ in range(interleaved_count):
            code += Op.POP
            code += dup_opcode
        
        # End POPs (balance the stack)
        for _ in range(end_pop_count):
            code += Op.POP
    
    # 4. Pop the dup_n initial values
    for _ in range(dup_n):
        code += Op.POP
    
    # 5. Write success marker
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code


def generate_swap_program(
    swap_n: int,
    op_count: int,
    max_op_count: int,
) -> Bytecode:
    """
    Generate a SWAP program following gas-cost-estimator's approach.
    
    Structure:
    1. Push swap_n+1 initial values onto stack
    2. For op_count iterations: execute SWAP (swaps don't change stack size)
    3. Pop the initial values
    4. Write success marker
    
    SWAP doesn't change stack size, so we can do many iterations.
    """
    code = Bytecode()
    
    # 1. Push swap_n+1 initial values
    for i in range(swap_n + 1):
        code += Op.PUSH1[i]
    
    # 2. Execute op_count SWAP operations
    swap_opcode = getattr(Op, f"SWAP{swap_n}")
    for _ in range(op_count):
        code += swap_opcode
    
    # 3. Pop the initial values
    for _ in range(swap_n + 1):
        code += Op.POP
    
    # 4. Write success marker
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code


# ============================================================================
# EXTERNAL CALL OPCODES - CALL, CALLCODE, DELEGATECALL, STATICCALL
# These call other contracts/addresses
# ============================================================================


def _generate_call_target_code() -> Bytecode:
    """
    Generate simple target contract code that just returns immediately.
    The target stores a value and returns, minimal gas consumption.
    """
    return Op.STOP


def generate_call_program(op_count: int, call_opcode: Op, max_op_count: int) -> Bytecode:
    """
    Generate a program that executes CALL-type opcode op_count times.
    
    Uses noop-based padding similar to other non-returning opcodes:
    - For op_count executions: push args + execute call + pop result
    - For remaining (max_op_count - op_count): just push args (no call)
    
    The target is a simple contract that just STOPs.
    """
    code = Bytecode()
    
    # Note: We'll need to set target_address later when deploying
    # For now, use placeholder - will be replaced in test function
    
    noop_count = max_op_count - op_count
    
    # Execute op_count real calls
    for _ in range(op_count):
        if call_opcode == Op.CALL or call_opcode == Op.CALLCODE:
            # CALL(gas, addr, value, argsOffset, argsSize, retOffset, retSize)
            code += Op.POP(
                call_opcode(Op.GAS, 0xCAFE, 0, 0, 0, 0, 0)  # 0xCAFE = placeholder
            )
        else:
            # DELEGATECALL/STATICCALL(gas, addr, argsOffset, argsSize, retOffset, retSize)
            code += Op.POP(
                call_opcode(Op.GAS, 0xCAFE, 0, 0, 0, 0)  # 0xCAFE = placeholder
            )
    
    # Execute noop_count "noops" (same pushes, no call)
    for _ in range(noop_count):
        if call_opcode == Op.CALL or call_opcode == Op.CALLCODE:
            # Push 7 values (CALL/CALLCODE args) and pop them
            for _ in range(7):
                code += Op.PUSH0
            for _ in range(7):
                code += Op.POP
        else:
            # Push 6 values (DELEGATECALL/STATICCALL args) and pop them
            for _ in range(6):
                code += Op.PUSH0
            for _ in range(6):
                code += Op.POP
    
    # Write success marker
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code


# ============================================================================
# CALL-FAMILY OPCODES - Using loop-based caller contract approach
# CALL, CALLCODE, DELEGATECALL, STATICCALL
# ============================================================================

# Loop-based caller contracts for each CALL variant
# These use a fixed-size loop structure, allowing much higher call counts

def generate_caller_with_call(target_address: Address, num_calls: int) -> Bytecode:
    """
    Generate caller contract that uses CALL in a loop.
    CALL(gas, addr, value, argsOffset, argsSize, retOffset, retSize) -> success
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
    
    # CALL: gas, addr, value, argsOffset, argsSize, retOffset, retSize
    code += Op.PUSH1(0)                   # retSize
    code += Op.PUSH1(0)                   # retOffset  
    code += Op.PUSH1(0)                   # argsSize
    code += Op.PUSH1(0)                   # argsOffset
    code += Op.PUSH1(0)                   # value
    code += Op.PUSH20(target_address)     # address
    code += Op.GAS                        # gas
    code += Op.CALL
    code += Op.POP                        # pop success flag
    
    # Decrement counter
    code += Op.PUSH1(1)
    code += Op.SWAP1
    code += Op.SUB
    
    # Loop back if counter > 0
    code += Op.DUP1
    code += Op.PUSH2(loop_start_offset)
    code += Op.JUMPI
    
    # Done - write success marker
    code += Op.POP
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code


def generate_caller_with_callcode(target_address: Address, num_calls: int) -> Bytecode:
    """
    Generate caller contract that uses CALLCODE in a loop.
    CALLCODE(gas, addr, value, argsOffset, argsSize, retOffset, retSize) -> success
    """
    code = Bytecode()
    
    if num_calls <= 0xFF:
        code += Op.PUSH1(num_calls)
    elif num_calls <= 0xFFFF:
        code += Op.PUSH2(num_calls)
    else:
        code += Op.PUSH3(num_calls)
    
    loop_start_offset = len(bytes(code))
    code += Op.JUMPDEST
    
    # CALLCODE: gas, addr, value, argsOffset, argsSize, retOffset, retSize
    code += Op.PUSH1(0)                   # retSize
    code += Op.PUSH1(0)                   # retOffset  
    code += Op.PUSH1(0)                   # argsSize
    code += Op.PUSH1(0)                   # argsOffset
    code += Op.PUSH1(0)                   # value
    code += Op.PUSH20(target_address)     # address
    code += Op.GAS                        # gas
    code += Op.CALLCODE
    code += Op.POP
    
    code += Op.PUSH1(1)
    code += Op.SWAP1
    code += Op.SUB
    
    code += Op.DUP1
    code += Op.PUSH2(loop_start_offset)
    code += Op.JUMPI
    
    code += Op.POP
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code


def generate_caller_with_delegatecall(target_address: Address, num_calls: int) -> Bytecode:
    """
    Generate caller contract that uses DELEGATECALL in a loop.
    DELEGATECALL(gas, addr, argsOffset, argsSize, retOffset, retSize) -> success
    """
    code = Bytecode()
    
    if num_calls <= 0xFF:
        code += Op.PUSH1(num_calls)
    elif num_calls <= 0xFFFF:
        code += Op.PUSH2(num_calls)
    else:
        code += Op.PUSH3(num_calls)
    
    loop_start_offset = len(bytes(code))
    code += Op.JUMPDEST
    
    # DELEGATECALL: gas, addr, argsOffset, argsSize, retOffset, retSize (no value!)
    code += Op.PUSH1(0)                   # retSize
    code += Op.PUSH1(0)                   # retOffset  
    code += Op.PUSH1(0)                   # argsSize
    code += Op.PUSH1(0)                   # argsOffset
    code += Op.PUSH20(target_address)     # address
    code += Op.GAS                        # gas
    code += Op.DELEGATECALL
    code += Op.POP
    
    code += Op.PUSH1(1)
    code += Op.SWAP1
    code += Op.SUB
    
    code += Op.DUP1
    code += Op.PUSH2(loop_start_offset)
    code += Op.JUMPI
    
    code += Op.POP
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code


def generate_caller_with_staticcall(target_address: Address, num_calls: int) -> Bytecode:
    """
    Generate caller contract that uses STATICCALL in a loop.
    STATICCALL(gas, addr, argsOffset, argsSize, retOffset, retSize) -> success
    """
    code = Bytecode()
    
    if num_calls <= 0xFF:
        code += Op.PUSH1(num_calls)
    elif num_calls <= 0xFFFF:
        code += Op.PUSH2(num_calls)
    else:
        code += Op.PUSH3(num_calls)
    
    loop_start_offset = len(bytes(code))
    code += Op.JUMPDEST
    
    # STATICCALL: gas, addr, argsOffset, argsSize, retOffset, retSize (no value!)
    code += Op.PUSH1(0)                   # retSize
    code += Op.PUSH1(0)                   # retOffset  
    code += Op.PUSH1(0)                   # argsSize
    code += Op.PUSH1(0)                   # argsOffset
    code += Op.PUSH20(target_address)     # address
    code += Op.GAS                        # gas
    code += Op.STATICCALL
    code += Op.POP
    
    code += Op.PUSH1(1)
    code += Op.SWAP1
    code += Op.SUB
    
    code += Op.DUP1
    code += Op.PUSH2(loop_start_offset)
    code += Op.JUMPI
    
    code += Op.POP
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code


# Configuration for CALL-family opcodes with simplified noop approach
# Stack-limited but caller-amplified for high total op counts
# Stack limit: 1024, each noop leaves +5 or +6 items
# Safe max_op_count: ~150 (with buffer), caller amplifies to 150 × N total ops
CALL_NUM_CALLS = 500  # Number of caller loop iterations
CALL_MAX_OP_COUNT = 99  # Target contract executes up to 99 CALLs per invocation
CALL_STEP = 33  # 4 data points


def _generate_target_with_inner_calls(
    inner_target: Address, op_count: int, max_op_count: int, call_op
) -> Bytecode:
    """
    Generate a target contract that makes op_count calls to inner_target,
    with simplified noop padding to ensure perfect marginal property.
    
    NEW APPROACH (simplified, perfect gas marginality):
    - Noops: Push args + POP one (stack accumulates, but no call)
    - Real calls: Push args + CALL + POP result
    
    Gas analysis:
    - Noop:      PUSH×6/7 (18/21 gas) + POP (2 gas) = 20/23 gas
    - Real call: PUSH×6/7 (18/21 gas) + CALL (100 gas) + POP (2 gas) = 120/123 gas
    - Marginal:  100 gas (exactly the CALL cost!)
    
    Stack analysis:
    - Each noop leaves +5 items (STATICCALL/DELEGATECALL) or +6 items (CALL/CALLCODE)
    - Stack limit = 1024, so max noops ≈ 150-170
    - With caller amplification, total ops = max_op_count × CALL_NUM_CALLS
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
    """Marginal cost test for CALL opcode using loop-based caller."""
    # Inner target: just stops
    inner_target = pre.deploy_contract(code=Op.STOP)
    
    # Target contract: makes op_count CALLs to inner_target per invocation
    # With noop padding for proper marginality
    target_code = _generate_target_with_inner_calls(
        inner_target, op_count, CALL_MAX_OP_COUNT, Op.CALL
    )
    target = pre.deploy_contract(code=target_code)
    
    # Caller contract: loops CALL_NUM_CALLS times, calling target
    caller_code = generate_caller_with_call(target, CALL_NUM_CALLS)
    caller = pre.deploy_contract(code=caller_code)
    
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(gas_limit=CALLER_GAS_LIMIT), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALL_MAX_OP_COUNT, CALL_STEP),
    ids=lambda x: f"op_count_{x * CALL_NUM_CALLS}",
)
def test_marginal_callcode(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CALLCODE opcode using loop-based caller."""
    inner_target = pre.deploy_contract(code=Op.STOP)
    # With noop padding for proper marginality
    target_code = _generate_target_with_inner_calls(
        inner_target, op_count, CALL_MAX_OP_COUNT, Op.CALLCODE
    )
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_with_callcode(target, CALL_NUM_CALLS)
    caller = pre.deploy_contract(code=caller_code)
    
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(gas_limit=CALLER_GAS_LIMIT), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALL_MAX_OP_COUNT, CALL_STEP),
    ids=lambda x: f"op_count_{x * CALL_NUM_CALLS}",
)
def test_marginal_delegatecall(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for DELEGATECALL opcode using loop-based caller."""
    inner_target = pre.deploy_contract(code=Op.STOP)
    # With noop padding for proper marginality
    target_code = _generate_target_with_inner_calls(
        inner_target, op_count, CALL_MAX_OP_COUNT, Op.DELEGATECALL
    )
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_with_delegatecall(target, CALL_NUM_CALLS)
    caller = pre.deploy_contract(code=caller_code)
    
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(gas_limit=CALLER_GAS_LIMIT), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALL_MAX_OP_COUNT, CALL_STEP),
    ids=lambda x: f"op_count_{x * CALL_NUM_CALLS}",
)
def test_marginal_staticcall(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for STATICCALL opcode using loop-based caller."""
    inner_target = pre.deploy_contract(code=Op.STOP)
    # With noop padding for proper marginality
    target_code = _generate_target_with_inner_calls(
        inner_target, op_count, CALL_MAX_OP_COUNT, Op.STATICCALL
    )
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_with_staticcall(target, CALL_NUM_CALLS)
    caller = pre.deploy_contract(code=caller_code)
    
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(gas_limit=CALLER_GAS_LIMIT), pre=pre, post=post, tx=tx)


# ============================================================================
# CREATE OPCODES - CREATE, CREATE2 (simplified noop approach)
# These deploy new contracts
# ============================================================================

# For CREATE: Each call to target increments nonce, so each CREATE gets unique address
# For CREATE2: We use a storage counter as salt to generate unique addresses

# Stack-limited: each noop leaves +2 items (3 pushed, 1 popped)
# Safe max_op_count: ~400 (with buffer), caller amplifies total
CREATE_NUM_CALLS = 400  # 2x for short proving time
CREATE_MAX_OP_COUNT = 21  # Target executes up to 21 CREATEs per call
CREATE_STEP = 7  # 4 data points


def _generate_target_with_creates(op_count: int, max_op_count: int) -> Bytecode:
    """
    Generate a target contract that executes op_count CREATE operations,
    with simplified noop padding to ensure perfect marginal property.
    
    NEW APPROACH (simplified, perfect gas marginality):
    - Noops: Push 3 args + POP one (stack accumulates, but no CREATE)
    - Real calls: Push 3 args + CREATE + POP result
    
    Gas analysis:
    - Noop:   PUSH×3 (9 gas) + POP (2 gas) = 11 gas
    - Real:   PUSH×3 (9 gas) + CREATE (32000 gas) + POP (2 gas) = 32011 gas
    - Marginal: 32000 gas (exactly the CREATE cost!)
    
    Stack analysis:
    - Each noop leaves +2 items (3 pushed, 1 popped)
    - Stack limit = 1024, so max noops ≈ 500
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
    with simplified noop padding to ensure perfect marginal property.
    
    NEW APPROACH (real ops first, then noops):
    - Real CREATE2s first (while stack is clean, DUP1 works correctly)
    - Then update salt counter (before noops pollute the stack)
    - Then noops (push 4 args + POP one, stack accumulates but unused)
    
    Gas analysis:
    - Noop:   PUSH×4 (12 gas) + POP (2 gas) = 14 gas
    - Real:   PUSH×4 (12 gas) + CREATE2 (32000 gas) + POP (2 gas) = 32014 gas
    - Marginal: 32000 gas (exactly the CREATE2 cost!)
    
    Stack analysis:
    - Each noop leaves +3 items (4 pushed, 1 popped)
    - Stack limit = 1024, so max noops ≈ 340
    
    Uses a storage slot as a counter for unique salts.
    """
    code = Bytecode()
    
    # Store minimal initcode in memory
    code += Op.MSTORE(0, 0x600080f3 << (28 * 8))
    
    # Load current salt counter from storage slot 0x100
    salt_slot = 0x100
    code += Op.SLOAD(salt_slot)  # salt counter on stack
    
    noop_count = max_op_count - op_count
    
    # ========== REAL CREATE2s FIRST (while stack is clean) ==========
    for i in range(op_count):
        # CREATE2(value, offset, size, salt) -> address
        code += Op.DUP1                       # duplicate salt counter (works while stack is clean)
        code += Op.PUSH2(i)                   # add offset for unique salt
        code += Op.ADD                        # salt = counter + i
        code += Op.PUSH1(4)                   # size
        code += Op.PUSH1(0)                   # offset
        code += Op.PUSH1(0)                   # value
        code += Op.CREATE2                    # Uses unique salt
        code += Op.POP                        # pop created address
    
    # Update salt counter NOW (while stack still has just salt_counter on top)
    code += Op.PUSH2(max_op_count)
    code += Op.ADD                            # new counter = old + max_op_count
    code += Op.PUSH2(salt_slot)
    code += Op.SSTORE                         # save updated counter
    
    # ========== NOOPS AFTER (push args + pop one, stack accumulates but unused) ==========
    for i in range(noop_count):
        # Push same arguments as real CREATE2
        # Salt value doesn't matter for noops, just push dummy values
        code += Op.PUSH2(op_count + i)        # dummy salt
        code += Op.PUSH1(4)                   # size
        code += Op.PUSH1(0)                   # offset
        code += Op.PUSH1(0)                   # value
        # Just pop one item - NO CREATE2, stack accumulates (but we're done after this)
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
    """Marginal cost test for CREATE opcode using loop-based caller."""
    # Target contract executes op_count CREATEs per call
    # With noop padding for proper marginality
    target_code = _generate_target_with_creates(op_count, CREATE_MAX_OP_COUNT)
    target = pre.deploy_contract(code=target_code)
    
    # Caller loops CREATE_NUM_CALLS times, calling target
    caller_code = generate_caller_with_call(target, CREATE_NUM_CALLS)
    caller = pre.deploy_contract(code=caller_code)
    
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(gas_limit=CALLER_GAS_LIMIT), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CREATE_MAX_OP_COUNT, CREATE_STEP),
    ids=lambda x: f"op_count_{x * CREATE_NUM_CALLS}",
)
def test_marginal_create2(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CREATE2 opcode using loop-based caller."""
    # Target contract executes op_count CREATE2s per call with unique salts
    # With noop padding for proper marginality
    target_code = _generate_target_with_create2s(op_count, CREATE_MAX_OP_COUNT)
    target = pre.deploy_contract(code=target_code)
    
    # Caller loops CREATE_NUM_CALLS times, calling target
    caller_code = generate_caller_with_call(target, CREATE_NUM_CALLS)
    caller = pre.deploy_contract(code=caller_code)
    
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(gas_limit=CALLER_GAS_LIMIT), pre=pre, post=post, tx=tx)


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
    step=100,
    stack_args=[0xDEAD],  # Query balance of address 0xDEAD
    pops_per_op=1,
    pushes_per_op=1,
    num_calls=1000,
    setup_code=Op.POP(Op.BALANCE(0xDEAD)),  # Warm up address 0xDEAD first
)

# EXTCODESIZE: pops address, pushes code size
# Cold access: 2600 gas, warm access: 100 gas
# Warm up the target address first for consistent marginal measurement
EXTCODESIZE_CONFIG = MarginalOpcodeConfig(
    name="EXTCODESIZE",
    opcode=Op.EXTCODESIZE,
    max_op_count=99,
    step=33,  # 4 data points
    stack_args=[0xDEAD],  # Query code size of address 0xDEAD
    pops_per_op=1,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
    setup_code=Op.POP(Op.EXTCODESIZE(0xDEAD)),  # Warm up address 0xDEAD first
)

# EXTCODEHASH: pops address, pushes code hash
# Cold access: 2600 gas, warm access: 100 gas
# Warm up the target address first for consistent marginal measurement
EXTCODEHASH_CONFIG = MarginalOpcodeConfig(
    name="EXTCODEHASH",
    opcode=Op.EXTCODEHASH,
    max_op_count=100,
    step=25,  # ~5 data points
    stack_args=[0xDEAD],  # Query code hash of address 0xDEAD
    pops_per_op=1,
    pushes_per_op=1,
    num_calls=2000,  # Calculated for 500K+ gas
    setup_code=Op.POP(Op.EXTCODEHASH(0xDEAD)),  # Warm up address 0xDEAD first
)

# EXTCODECOPY: address, destOffset, offset, size (4 args, copies external code to memory)
# Warm up both memory and target address for consistent marginal measurement
EXTCODECOPY_CONFIG = MarginalOpcodeConfig(
    name="EXTCODECOPY",
    opcode=Op.EXTCODECOPY,
    max_op_count=51,
    step=17,  # 4 data points
    stack_args=[256, 0, 0, 0xDEAD],  # size=256, offset=0, destOffset=0, address (pushed in reverse pop order)
    pops_per_op=4,
    pushes_per_op=0,
    num_calls=2000,  # Scaled for 150M cycles target
    setup_code=Op.MSTORE(0, 0) + Op.POP(Op.EXTCODESIZE(0xDEAD)),  # Pre-expand memory + warm up address
)


# ============================================================================
# CALLER-CONTRACT TESTS FOR LOW-GAS OPCODES
# ============================================================================
# These use the caller-contract approach to amplify effective op_count.
# Effective op_count = NUM_CALLS × op_count_per_call
#
# This is useful for opcodes with low gas costs where single-contract tests
# don't provide enough gas variation for meaningful linear regression.
# ============================================================================

# Arithmetic opcodes
test_add = _create_caller_test(ADD_CONFIG)
test_sub = _create_caller_test(SUB_CONFIG)
test_mul = _create_caller_test(MUL_CONFIG)
test_div = _create_caller_test(DIV_CONFIG)
test_sdiv = _create_caller_test(SDIV_CONFIG)
test_mod = _create_caller_test(MOD_CONFIG)
test_smod = _create_caller_test(SMOD_CONFIG)
test_addmod = _create_caller_test(ADDMOD_CONFIG)
test_mulmod = _create_caller_test(MULMOD_CONFIG)
test_signextend = _create_caller_test(SIGNEXTEND_CONFIG)

# Comparison opcodes
test_lt = _create_caller_test(LT_CONFIG)
test_gt = _create_caller_test(GT_CONFIG)
test_slt = _create_caller_test(SLT_CONFIG)
test_sgt = _create_caller_test(SGT_CONFIG)
test_eq = _create_caller_test(EQ_CONFIG)
test_iszero = _create_caller_test(ISZERO_CONFIG)

# Bitwise opcodes
test_and = _create_caller_test(AND_CONFIG)
test_or = _create_caller_test(OR_CONFIG)
test_xor = _create_caller_test(XOR_CONFIG)
test_not = _create_caller_test(NOT_CONFIG)
test_byte = _create_caller_test(BYTE_CONFIG)
test_shl = _create_caller_test(SHL_CONFIG)
test_shr = _create_caller_test(SHR_CONFIG)
test_sar = _create_caller_test(SAR_CONFIG)

# Stack opcodes
test_push0 = _create_caller_test(PUSH0_CONFIG)
test_push1 = _create_caller_test(PUSH1_CONFIG)
test_push16 = _create_caller_test(PUSH16_CONFIG)
test_push32 = _create_caller_test(PUSH32_CONFIG)
test_pop = _create_caller_test(POP_CONFIG)

# Environment opcodes
test_address = _create_caller_test(ADDRESS_CONFIG)
test_origin = _create_caller_test(ORIGIN_CONFIG)
test_caller = _create_caller_test(CALLER_CONFIG)
test_callvalue = _create_caller_test(CALLVALUE_CONFIG)
test_calldatasize = _create_caller_test(CALLDATASIZE_CONFIG)
test_codesize = _create_caller_test(CODESIZE_CONFIG)
test_gasprice = _create_caller_test(GASPRICE_CONFIG)
test_returndatasize = _create_caller_test(RETURNDATASIZE_CONFIG)
test_gas = _create_caller_test(GAS_CONFIG)

# Block info opcodes
test_coinbase = _create_caller_test(COINBASE_CONFIG)
test_timestamp = _create_caller_test(TIMESTAMP_CONFIG)
test_number = _create_caller_test(NUMBER_CONFIG)
test_prevrandao = _create_caller_test(PREVRANDAO_CONFIG)
test_gaslimit = _create_caller_test(GASLIMIT_CONFIG)
test_chainid = _create_caller_test(CHAINID_CONFIG)
test_selfbalance = _create_caller_test(SELFBALANCE_CONFIG)
test_caller_basefee = _create_caller_test(BASEFEE_CONFIG)
test_blobbasefee = _create_caller_test(BLOBBASEFEE_CONFIG)
test_pc = _create_caller_test(PC_CONFIG)

# Memory opcodes
test_mload = _create_caller_test(MLOAD_CONFIG)
test_mstore = _create_caller_test(MSTORE_CONFIG)
test_mstore8 = _create_caller_test(MSTORE8_CONFIG)
test_msize = _create_caller_test(MSIZE_CONFIG)
test_mcopy = _create_caller_test(MCOPY_CONFIG)
test_codecopy = _create_caller_test(CODECOPY_CONFIG)
test_calldatacopy = _create_caller_test(CALLDATACOPY_CONFIG)
test_calldataload = _create_caller_test(CALLDATALOAD_CONFIG)
test_returndatacopy = _create_caller_test(RETURNDATACOPY_CONFIG)

# Storage opcodes (SLOAD, TLOAD work with STATICCALL)
test_sload = _create_caller_test(SLOAD_CONFIG)
test_tload = _create_caller_test(TLOAD_CONFIG)

# External code opcodes
test_balance = _create_caller_test(BALANCE_CONFIG)
test_extcodesize = _create_caller_test(EXTCODESIZE_CONFIG)
test_extcodehash = _create_caller_test(EXTCODEHASH_CONFIG)
test_extcodecopy = _create_caller_test(EXTCODECOPY_CONFIG)
# Note: BLOCKHASH caller test omitted - fails with high op_count due to large bytecode
test_blobhash = _create_caller_test(BLOBHASH_CONFIG)

# Hash opcodes
test_keccak256 = _create_caller_test(KECCAK256_CONFIG)

# Misc opcodes
test_jumpdest = _create_caller_test(JUMPDEST_CONFIG)
test_exp = _create_caller_test(EXP_CONFIG)

# Control flow opcodes
test_jump = _create_caller_test(JUMP_CONFIG, generate_jump_target)
test_jumpi = _create_caller_test(JUMPI_CONFIG, generate_jumpi_target)

# State-modifying opcodes (require CALL instead of STATICCALL)
test_sstore = _create_caller_test(SSTORE_CONFIG, needs_call=True)
test_tstore = _create_caller_test(TSTORE_CONFIG, needs_call=True)

# DUP opcodes
test_dup1 = _create_caller_test(
    DUP1_CONFIG, lambda oc, moc: generate_dup_target(DUP1_CONFIG.variant, oc, moc)
)
test_dup8 = _create_caller_test(
    DUP8_CONFIG, lambda oc, moc: generate_dup_target(DUP8_CONFIG.variant, oc, moc)
)
test_dup16 = _create_caller_test(
    DUP16_CONFIG, lambda oc, moc: generate_dup_target(DUP16_CONFIG.variant, oc, moc)
)

# SWAP opcodes
test_swap1 = _create_caller_test(
    SWAP1_CONFIG, lambda oc, moc: generate_swap_target(SWAP1_CONFIG.variant, oc, moc)
)
test_swap8 = _create_caller_test(
    SWAP8_CONFIG, lambda oc, moc: generate_swap_target(SWAP8_CONFIG.variant, oc, moc)
)
test_swap16 = _create_caller_test(
    SWAP16_CONFIG, lambda oc, moc: generate_swap_target(SWAP16_CONFIG.variant, oc, moc)
)

# LOG opcodes (require CALL instead of STATICCALL)
test_log0 = _create_caller_test(
    LOG0_CONFIG, lambda oc, moc: generate_log_program(Op.LOG0, LOG0_CONFIG.topic_count, oc, moc)
)
test_log1 = _create_caller_test(
    LOG1_CONFIG, lambda oc, moc: generate_log_program(Op.LOG1, LOG1_CONFIG.topic_count, oc, moc)
)
test_log2 = _create_caller_test(
    LOG2_CONFIG, lambda oc, moc: generate_log_program(Op.LOG2, LOG2_CONFIG.topic_count, oc, moc)
)
test_log3 = _create_caller_test(
    LOG3_CONFIG, lambda oc, moc: generate_log_program(Op.LOG3, LOG3_CONFIG.topic_count, oc, moc)
)
test_log4 = _create_caller_test(
    LOG4_CONFIG, lambda oc, moc: generate_log_program(Op.LOG4, LOG4_CONFIG.topic_count, oc, moc)
)


# ============================================================================
# HELPER FUNCTIONS FOR DUP/SWAP TARGET GENERATION
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
    """Generate SWAP target for caller (no SSTORE, just STOP)."""
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
