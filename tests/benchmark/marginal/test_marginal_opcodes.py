"""
Marginal cost estimation tests for EVM opcodes.

This module implements the "marginal approach" for gas cost estimation as described
in the gas-cost-estimator project. The key insight is:

1. Generate a series of programs where only the number of target opcodes varies
2. Keep everything else constant (stack setup, cleanup)
3. The marginal cost of an opcode can be extracted via linear regression on execution times

Program layout for an opcode that pops N values and pushes M values:
    | PUSH × max_op_count × N | Stack setup (same for all op_counts)     |
    | (OPCODE + POP×M) × op_count | Execute and clean results           |
    | POP × (max_op_count - op_count) × N | Clean remaining stack items |
    | SSTORE success marker   | Verify execution completed              |
    | STOP                    | Halt                                     |

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

ADD_CONFIG = MarginalOpcodeConfig(
    name="ADD",
    opcode=Op.ADD,
    max_op_count=200,
    step=20,
    stack_args=[MAX_U256, MAX_U256],  # Worst case: max values
    pops_per_op=2,
    pushes_per_op=1,
)

MUL_CONFIG = MarginalOpcodeConfig(
    name="MUL",
    opcode=Op.MUL,
    max_op_count=200,
    step=20,
    stack_args=[MAX_U256, MAX_U256],  # Worst case: max values
    pops_per_op=2,
    pushes_per_op=1,
)

SUB_CONFIG = MarginalOpcodeConfig(
    name="SUB",
    opcode=Op.SUB,
    max_op_count=200,
    step=20,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

DIV_CONFIG = MarginalOpcodeConfig(
    name="DIV",
    opcode=Op.DIV,
    max_op_count=200,
    step=20,
    stack_args=[MAX_U256, MAX_U256],  # Worst case: large dividend/divisor
    pops_per_op=2,
    pushes_per_op=1,
)

SDIV_CONFIG = MarginalOpcodeConfig(
    name="SDIV",
    opcode=Op.SDIV,
    max_op_count=200,
    step=20,
    stack_args=[MAX_S256_NEG, MAX_S256_NEG],  # Worst case: signed max negative
    pops_per_op=2,
    pushes_per_op=1,
)

MOD_CONFIG = MarginalOpcodeConfig(
    name="MOD",
    opcode=Op.MOD,
    max_op_count=200,
    step=20,
    stack_args=[MAX_U256, MAX_U256 - 1],  # Large dividend, slightly smaller divisor
    pops_per_op=2,
    pushes_per_op=1,
)

SMOD_CONFIG = MarginalOpcodeConfig(
    name="SMOD",
    opcode=Op.SMOD,
    max_op_count=200,
    step=20,
    stack_args=[MAX_S256_NEG, MAX_S256_NEG - 1],
    pops_per_op=2,
    pushes_per_op=1,
)

ADDMOD_CONFIG = MarginalOpcodeConfig(
    name="ADDMOD",
    opcode=Op.ADDMOD,
    max_op_count=150,
    step=15,
    stack_args=[MAX_U256, MAX_U256, MAX_U256 - 1],  # (a + b) mod N
    pops_per_op=3,
    pushes_per_op=1,
)

MULMOD_CONFIG = MarginalOpcodeConfig(
    name="MULMOD",
    opcode=Op.MULMOD,
    max_op_count=150,
    step=15,
    stack_args=[MAX_U256, MAX_U256, MAX_U256 - 1],  # (a * b) mod N
    pops_per_op=3,
    pushes_per_op=1,
)

# EXP is expensive: 10 + 50 * byte_length_of_exponent
# With 32-byte exponent = 10 + 50 * 32 = 1610 gas
EXP_CONFIG = MarginalOpcodeConfig(
    name="EXP",
    opcode=Op.EXP,
    max_op_count=10,
    step=2,
    stack_args=[2, MAX_U256],  # base=2, exponent=max (32 bytes) for worst case
    pops_per_op=2,
    pushes_per_op=1,
)

SIGNEXTEND_CONFIG = MarginalOpcodeConfig(
    name="SIGNEXTEND",
    opcode=Op.SIGNEXTEND,
    max_op_count=200,
    step=20,
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
    max_op_count=200,
    step=20,
    stack_args=[MAX_U256, MAX_U256 - 1],
    pops_per_op=2,
    pushes_per_op=1,
)

GT_CONFIG = MarginalOpcodeConfig(
    name="GT",
    opcode=Op.GT,
    max_op_count=200,
    step=20,
    stack_args=[MAX_U256, MAX_U256 - 1],
    pops_per_op=2,
    pushes_per_op=1,
)

SLT_CONFIG = MarginalOpcodeConfig(
    name="SLT",
    opcode=Op.SLT,
    max_op_count=200,
    step=20,
    stack_args=[MAX_S256_NEG, MAX_S256_NEG - 1],
    pops_per_op=2,
    pushes_per_op=1,
)

SGT_CONFIG = MarginalOpcodeConfig(
    name="SGT",
    opcode=Op.SGT,
    max_op_count=200,
    step=20,
    stack_args=[MAX_S256_NEG, MAX_S256_NEG - 1],
    pops_per_op=2,
    pushes_per_op=1,
)

EQ_CONFIG = MarginalOpcodeConfig(
    name="EQ",
    opcode=Op.EQ,
    max_op_count=200,
    step=20,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

ISZERO_CONFIG = MarginalOpcodeConfig(
    name="ISZERO",
    opcode=Op.ISZERO,
    max_op_count=200,
    step=20,
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
    max_op_count=200,
    step=20,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

OR_CONFIG = MarginalOpcodeConfig(
    name="OR",
    opcode=Op.OR,
    max_op_count=200,
    step=20,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

XOR_CONFIG = MarginalOpcodeConfig(
    name="XOR",
    opcode=Op.XOR,
    max_op_count=200,
    step=20,
    stack_args=[MAX_U256, MAX_U256],
    pops_per_op=2,
    pushes_per_op=1,
)

NOT_CONFIG = MarginalOpcodeConfig(
    name="NOT",
    opcode=Op.NOT,
    max_op_count=200,
    step=20,
    stack_args=[MAX_U256],
    pops_per_op=1,
    pushes_per_op=1,
)

BYTE_CONFIG = MarginalOpcodeConfig(
    name="BYTE",
    opcode=Op.BYTE,
    max_op_count=200,
    step=20,
    stack_args=[0, MAX_U256],  # Extract byte 0 from max value
    pops_per_op=2,
    pushes_per_op=1,
)

SHL_CONFIG = MarginalOpcodeConfig(
    name="SHL",
    opcode=Op.SHL,
    max_op_count=200,
    step=20,
    stack_args=[255, MAX_U256],  # Shift left by 255 bits (max)
    pops_per_op=2,
    pushes_per_op=1,
)

SHR_CONFIG = MarginalOpcodeConfig(
    name="SHR",
    opcode=Op.SHR,
    max_op_count=200,
    step=20,
    stack_args=[255, MAX_U256],  # Shift right by 255 bits (max)
    pops_per_op=2,
    pushes_per_op=1,
)

SAR_CONFIG = MarginalOpcodeConfig(
    name="SAR",
    opcode=Op.SAR,
    max_op_count=200,
    step=20,
    stack_args=[255, MAX_S256_NEG],  # Arithmetic shift right by 255
    pops_per_op=2,
    pushes_per_op=1,
)

# ============================================================================
# KECCAK256 OPCODE - Variable cost based on input size
# ============================================================================

KECCAK256_CONFIG = MarginalOpcodeConfig(
    name="KECCAK256",
    opcode=Op.SHA3,  # SHA3 is the opcode name for KECCAK256
    max_op_count=20,
    step=5,
    stack_args=[0, 32],  # offset=0, size=32 bytes
    pops_per_op=2,
    pushes_per_op=1,
    # Pre-allocate memory with some data to hash
    setup_code=Op.MSTORE(0, 0xDEADBEEFCAFEBABE),
)

# ============================================================================
# STACK OPCODES - Representative samples (PUSH1, PUSH16, PUSH32, DUP, SWAP)
# ============================================================================

# Note: PUSH opcodes need special handling - they don't pop anything
# and we need to pop their result to balance the stack

PUSH1_CONFIG = MarginalOpcodeConfig(
    name="PUSH1",
    opcode=Op.PUSH1(0xFF),  # Push max 1-byte value
    max_op_count=200,
    step=20,
    stack_args=[],  # PUSH doesn't consume stack
    pops_per_op=0,
    pushes_per_op=1,
)

PUSH16_CONFIG = MarginalOpcodeConfig(
    name="PUSH16",
    opcode=Op.PUSH16(MAX_U256 >> 128),  # Max 16-byte value
    max_op_count=200,
    step=20,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

PUSH32_CONFIG = MarginalOpcodeConfig(
    name="PUSH32",
    opcode=Op.PUSH32(MAX_U256),  # Max 32-byte value
    max_op_count=200,
    step=20,
    stack_args=[],
    pops_per_op=0,
    pushes_per_op=1,
)

# DUP opcodes need N items on stack before they can duplicate
# Use small values (PUSH1) to minimize bytecode size - stack depth matters, not value
# Contract code limit is 24,576 bytes

DUP1_CONFIG = MarginalOpcodeConfig(
    name="DUP1",
    opcode=Op.DUP1,
    max_op_count=200,
    step=20,
    stack_args=[0xFF],  # Need 1 item for DUP1
    pops_per_op=0,  # DUP doesn't pop
    pushes_per_op=1,  # DUP pushes 1
)

DUP8_CONFIG = MarginalOpcodeConfig(
    name="DUP8",
    opcode=Op.DUP8,
    max_op_count=100,
    step=10,
    stack_args=[0xFF] * 8,  # Need 8 items for DUP8
    pops_per_op=0,
    pushes_per_op=1,
)

DUP16_CONFIG = MarginalOpcodeConfig(
    name="DUP16",
    opcode=Op.DUP16,
    max_op_count=50,
    step=5,
    stack_args=[0xFF] * 16,  # Need 16 items for DUP16
    pops_per_op=0,
    pushes_per_op=1,
)

# SWAP opcodes need N+1 items on stack
SWAP1_CONFIG = MarginalOpcodeConfig(
    name="SWAP1",
    opcode=Op.SWAP1,
    max_op_count=200,
    step=20,
    stack_args=[0xAA, 0xBB],  # Need 2 items for SWAP1
    pops_per_op=0,  # SWAP doesn't change stack size
    pushes_per_op=0,
)

SWAP8_CONFIG = MarginalOpcodeConfig(
    name="SWAP8",
    opcode=Op.SWAP8,
    max_op_count=100,
    step=10,
    stack_args=[0xFF] * 9,  # Need 9 items for SWAP8
    pops_per_op=0,
    pushes_per_op=0,
)

SWAP16_CONFIG = MarginalOpcodeConfig(
    name="SWAP16",
    opcode=Op.SWAP16,
    max_op_count=50,
    step=5,
    stack_args=[0xFF] * 17,  # Need 17 items for SWAP16
    pops_per_op=0,
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

    The program structure ensures that:
    1. Total bytecode structure is constant regardless of op_count
    2. Only the number of opcode executions varies
    3. Stack is properly balanced at the end
    4. Success marker is written to storage if execution completes

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

    # 2. Push stack arguments for ALL potential opcode instances
    # This ensures the stack setup is identical regardless of op_count
    for _ in range(config.max_op_count):
        for arg in config.stack_args:
            code += push_value(arg)

    # 3. Execute the opcode op_count times, each followed by POPs to clean results
    for _ in range(op_count):
        code += config.opcode
        # Pop the results to keep stack balanced
        for _ in range(config.pushes_per_op):
            code += Op.POP

    # 4. Pop remaining unused arguments from stack
    # For each unused op, we have pops_per_op arguments still on stack
    remaining_args = (config.max_op_count - op_count) * config.pops_per_op
    for _ in range(remaining_args):
        code += Op.POP

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
    generate_op_counts(DUP1_CONFIG.max_op_count, DUP1_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_dup1(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for DUP1 opcode."""
    code = generate_marginal_program(DUP1_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(DUP8_CONFIG.max_op_count, DUP8_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_dup8(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for DUP8 opcode."""
    code = generate_marginal_program(DUP8_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(DUP16_CONFIG.max_op_count, DUP16_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_dup16(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for DUP16 opcode."""
    code = generate_marginal_program(DUP16_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SWAP1_CONFIG.max_op_count, SWAP1_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_swap1(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SWAP1 opcode."""
    code = generate_marginal_program(SWAP1_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SWAP8_CONFIG.max_op_count, SWAP8_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_swap8(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SWAP8 opcode."""
    code = generate_marginal_program(SWAP8_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(SWAP16_CONFIG.max_op_count, SWAP16_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_swap16(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Marginal cost test for SWAP16 opcode."""
    code = generate_marginal_program(SWAP16_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=1_000_000, sender=sender)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)
