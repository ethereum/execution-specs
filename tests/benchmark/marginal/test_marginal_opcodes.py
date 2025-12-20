"""
Marginal cost estimation tests for EVM opcodes.

This module implements the "marginal approach" for gas cost estimation as described
in the gas-cost-estimator project. The key insight is:

1. Generate a series of programs where only the number of target opcodes varies
2. Keep everything else constant (stack setup, cleanup, or noop padding)
3. The marginal cost of an opcode can be extracted via linear regression on execution times

Two strategies are used depending on whether the opcode returns values:

Strategy 1: POP-based padding (for opcodes with pushes_per_op > 0)
    | PUSH0 × max_op_count × pushes_per_op | Empty values for POP padding    |
    | PUSH args × max_op_count             | Stack setup (same for all)      |
    | OPCODE + (POP × pushes_per_op + OPCODE) × (op_count-1) | Interleaved   |
    | POP × remaining                      | Constant total POPs             |
    | SSTORE + STOP                        | Success marker                  |

Strategy 2: Noop-based padding (for opcodes with pushes_per_op == 0, like MSTORE)
    | (PUSH args + OPCODE) × op_count      | Real operations                 |
    | (PUSH args) × (max_op_count - op_count) | Noops (push only, no op)     |
    | SSTORE + STOP                        | Success marker                  |

The program with op_count=K+1 differs from op_count=K by exactly ONE instance
of the target opcode, enabling marginal cost estimation.
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
    """Maximum number of opcode instances."""

    step: int
    """Step size for op_count increments."""

    stack_args: List[int]
    """Values to push for each opcode instance (one per argument)."""

    pops_per_op: int
    """Number of values the opcode pops from stack."""

    pushes_per_op: int
    """Number of values the opcode pushes to stack."""

    setup_code: Bytecode | None = None
    """Optional setup code to run before the main loop (e.g., memory init)."""


# Define opcode configurations
# Low-cost opcodes: 200 max_op_count, step of 20
# High-cost opcodes: 20 max_op_count, step of 5

# ============================================================================
# ARITHMETIC OPCODES - Use max 256-bit values for worst case
# ============================================================================
MAX_U256 = (1 << 256) - 1  # Maximum uint256 value
MAX_S256_NEG = 1 << 255     # Most negative signed int256

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

ADD_CONFIG = MarginalOpcodeConfig(
    name="ADD",
    opcode=Op.ADD,
    max_op_count=300,  # 300 * 3 = 900 < 1024
    step=30,
    stack_args=[MAX_U256, MAX_U256],  # Worst case: max values
    pops_per_op=2,
    pushes_per_op=1,
)

MUL_CONFIG = MarginalOpcodeConfig(
    name="MUL",
    opcode=Op.MUL,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, MAX_U256],  # Worst case: max values
    pops_per_op=2,
    pushes_per_op=1,
)

SUB_CONFIG = MarginalOpcodeConfig(
    name="SUB",
    opcode=Op.SUB,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

DIV_CONFIG = MarginalOpcodeConfig(
    name="DIV",
    opcode=Op.DIV,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, 3],  # Worst case: large dividend, small divisor
    pops_per_op=2,
    pushes_per_op=1,
)

SDIV_CONFIG = MarginalOpcodeConfig(
    name="SDIV",
    opcode=Op.SDIV,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, 3],  # Worst case: large dividend, small divisor
    pops_per_op=2,
    pushes_per_op=1,
)

MOD_CONFIG = MarginalOpcodeConfig(
    name="MOD",
    opcode=Op.MOD,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, 3],  # Large dividend, small divisor
    pops_per_op=2,
    pushes_per_op=1,
)

SMOD_CONFIG = MarginalOpcodeConfig(
    name="SMOD",
    opcode=Op.SMOD,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, 3],
    pops_per_op=2,
    pushes_per_op=1,
)

ADDMOD_CONFIG = MarginalOpcodeConfig(
    name="ADDMOD",
    opcode=Op.ADDMOD,
    max_op_count=200,  # 200 * 4 = 800 < 1024
    step=20,
    stack_args=[MAX_U256, MAX_U256, 3],  # (a + b) mod N, small modulus
    pops_per_op=3,
    pushes_per_op=1,
)

MULMOD_CONFIG = MarginalOpcodeConfig(
    name="MULMOD",
    opcode=Op.MULMOD,
    max_op_count=200,
    step=20,
    stack_args=[MAX_U256, MAX_U256, 3],  # (a * b) mod N, small modulus
    pops_per_op=3,
    pushes_per_op=1,
)

# EXP is expensive: 10 + 50 * byte_length_of_exponent
# With 32-byte exponent = 10 + 50 * 32 = 1610 gas
EXP_CONFIG = MarginalOpcodeConfig(
    name="EXP",
    opcode=Op.EXP,
    max_op_count=150,
    step=15,
    stack_args=[MAX_U256, MAX_U256],  # Worst case: max base and exponent
    pops_per_op=2,
    pushes_per_op=1,
)

SIGNEXTEND_CONFIG = MarginalOpcodeConfig(
    name="SIGNEXTEND",
    opcode=Op.SIGNEXTEND,
    max_op_count=300,  # 300 * 3 = 900 < 1024
    step=30,
    stack_args=[31, MAX_U256],  # Extend from byte 31 (full 256-bit)
    pops_per_op=2,
    pushes_per_op=1,
)

# ============================================================================
# COMPARISON OPCODES
# ============================================================================

LT_CONFIG = MarginalOpcodeConfig(
    name="LT",
    opcode=Op.LT,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

GT_CONFIG = MarginalOpcodeConfig(
    name="GT",
    opcode=Op.GT,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

SLT_CONFIG = MarginalOpcodeConfig(
    name="SLT",
    opcode=Op.SLT,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

SGT_CONFIG = MarginalOpcodeConfig(
    name="SGT",
    opcode=Op.SGT,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

EQ_CONFIG = MarginalOpcodeConfig(
    name="EQ",
    opcode=Op.EQ,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

ISZERO_CONFIG = MarginalOpcodeConfig(
    name="ISZERO",
    opcode=Op.ISZERO,
    max_op_count=450,  # 450 * 2 = 900 < 1024
    step=45,
    stack_args=[MAX_U256],
    pops_per_op=1,
    pushes_per_op=1,
)

# ============================================================================
# BITWISE OPCODES
# ============================================================================

AND_CONFIG = MarginalOpcodeConfig(
    name="AND",
    opcode=Op.AND,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

OR_CONFIG = MarginalOpcodeConfig(
    name="OR",
    opcode=Op.OR,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

XOR_CONFIG = MarginalOpcodeConfig(
    name="XOR",
    opcode=Op.XOR,
    max_op_count=300,
    step=30,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

NOT_CONFIG = MarginalOpcodeConfig(
    name="NOT",
    opcode=Op.NOT,
    max_op_count=450,  # 450 * 2 = 900 < 1024
    step=45,
    stack_args=[MAX_U256],
    pops_per_op=1,
    pushes_per_op=1,
)

BYTE_CONFIG = MarginalOpcodeConfig(
    name="BYTE",
    opcode=Op.BYTE,
    max_op_count=300,  # 300 * 3 = 900 < 1024
    step=30,
    stack_args=[31, MAX_U256],  # Extract byte 31 from max value
    pops_per_op=2,
    pushes_per_op=1,
)

SHL_CONFIG = MarginalOpcodeConfig(
    name="SHL",
    opcode=Op.SHL,
    max_op_count=300,  # 300 * 3 = 900 < 1024
    step=30,
    stack_args=[255, MAX_U256],  # Shift left by 255 bits (max)
    pops_per_op=2,
    pushes_per_op=1,
)

SHR_CONFIG = MarginalOpcodeConfig(
    name="SHR",
    opcode=Op.SHR,
    max_op_count=300,
    step=30,
    stack_args=[255, MAX_U256],  # Shift right by 255 bits (max)
    pops_per_op=2,
    pushes_per_op=1,
)

SAR_CONFIG = MarginalOpcodeConfig(
    name="SAR",
    opcode=Op.SAR,
    max_op_count=300,
    step=30,
    stack_args=[255, MAX_U256],  # Arithmetic shift right by 255
    pops_per_op=2,
    pushes_per_op=1,
)

# ============================================================================
# KECCAK256 OPCODE - Variable cost based on input size
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
    max_op_count=100,
    step=10,
    stack_args=[0, 8192],  # offset=0, size=8KB for worst-case
    pops_per_op=2,
    pushes_per_op=1,
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
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

PUSH1_CONFIG = MarginalOpcodeConfig(
    name="PUSH1",
    opcode=Op.PUSH1(0xFF),  # Push max 1-byte value
    max_op_count=600,
    step=60,
    stack_args=[],  # PUSH doesn't consume stack
    pops_per_op=0,
    pushes_per_op=1,
)

PUSH16_CONFIG = MarginalOpcodeConfig(
    name="PUSH16",
    opcode=Op.PUSH16(MAX_U256 >> 128),  # Max 16-byte value
    max_op_count=500,
    step=50,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

PUSH32_CONFIG = MarginalOpcodeConfig(
    name="PUSH32",
    opcode=Op.PUSH32(MAX_U256),  # Max 32-byte value
    max_op_count=350,
    step=35,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

# DUP opcodes need N items on stack before they can duplicate
# Use small values (PUSH1) to minimize bytecode size - stack depth matters, not value
# Contract code limit is 24,576 bytes

# DUP1 uses custom generator - see generate_dup_program
DUP1_MAX_OP_COUNT = 300
DUP1_STEP = 30

# DUP8, DUP16, SWAP8, SWAP16 need special handling - see generate_dup_program/generate_swap_program
# Stack limit constraints: Need base items + space for max_op_count duplicates
# DUP8: 8 base items, each DUP adds 1, each POP removes 1, net = 0 per iteration
# So max_op_count is limited only by bytecode size, not stack
DUP8_MAX_OP_COUNT = 300
DUP8_STEP = 30
DUP16_MAX_OP_COUNT = 300
DUP16_STEP = 30

# SWAP opcodes need N+1 items on stack
# SWAP1 uses custom generator - see generate_swap_program
SWAP1_MAX_OP_COUNT = 300
SWAP1_STEP = 30

# SWAP8, SWAP16 use custom generator - see generate_swap_program
SWAP8_MAX_OP_COUNT = 300
SWAP8_STEP = 30
SWAP16_MAX_OP_COUNT = 300
SWAP16_STEP = 30

# POP opcode: pops 1 value, pushes 0 (2 gas)
# For marginal testing, we need to provide values to pop
POP_CONFIG = MarginalOpcodeConfig(
    name="POP",
    opcode=Op.POP,
    max_op_count=600,
    step=60,
    stack_args=[0],  # Push 0 to pop (using PUSH0 is cheapest)
    pops_per_op=1,
    pushes_per_op=0,
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
# ADD opcode tests (low cost - step 10)
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(ADD_CONFIG.max_op_count, ADD_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_add(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for ADD opcode.

    Generates a program with exactly `op_count` ADD instructions.
    The test verifies execution completed successfully via storage marker.
    """
    code = generate_marginal_program(ADD_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        sender=sender,
    )

    # Verify execution completed successfully (didn't revert)
    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# Helper to generate test for any opcode config
