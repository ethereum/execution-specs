"""
Investigation: Does ADD argument size (1-byte vs 32-byte) affect zkcycles?

This test compares:
1. ADD with PUSH1 (1-byte values)
2. ADD with PUSH32 (32-byte MAX_U256 values)

Both have the same number of ADD operations.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Environment,
    Op,
    StateTestFiller,
    Transaction,
)


# Constants
# PUSH32 version: 68 bytes per op (33+33+1+1), max bytecode = 24576
# Max ops with PUSH32 = 24576 / 68 ≈ 361, use 350 for safety
NUM_ADDS = 350  # Number of ADD operations
SUCCESS_SLOT = 0
SUCCESS_MARKER = 1

# Max U256 value
MAX_U256 = (1 << 256) - 1


def generate_add_push1_bytecode(num_adds: int) -> Bytecode:
    """Generate bytecode with PUSH1 + PUSH1 + ADD + POP pattern."""
    code = Bytecode()
    
    for _ in range(num_adds):
        code += Op.PUSH1(0x03)  # Small 1-byte value
        code += Op.PUSH1(0x03)  # Small 1-byte value
        code += Op.ADD
        code += Op.POP  # Consume result
    
    # Success marker
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code


def generate_add_push32_bytecode(num_adds: int) -> Bytecode:
    """Generate bytecode with PUSH32 + PUSH32 + ADD + POP pattern."""
    code = Bytecode()
    
    for _ in range(num_adds):
        code += Op.PUSH32(MAX_U256)  # Full 32-byte MAX value
        code += Op.PUSH32(MAX_U256)  # Full 32-byte MAX value
        code += Op.ADD
        code += Op.POP  # Consume result
    
    # Success marker
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code


@pytest.mark.valid_from("Prague")
def test_add_with_push1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test ADD operations with small 1-byte values (PUSH1).
    
    Pattern: (PUSH1 0x03, PUSH1 0x03, ADD, POP) × NUM_ADDS
    """
    code = generate_add_push1_bytecode(NUM_ADDS)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    
    tx = Transaction(
        to=contract,
        gas_limit=10_000_000,
        sender=sender,
    )
    
    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }
    
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.valid_from("Prague")
def test_add_with_push32(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test ADD operations with full 32-byte MAX_U256 values (PUSH32).
    
    Pattern: (PUSH32 MAX_U256, PUSH32 MAX_U256, ADD, POP) × NUM_ADDS
    """
    code = generate_add_push32_bytecode(NUM_ADDS)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    
    tx = Transaction(
        to=contract,
        gas_limit=10_000_000,
        sender=sender,
    )
    
    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }
    
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )
