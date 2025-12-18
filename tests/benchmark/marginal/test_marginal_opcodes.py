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

ADD_CONFIG = MarginalOpcodeConfig(
    name="ADD",
    opcode=Op.ADD,
    max_op_count=200,
    step=20,  # 11 points: 0, 20, 40, ..., 180, 200
    stack_args=[3, 5],  # Two arguments for ADD
    pops_per_op=2,
    pushes_per_op=1,
)

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
            code += Op.PUSH1(arg)

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