# ============================================================================

def _create_opcode_test(config: MarginalOpcodeConfig, gas_limit: int = 1_000_000):
    """Factory to create test function for an opcode config."""
    @pytest.mark.valid_from("Prague")
    @pytest.mark.parametrize(
        "op_count",
        generate_op_counts(config.max_op_count, config.step),
        ids=lambda x: f"op_count_{x}",
    )
    def test_func(
        state_test: StateTestFiller,
        pre: Alloc,
        op_count: int,
    ) -> None:
        code = generate_marginal_program(config, op_count)
        contract = pre.deploy_contract(code=code)
        sender = pre.fund_eoa()

        tx = Transaction(
            to=contract,
            gas_limit=gas_limit,
            sender=sender,
        )

        post = {
            contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
        }

        state_test(env=Environment(), pre=pre, post=post, tx=tx)
    
    return test_func


# ============================================================================
# ARITHMETIC OPCODE TESTS
# ============================================================================

@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(MUL_CONFIG.max_op_count, MUL_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_mul(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for MUL opcode with max 256-bit values."""
    code = generate_marginal_program(MUL_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SUB_CONFIG.max_op_count, SUB_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_sub(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SUB opcode."""
    code = generate_marginal_program(SUB_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(DIV_CONFIG.max_op_count, DIV_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_div(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for DIV opcode."""
    code = generate_marginal_program(DIV_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SDIV_CONFIG.max_op_count, SDIV_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_sdiv(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SDIV opcode with signed values."""
    code = generate_marginal_program(SDIV_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(MOD_CONFIG.max_op_count, MOD_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_mod(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for MOD opcode."""
    code = generate_marginal_program(MOD_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SMOD_CONFIG.max_op_count, SMOD_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_smod(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SMOD opcode."""
    code = generate_marginal_program(SMOD_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(ADDMOD_CONFIG.max_op_count, ADDMOD_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_addmod(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for ADDMOD opcode."""
    code = generate_marginal_program(ADDMOD_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(MULMOD_CONFIG.max_op_count, MULMOD_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_mulmod(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for MULMOD opcode."""
    code = generate_marginal_program(MULMOD_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(EXP_CONFIG.max_op_count, EXP_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_exp(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for EXP opcode with 32-byte exponent (worst case)."""
    code = generate_marginal_program(EXP_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SIGNEXTEND_CONFIG.max_op_count, SIGNEXTEND_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_signextend(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SIGNEXTEND opcode."""
    code = generate_marginal_program(SIGNEXTEND_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# COMPARISON OPCODE TESTS
# ============================================================================

@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(LT_CONFIG.max_op_count, LT_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_lt(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for LT opcode."""
    code = generate_marginal_program(LT_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(GT_CONFIG.max_op_count, GT_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_gt(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for GT opcode."""
    code = generate_marginal_program(GT_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SLT_CONFIG.max_op_count, SLT_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_slt(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SLT opcode with signed values."""
    code = generate_marginal_program(SLT_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SGT_CONFIG.max_op_count, SGT_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_sgt(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SGT opcode with signed values."""
    code = generate_marginal_program(SGT_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(EQ_CONFIG.max_op_count, EQ_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_eq(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for EQ opcode."""
    code = generate_marginal_program(EQ_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(ISZERO_CONFIG.max_op_count, ISZERO_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_iszero(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for ISZERO opcode."""
    code = generate_marginal_program(ISZERO_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# BITWISE OPCODE TESTS
# ============================================================================

@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(AND_CONFIG.max_op_count, AND_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_and(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for AND opcode."""
    code = generate_marginal_program(AND_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(OR_CONFIG.max_op_count, OR_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_or(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for OR opcode."""
    code = generate_marginal_program(OR_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(XOR_CONFIG.max_op_count, XOR_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_xor(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for XOR opcode."""
    code = generate_marginal_program(XOR_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(NOT_CONFIG.max_op_count, NOT_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_not(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for NOT opcode."""
    code = generate_marginal_program(NOT_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BYTE_CONFIG.max_op_count, BYTE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_byte(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for BYTE opcode."""
    code = generate_marginal_program(BYTE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SHL_CONFIG.max_op_count, SHL_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_shl(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SHL opcode with max shift."""
    code = generate_marginal_program(SHL_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SHR_CONFIG.max_op_count, SHR_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_shr(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SHR opcode with max shift."""
    code = generate_marginal_program(SHR_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SAR_CONFIG.max_op_count, SAR_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_sar(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SAR opcode with max shift on negative value."""
    code = generate_marginal_program(SAR_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# KECCAK256 opcode tests (medium cost - step 5)
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(KECCAK256_CONFIG.max_op_count, KECCAK256_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_keccak256(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for KECCAK256 opcode.

    Generates a program with exactly `op_count` KECCAK256 instructions.
    Memory is pre-initialized with data to hash.
    The test verifies execution completed successfully via storage marker.
    """
    code = generate_marginal_program(KECCAK256_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=5_000_000,  # Higher gas limit for KECCAK256
        sender=sender,
    )

    # Verify execution completed successfully (didn't revert)
    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# STACK OPCODE TESTS (PUSH, DUP, SWAP)
# ============================================================================

@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(PUSH0_CONFIG.max_op_count, PUSH0_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_push0(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for PUSH0 opcode (EIP-3855)."""
    code = generate_marginal_program(PUSH0_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(PUSH1_CONFIG.max_op_count, PUSH1_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_push1(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for PUSH1 opcode."""
    code = generate_marginal_program(PUSH1_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(PUSH16_CONFIG.max_op_count, PUSH16_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_push16(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for PUSH16 opcode."""
    code = generate_marginal_program(PUSH16_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(PUSH32_CONFIG.max_op_count, PUSH32_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_push32(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for PUSH32 opcode with max 256-bit value."""
    code = generate_marginal_program(PUSH32_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(DUP1_MAX_OP_COUNT, DUP1_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_dup1(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for DUP1 opcode."""
    code = generate_dup_program(1, op_count, DUP1_MAX_OP_COUNT)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(DUP8_MAX_OP_COUNT, DUP8_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_dup8(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for DUP8 opcode."""
    code = generate_dup_program(8, op_count, DUP8_MAX_OP_COUNT)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(DUP16_MAX_OP_COUNT, DUP16_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_dup16(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for DUP16 opcode."""
    code = generate_dup_program(16, op_count, DUP16_MAX_OP_COUNT)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SWAP1_MAX_OP_COUNT, SWAP1_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_swap1(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SWAP1 opcode."""
    code = generate_swap_program(1, op_count, SWAP1_MAX_OP_COUNT)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SWAP8_MAX_OP_COUNT, SWAP8_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_swap8(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SWAP8 opcode."""
    code = generate_swap_program(8, op_count, SWAP8_MAX_OP_COUNT)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SWAP16_MAX_OP_COUNT, SWAP16_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_swap16(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SWAP16 opcode."""
    code = generate_swap_program(16, op_count, SWAP16_MAX_OP_COUNT)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(POP_CONFIG.max_op_count, POP_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_pop(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for POP opcode."""
    code = generate_marginal_program(POP_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# ENVIRONMENT OPCODES - Return context/environment info (no input, push 1)
# ============================================================================

ADDRESS_CONFIG = MarginalOpcodeConfig(
    name="ADDRESS",
    opcode=Op.ADDRESS,
    max_op_count=600,
    step=60,
    stack_args=[],  # No input
    pops_per_op=0,
    pushes_per_op=1,
)

ORIGIN_CONFIG = MarginalOpcodeConfig(
    name="ORIGIN",
    opcode=Op.ORIGIN,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

CALLER_CONFIG = MarginalOpcodeConfig(
    name="CALLER",
    opcode=Op.CALLER,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

CALLVALUE_CONFIG = MarginalOpcodeConfig(
    name="CALLVALUE",
    opcode=Op.CALLVALUE,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

CALLDATASIZE_CONFIG = MarginalOpcodeConfig(
    name="CALLDATASIZE",
    opcode=Op.CALLDATASIZE,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

CODESIZE_CONFIG = MarginalOpcodeConfig(
    name="CODESIZE",
    opcode=Op.CODESIZE,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

GASPRICE_CONFIG = MarginalOpcodeConfig(
    name="GASPRICE",
    opcode=Op.GASPRICE,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

RETURNDATASIZE_CONFIG = MarginalOpcodeConfig(
    name="RETURNDATASIZE",
    opcode=Op.RETURNDATASIZE,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

GAS_CONFIG = MarginalOpcodeConfig(
    name="GAS",
    opcode=Op.GAS,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(ADDRESS_CONFIG.max_op_count, ADDRESS_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_address(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for ADDRESS opcode."""
    code = generate_marginal_program(ADDRESS_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(ORIGIN_CONFIG.max_op_count, ORIGIN_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_origin(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for ORIGIN opcode."""
    code = generate_marginal_program(ORIGIN_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALLER_CONFIG.max_op_count, CALLER_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_caller(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CALLER opcode."""
    code = generate_marginal_program(CALLER_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALLVALUE_CONFIG.max_op_count, CALLVALUE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_callvalue(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CALLVALUE opcode."""
    code = generate_marginal_program(CALLVALUE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALLDATASIZE_CONFIG.max_op_count, CALLDATASIZE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_calldatasize(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CALLDATASIZE opcode."""
    code = generate_marginal_program(CALLDATASIZE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CODESIZE_CONFIG.max_op_count, CODESIZE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_codesize(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CODESIZE opcode."""
    code = generate_marginal_program(CODESIZE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(GASPRICE_CONFIG.max_op_count, GASPRICE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_gasprice(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for GASPRICE opcode."""
    code = generate_marginal_program(GASPRICE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(RETURNDATASIZE_CONFIG.max_op_count, RETURNDATASIZE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_returndatasize(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for RETURNDATASIZE opcode."""
    code = generate_marginal_program(RETURNDATASIZE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(GAS_CONFIG.max_op_count, GAS_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_gas(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for GAS opcode."""
    code = generate_marginal_program(GAS_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# BLOCK INFO OPCODES - Return block context (no input, push 1)
# ============================================================================

COINBASE_CONFIG = MarginalOpcodeConfig(
    name="COINBASE",
    opcode=Op.COINBASE,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

TIMESTAMP_CONFIG = MarginalOpcodeConfig(
    name="TIMESTAMP",
    opcode=Op.TIMESTAMP,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

NUMBER_CONFIG = MarginalOpcodeConfig(
    name="NUMBER",
    opcode=Op.NUMBER,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

PREVRANDAO_CONFIG = MarginalOpcodeConfig(
    name="PREVRANDAO",
    opcode=Op.PREVRANDAO,  # Was DIFFICULTY pre-merge
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

GASLIMIT_CONFIG = MarginalOpcodeConfig(
    name="GASLIMIT",
    opcode=Op.GASLIMIT,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

CHAINID_CONFIG = MarginalOpcodeConfig(
    name="CHAINID",
    opcode=Op.CHAINID,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

SELFBALANCE_CONFIG = MarginalOpcodeConfig(
    name="SELFBALANCE",
    opcode=Op.SELFBALANCE,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

BASEFEE_CONFIG = MarginalOpcodeConfig(
    name="BASEFEE",
    opcode=Op.BASEFEE,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

BLOBBASEFEE_CONFIG = MarginalOpcodeConfig(
    name="BLOBBASEFEE",
    opcode=Op.BLOBBASEFEE,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(COINBASE_CONFIG.max_op_count, COINBASE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_coinbase(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for COINBASE opcode."""
    code = generate_marginal_program(COINBASE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(TIMESTAMP_CONFIG.max_op_count, TIMESTAMP_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_timestamp(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for TIMESTAMP opcode."""
    code = generate_marginal_program(TIMESTAMP_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(NUMBER_CONFIG.max_op_count, NUMBER_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_number(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for NUMBER opcode."""
    code = generate_marginal_program(NUMBER_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(PREVRANDAO_CONFIG.max_op_count, PREVRANDAO_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_prevrandao(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for PREVRANDAO opcode (was DIFFICULTY)."""
    code = generate_marginal_program(PREVRANDAO_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(GASLIMIT_CONFIG.max_op_count, GASLIMIT_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_gaslimit(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for GASLIMIT opcode."""
    code = generate_marginal_program(GASLIMIT_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CHAINID_CONFIG.max_op_count, CHAINID_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_chainid(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CHAINID opcode."""
    code = generate_marginal_program(CHAINID_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SELFBALANCE_CONFIG.max_op_count, SELFBALANCE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_selfbalance(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SELFBALANCE opcode."""
    code = generate_marginal_program(SELFBALANCE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BASEFEE_CONFIG.max_op_count, BASEFEE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_basefee(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for BASEFEE opcode."""
    code = generate_marginal_program(BASEFEE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BLOBBASEFEE_CONFIG.max_op_count, BLOBBASEFEE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_blobbasefee(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for BLOBBASEFEE opcode."""
    code = generate_marginal_program(BLOBBASEFEE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# MEMORY OPCODES - Memory read/write operations
# ============================================================================

# Memory is pre-expanded via setup_code to avoid memory expansion costs in measurements

MLOAD_CONFIG = MarginalOpcodeConfig(
    name="MLOAD",
    opcode=Op.MLOAD,
    max_op_count=500,
    step=50,
    stack_args=[0],  # offset - read from offset 0
    pops_per_op=1,
    pushes_per_op=1,
    setup_code=Op.MSTORE(0, MAX_U256),  # Pre-expand memory with data
)

MSTORE_CONFIG = MarginalOpcodeConfig(
    name="MSTORE",
    opcode=Op.MSTORE,
    max_op_count=500,
    step=50,
    stack_args=[MAX_U256, 0],  # value, offset (MSTORE pops offset first)
    pops_per_op=2,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, 0),  # Pre-expand memory
)

MSTORE8_CONFIG = MarginalOpcodeConfig(
    name="MSTORE8",
    opcode=Op.MSTORE8,
    max_op_count=500,
    step=50,
    stack_args=[0xFF, 0],  # value, offset (MSTORE8 pops offset first)
    pops_per_op=2,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, 0),  # Pre-expand memory
)

MSIZE_CONFIG = MarginalOpcodeConfig(
    name="MSIZE",
    opcode=Op.MSIZE,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
    setup_code=Op.MSTORE(0, 0),  # Pre-expand memory so MSIZE returns non-zero
)

# CALLDATACOPY: destOffset, offset, size (copies from calldata to memory)
# Use 1KB size for worst-case (aligned with gas-cost-estimator)
CALLDATACOPY_CONFIG = MarginalOpcodeConfig(
    name="CALLDATACOPY",
    opcode=Op.CALLDATACOPY,
    max_op_count=300,
    step=30,
    stack_args=[0, 0, 1024],  # destOffset=0, offset=0, size=1KB
    pops_per_op=3,
    pushes_per_op=0,
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
RETURNDATACOPY_CONFIG = MarginalOpcodeConfig(
    name="RETURNDATACOPY",
    opcode=Op.RETURNDATACOPY,
    max_op_count=300,
    step=30,
    stack_args=[128, 0, 64],  # destOffset=128, offset=0, size=64 (copy returndata)
    pops_per_op=3,
    pushes_per_op=0,
    setup_code=_generate_returndatacopy_setup(),
)

# CODECOPY: destOffset, offset, size (copies from code to memory)
CODECOPY_CONFIG = MarginalOpcodeConfig(
    name="CODECOPY",
    opcode=Op.CODECOPY,
    max_op_count=300,
    step=30,
    stack_args=[0, 0, 1024],  # destOffset=0, offset=0, size=1KB
    pops_per_op=3,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, 0),  # Pre-expand memory
)

# MCOPY: destOffset, srcOffset, size (copies within memory) - EIP-5656
MCOPY_CONFIG = MarginalOpcodeConfig(
    name="MCOPY",
    opcode=Op.MCOPY,
    max_op_count=300,
    step=30,
    stack_args=[4096, 0, 1024],  # destOffset=4096, srcOffset=0, size=1KB (non-overlapping)
    pops_per_op=3,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, MAX_U256) + Op.MSTORE(4096, 0),  # Pre-expand memory regions
)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(MLOAD_CONFIG.max_op_count, MLOAD_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_mload(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for MLOAD opcode."""
    code = generate_marginal_program(MLOAD_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(MSTORE_CONFIG.max_op_count, MSTORE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_mstore(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for MSTORE opcode."""
    code = generate_marginal_program(MSTORE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(MSTORE8_CONFIG.max_op_count, MSTORE8_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_mstore8(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for MSTORE8 opcode."""
    code = generate_marginal_program(MSTORE8_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(MSIZE_CONFIG.max_op_count, MSIZE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_msize(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for MSIZE opcode."""
    code = generate_marginal_program(MSIZE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALLDATACOPY_CONFIG.max_op_count, CALLDATACOPY_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_calldatacopy(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CALLDATACOPY opcode."""
    code = generate_marginal_program(CALLDATACOPY_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    # Send some calldata to copy
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender, data=bytes(64))
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.skip(reason="RETURNDATACOPY setup needs investigation")
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(RETURNDATACOPY_CONFIG.max_op_count, RETURNDATACOPY_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_returndatacopy(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for RETURNDATACOPY opcode."""
    code = generate_marginal_program(RETURNDATACOPY_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CODECOPY_CONFIG.max_op_count, CODECOPY_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_codecopy(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CODECOPY opcode."""
    code = generate_marginal_program(CODECOPY_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(MCOPY_CONFIG.max_op_count, MCOPY_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_mcopy(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for MCOPY opcode (EIP-5656)."""
    code = generate_marginal_program(MCOPY_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# DATA ACCESS OPCODES
# ============================================================================

# CALLDATALOAD: pops offset, pushes 32 bytes from calldata
CALLDATALOAD_CONFIG = MarginalOpcodeConfig(
    name="CALLDATALOAD",
    opcode=Op.CALLDATALOAD,
    max_op_count=500,
    step=50,
    stack_args=[0],  # Load from offset 0
    pops_per_op=1,
    pushes_per_op=1,
)

# BLOCKHASH: pops block number, pushes hash (or 0 if out of range)
BLOCKHASH_CONFIG = MarginalOpcodeConfig(
    name="BLOCKHASH",
    opcode=Op.BLOCKHASH,
    max_op_count=300,
    step=30,
    stack_args=[0],  # Block 0 (will return 0 but still executes)
    pops_per_op=1,
    pushes_per_op=1,
)

# BLOBHASH: pops blob index, pushes versioned hash (or 0 if out of range)
BLOBHASH_CONFIG = MarginalOpcodeConfig(
    name="BLOBHASH",
    opcode=Op.BLOBHASH,
    max_op_count=500,
    step=50,
    stack_args=[0],  # Blob index 0 (will return 0 if no blobs)
    pops_per_op=1,
    pushes_per_op=1,
)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALLDATALOAD_CONFIG.max_op_count, CALLDATALOAD_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_calldataload(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CALLDATALOAD opcode."""
    code = generate_marginal_program(CALLDATALOAD_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    # Send calldata so loads are meaningful
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender, data=bytes(64))
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


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
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BLOBHASH_CONFIG.max_op_count, BLOBHASH_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_blobhash(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for BLOBHASH opcode (EIP-4844)."""
    code = generate_marginal_program(BLOBHASH_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# STORAGE OPCODES - SLOAD, SSTORE, TLOAD, TSTORE
# ============================================================================

# SLOAD: First access to cold slot costs 2100 gas, warm access costs 100 gas
# For marginal testing, we warm up the slot first to measure consistent warm access cost
SLOAD_CONFIG = MarginalOpcodeConfig(
    name="SLOAD",
    opcode=Op.SLOAD,
    max_op_count=100,
    step=10,
    stack_args=[100],  # Storage slot 100 (different from SUCCESS_SLOT)
    pops_per_op=1,
    pushes_per_op=1,
    setup_code=Op.POP(Op.SLOAD(100)),  # Warm up slot 100 first
)

# SSTORE: Complex gas rules (cold access, dirty/clean, refunds)
# Slot 100, value MAX_U256 - repeated writes to same slot
# Note: SSTORE pops slot first, then value, so push order is [value, slot]
# We warm up the slot first by doing an SLOAD to get consistent warm access cost
SSTORE_CONFIG = MarginalOpcodeConfig(
    name="SSTORE",
    opcode=Op.SSTORE,
    max_op_count=50,
    step=5,
    stack_args=[MAX_U256, 100],  # value, slot (SSTORE pops slot first)
    pops_per_op=2,
    pushes_per_op=0,
    setup_code=Op.POP(Op.SLOAD(100)),  # Warm up slot 100 first
)

# TLOAD: Transient storage load (EIP-1153) - 100 gas
TLOAD_CONFIG = MarginalOpcodeConfig(
    name="TLOAD",
    opcode=Op.TLOAD,
    max_op_count=200,
    step=20,
    stack_args=[0],  # Transient slot 0
    pops_per_op=1,
    pushes_per_op=1,
)

# TSTORE: Transient storage store (EIP-1153) - 100 gas
# Note: TSTORE pops slot first, then value, so push order is [value, slot]
TSTORE_CONFIG = MarginalOpcodeConfig(
    name="TSTORE",
    opcode=Op.TSTORE,
    max_op_count=100,
    step=10,
    stack_args=[MAX_U256, 0],  # value, slot (TSTORE pops slot first)
    pops_per_op=2,
    pushes_per_op=0,
)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SLOAD_CONFIG.max_op_count, SLOAD_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_sload(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SLOAD opcode (warm access after first)."""
    code = generate_marginal_program(SLOAD_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SSTORE_CONFIG.max_op_count, SSTORE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_sstore(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SSTORE opcode (warm, no value change = 100 gas)."""
    code = generate_marginal_program(SSTORE_CONFIG, op_count)
    # Pre-set slot 100 to MAX_U256 so all SSTOREs are "no value change" (100 gas)
    # This makes the gas cost consistent: warm access (100) + no change (0) = 100 gas
    contract = pre.deploy_contract(code=code, storage={100: MAX_U256})
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender)
    # Slot 100 will still have MAX_U256 after execution (same value written)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER, 100: MAX_U256})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(TLOAD_CONFIG.max_op_count, TLOAD_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_tload(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for TLOAD opcode (EIP-1153)."""
    code = generate_marginal_program(TLOAD_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(TSTORE_CONFIG.max_op_count, TSTORE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_tstore(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for TSTORE opcode (EIP-1153)."""
    code = generate_marginal_program(TSTORE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# CONTROL FLOW OPCODES
# ============================================================================

# JUMPDEST is just a marker (1 gas) - essentially a no-op
JUMPDEST_CONFIG = MarginalOpcodeConfig(
    name="JUMPDEST",
    opcode=Op.JUMPDEST,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=0,
)

# PC pushes the program counter value
PC_CONFIG = MarginalOpcodeConfig(
    name="PC",
    opcode=Op.PC,
    max_op_count=600,
    step=60,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
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
    Generate a JUMPI program following gas-cost-estimator's approach EXACTLY.
    
    Structure:
    1. Push conditions upfront (one per real JUMPI op)
    2. Run combos:
       - Real combo: PUSH3(dest) + JUMPI + JUMPDEST = 6 bytes
         (JUMPI pops dest from PUSH3, then pops condition from earlier push)
       - Noop combo: PUSH3(dest) + JUMPDEST = 5 bytes
         (no JUMPI, so condition stays on stack - that's ok)
    
    Gas per combo:
    - Real: PUSH3(3) + JUMPI(10) + JUMPDEST(1) = 14 gas
    - Noop: PUSH3(3) + JUMPDEST(1) = 4 gas
    
    Gas for condition pushes: op_count * PUSH1(3) = 3*op_count (constant overhead)
    
    Marginal = 14 - 4 = 10 gas (exactly JUMPI gas!)
    """
    bytecode_hex = ""
    
    # 1. Push conditions upfront (one non-zero value per real JUMPI)
    # PUSH1 1 = 6001 (2 bytes each)
    for _ in range(op_count):
        bytecode_hex += "6001"  # PUSH1 1
    
    # 2. Run combos
    for i in range(max_op_count):
        current_pc = len(bytecode_hex) // 2
        
        if i < op_count:
            # Real combo: PUSH3(dest) + JUMPI + JUMPDEST = 6 bytes
            # JUMPDEST at: current_pc + 1 (PUSH3 opcode) + 3 (value) + 1 (JUMPI) = current_pc + 5
            jumpdest_pc = current_pc + 1 + 3 + 1
            # PUSH3 = 0x62, JUMPI = 0x57, JUMPDEST = 0x5b
            bytecode_hex += f"62{jumpdest_pc:06x}575b"
        else:
            # Noop combo: PUSH3(dest) + JUMPDEST = 5 bytes (no JUMPI)
            jumpdest_pc = current_pc + 1 + 3
            bytecode_hex += f"62{jumpdest_pc:06x}5b"
    
    # 3. Add epilogue as hex:
    # SSTORE(SUCCESS_SLOT=0, SUCCESS_MARKER=0xdead)
    # PUSH2 0xdead = 61dead, PUSH1 0 = 6000, SSTORE = 55, STOP = 00
    bytecode_hex += "61dead60005500"
    
    # For raw bytes, must specify stack items (0 pops, 0 pushes for complete program)
    return Bytecode(bytes.fromhex(bytecode_hex), popped_stack_items=0, pushed_stack_items=0, terminating=True)


JUMP_MAX_OP_COUNT = 200
JUMP_STEP = 20
JUMPI_MAX_OP_COUNT = 200
JUMPI_STEP = 20


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(JUMPDEST_CONFIG.max_op_count, JUMPDEST_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_jumpdest(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for JUMPDEST opcode."""
    code = generate_marginal_program(JUMPDEST_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(PC_CONFIG.max_op_count, PC_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_pc(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for PC opcode."""
    code = generate_marginal_program(PC_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(JUMP_MAX_OP_COUNT, JUMP_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_jump(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for JUMP opcode (sequential approach)."""
    code = generate_jump_program(op_count, JUMP_MAX_OP_COUNT)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(JUMPI_MAX_OP_COUNT, JUMPI_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_jumpi(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for JUMPI opcode (sequential approach)."""
    code = generate_jumpi_program(op_count, JUMPI_MAX_OP_COUNT)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


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
    Generate a DUP program following gas-cost-estimator's noop-based approach.
    
    Structure:
    1. Push dup_n initial values onto stack (these stay for the entire program)
    2. For op_count iterations: DUP + POP (real operation)
    3. For (max_op_count - op_count) iterations: PUSH0 + POP (noop - same gas as DUP+POP)
    4. Pop the initial values
    5. Write success marker
    
    Key insight: DUP (3 gas) + POP (2 gas) = 5 gas
                 PUSH0 (2 gas) + POP (2 gas) = 4 gas (close enough for noop)
    Actually: We need exact match. Use PUSH1 (3 gas) + POP (2 gas) = 5 gas as noop
    
    This way, total gas = constant + op_count * DUP_gas
    Because both real and noop cost 5 gas, but noop uses PUSH1 instead of DUP.
    """
    code = Bytecode()
    
    # 1. Push dup_n initial values
    for i in range(dup_n):
        code += Op.PUSH1[i]
    
    dup_opcode = getattr(Op, f"DUP{dup_n}")
    
    # 2. Execute op_count DUP+POP pairs (real operation)
    for _ in range(op_count):
        code += dup_opcode
        code += Op.POP
    
    # 3. For noops: PUSH1 + POP (same 5 gas as DUP + POP, but uses PUSH1 instead of DUP)
    noop_count = max_op_count - op_count
    for _ in range(noop_count):
        code += Op.PUSH1[0]
        code += Op.POP
    
    # 4. Pop the initial values
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


# LOG configs - these use the special generate_log_program function
LOG0_MAX_OP_COUNT = 100
LOG0_STEP = 10
LOG1_MAX_OP_COUNT = 80
LOG1_STEP = 10

LOG2_MAX_OP_COUNT = 60
LOG2_STEP = 10
LOG3_MAX_OP_COUNT = 50
LOG3_STEP = 10
LOG4_MAX_OP_COUNT = 40
LOG4_STEP = 10


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(LOG0_MAX_OP_COUNT, LOG0_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_log0(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for LOG0 opcode (gas-cost-estimator style)."""
    code = generate_log_program(Op.LOG0, 0, op_count, LOG0_MAX_OP_COUNT)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=10_000_000, sender=sender)
    # No success marker - just verify contract exists after execution
    post = {contract: Account()}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(LOG1_MAX_OP_COUNT, LOG1_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_log1(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for LOG1 opcode (gas-cost-estimator style)."""
    code = generate_log_program(Op.LOG1, 1, op_count, LOG1_MAX_OP_COUNT)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=10_000_000, sender=sender)
    post = {contract: Account()}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(LOG2_MAX_OP_COUNT, LOG2_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_log2(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for LOG2 opcode (gas-cost-estimator style)."""
    code = generate_log_program(Op.LOG2, 2, op_count, LOG2_MAX_OP_COUNT)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=10_000_000, sender=sender)
    post = {contract: Account()}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(LOG3_MAX_OP_COUNT, LOG3_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_log3(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for LOG3 opcode (gas-cost-estimator style)."""
    code = generate_log_program(Op.LOG3, 3, op_count, LOG3_MAX_OP_COUNT)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=10_000_000, sender=sender)
    post = {contract: Account()}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(LOG4_MAX_OP_COUNT, LOG4_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_log4(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for LOG4 opcode (gas-cost-estimator style)."""
    code = generate_log_program(Op.LOG4, 4, op_count, LOG4_MAX_OP_COUNT)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=10_000_000, sender=sender)
    post = {contract: Account()}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


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


CALL_MAX_OP_COUNT = 100
CALL_STEP = 10


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALL_MAX_OP_COUNT, CALL_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_call(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CALL opcode."""
    # Deploy target contract
    target = pre.deploy_contract(code=_generate_call_target_code())
    
    # Generate call program with actual target address
    code = Bytecode()
    noop_count = CALL_MAX_OP_COUNT - op_count
    
    for _ in range(op_count):
        code += Op.POP(Op.CALL(Op.GAS, target, 0, 0, 0, 0, 0))
    
    for _ in range(noop_count):
        for _ in range(7):
            code += Op.PUSH0
        for _ in range(7):
            code += Op.POP
    
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALL_MAX_OP_COUNT, CALL_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_callcode(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CALLCODE opcode."""
    target = pre.deploy_contract(code=_generate_call_target_code())
    
    code = Bytecode()
    noop_count = CALL_MAX_OP_COUNT - op_count
    
    for _ in range(op_count):
        code += Op.POP(Op.CALLCODE(Op.GAS, target, 0, 0, 0, 0, 0))
    
    for _ in range(noop_count):
        for _ in range(7):
            code += Op.PUSH0
        for _ in range(7):
            code += Op.POP
    
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALL_MAX_OP_COUNT, CALL_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_delegatecall(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for DELEGATECALL opcode."""
    target = pre.deploy_contract(code=_generate_call_target_code())
    
    code = Bytecode()
    noop_count = CALL_MAX_OP_COUNT - op_count
    
    for _ in range(op_count):
        code += Op.POP(Op.DELEGATECALL(Op.GAS, target, 0, 0, 0, 0))
    
    for _ in range(noop_count):
        for _ in range(6):
            code += Op.PUSH0
        for _ in range(6):
            code += Op.POP
    
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CALL_MAX_OP_COUNT, CALL_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_staticcall(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for STATICCALL opcode."""
    target = pre.deploy_contract(code=_generate_call_target_code())
    
    code = Bytecode()
    noop_count = CALL_MAX_OP_COUNT - op_count
    
    for _ in range(op_count):
        code += Op.POP(Op.STATICCALL(Op.GAS, target, 0, 0, 0, 0))
    
    for _ in range(noop_count):
        for _ in range(6):
            code += Op.PUSH0
        for _ in range(6):
            code += Op.POP
    
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# CREATE OPCODES - CREATE, CREATE2
# These deploy new contracts
# ============================================================================

# Minimal contract bytecode that just STOPs (0x00 = STOP)
# In initcode: just return empty runtime code
MINIMAL_INITCODE = bytes.fromhex("600080f3")  # PUSH1 0, DUP1, RETURN (returns empty code)

CREATE_MAX_OP_COUNT = 50  # CREATE is expensive (32000 gas base)
CREATE_STEP = 5


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CREATE_MAX_OP_COUNT, CREATE_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_create(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CREATE opcode."""
    code = Bytecode()
    noop_count = CREATE_MAX_OP_COUNT - op_count
    
    # Store initcode in memory
    # MINIMAL_INITCODE = 0x600080f3 (4 bytes)
    code += Op.MSTORE(0, 0x600080f3 << (28 * 8))  # Left-align in 32 bytes
    
    # Execute op_count CREATE calls
    # CREATE(value, offset, size) -> address
    for _ in range(op_count):
        code += Op.POP(Op.CREATE(0, 0, 4))  # value=0, offset=0, size=4
    
    # Noop padding: push 3 values and pop them
    for _ in range(noop_count):
        for _ in range(3):
            code += Op.PUSH0
        for _ in range(3):
            code += Op.POP
    
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=10_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


CREATE2_MAX_OP_COUNT = 50
CREATE2_STEP = 5


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(CREATE2_MAX_OP_COUNT, CREATE2_STEP),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_create2(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for CREATE2 opcode."""
    code = Bytecode()
    noop_count = CREATE2_MAX_OP_COUNT - op_count
    
    # Store initcode in memory
    code += Op.MSTORE(0, 0x600080f3 << (28 * 8))
    
    # Execute op_count CREATE2 calls
    # CREATE2(value, offset, size, salt) -> address
    # Use different salts for each call to create different addresses
    for i in range(op_count):
        code += Op.POP(Op.CREATE2(0, 0, 4, i))  # Use i as salt
    
    # Noop padding: push 4 values and pop them
    for _ in range(noop_count):
        for _ in range(4):
            code += Op.PUSH0
        for _ in range(4):
            code += Op.POP
    
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=10_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


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
    max_op_count=100,
    step=10,
    stack_args=[0xDEAD],  # Query balance of address 0xDEAD
    pops_per_op=1,
    pushes_per_op=1,
    setup_code=Op.POP(Op.BALANCE(0xDEAD)),  # Warm up address 0xDEAD first
)

# EXTCODESIZE: pops address, pushes code size
# Cold access: 2600 gas, warm access: 100 gas
# Warm up the target address first for consistent marginal measurement
EXTCODESIZE_CONFIG = MarginalOpcodeConfig(
    name="EXTCODESIZE",
    opcode=Op.EXTCODESIZE,
    max_op_count=100,
    step=10,
    stack_args=[0xDEAD],  # Query code size of address 0xDEAD
    pops_per_op=1,
    pushes_per_op=1,
    setup_code=Op.POP(Op.EXTCODESIZE(0xDEAD)),  # Warm up address 0xDEAD first
)

# EXTCODEHASH: pops address, pushes code hash
# Cold access: 2600 gas, warm access: 100 gas
# Warm up the target address first for consistent marginal measurement
EXTCODEHASH_CONFIG = MarginalOpcodeConfig(
    name="EXTCODEHASH",
    opcode=Op.EXTCODEHASH,
    max_op_count=100,
    step=10,
    stack_args=[0xDEAD],  # Query code hash of address 0xDEAD
    pops_per_op=1,
    pushes_per_op=1,
    setup_code=Op.POP(Op.EXTCODEHASH(0xDEAD)),  # Warm up address 0xDEAD first
)

# EXTCODECOPY: address, destOffset, offset, size (4 args, copies external code to memory)
# Warm up both memory and target address for consistent marginal measurement
EXTCODECOPY_CONFIG = MarginalOpcodeConfig(
    name="EXTCODECOPY",
    opcode=Op.EXTCODECOPY,
    max_op_count=50,
    step=5,
    stack_args=[0xDEAD, 0, 0, 256],  # address, destOffset, offset, size=256 bytes
    pops_per_op=4,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, 0) + Op.POP(Op.EXTCODESIZE(0xDEAD)),  # Pre-expand memory + warm up address
)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(BALANCE_CONFIG.max_op_count, BALANCE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_balance(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for BALANCE opcode (warm access after first)."""
    code = generate_marginal_program(BALANCE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(EXTCODESIZE_CONFIG.max_op_count, EXTCODESIZE_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_extcodesize(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for EXTCODESIZE opcode (warm access after first)."""
    code = generate_marginal_program(EXTCODESIZE_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(EXTCODEHASH_CONFIG.max_op_count, EXTCODEHASH_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_extcodehash(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for EXTCODEHASH opcode (warm access after first)."""
    code = generate_marginal_program(EXTCODEHASH_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(EXTCODECOPY_CONFIG.max_op_count, EXTCODECOPY_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_extcodecopy(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for EXTCODECOPY opcode."""
    code = generate_marginal_program(EXTCODECOPY_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)
