"""
Investigation: Caller-contract approach for marginal ADD benchmarking.

This test uses a caller contract to amplify op_count while preserving the marginal property:
1. Target contract: Contains K ADDs using batch marginal pattern
2. Caller contract: Calls target N times (N is constant across all K values)

Effective op_count = N × K, allowing much higher operation counts.
"""

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

# Configuration
NUM_CALLS = 10  # N: Number of times caller calls target (CONSTANT)
MAX_ADDS_PER_CALL = 100  # Maximum K per target contract
STEP = 10  # Step size for K values

# Generate op_count values: 0, 10, 20, ..., 100
OP_COUNTS = list(range(0, MAX_ADDS_PER_CALL + 1, STEP))

SUCCESS_MARKER = 0xDEAD
SUCCESS_SLOT = 0


def generate_target_contract_code(op_count: int) -> Bytecode:
    """
    Generate target contract with op_count ADDs using batch marginal pattern.
    
    Structure:
    - [PUSH0 × MAX] - empty values for POP padding (MAX = MAX_ADDS_PER_CALL)
    - [PUSH1 0x03 × MAX × 2] - arguments for all potential ADDs
    - [ADD + (POP + ADD) × (op_count-1)] - interleaved ADDs and POPs
    - [POP × remaining] - consume remaining stack values
    - STOP
    
    This preserves marginal property: PUSH and POP counts are constant,
    only ADD count varies.
    """
    MAX = MAX_ADDS_PER_CALL
    code = Bytecode()
    
    # Empty pushes for POP padding (nreturns=1 for ADD)
    for _ in range(MAX):
        code += Op.PUSH0
    
    # Argument pushes (2 args per ADD × MAX ADDs)
    for _ in range(MAX * 2):
        code += Op.PUSH1(0x03)
    
    # Interleaved ADDs and POPs
    if op_count == 0:
        # No ADDs, just POPs
        pass
    elif op_count >= 1:
        code += Op.ADD
        for _ in range(op_count - 1):
            code += Op.POP
            code += Op.ADD
    
    # Remaining POPs: total should be MAX
    # We've done (op_count - 1) POPs in the interleaved section
    remaining_pops = MAX - (op_count - 1) if op_count > 0 else MAX
    for _ in range(remaining_pops):
        code += Op.POP
    
    # Return success (for STATICCALL, we just return)
    code += Op.STOP
    
    return code


def generate_caller_contract_code(target_address: Address, num_calls: int) -> Bytecode:
    """
    Generate caller contract that calls target num_calls times.
    
    Uses a simple loop to ensure constant opcode counts.
    """
    code = Bytecode()
    
    # Simple approach: unrolled calls (no loop complexity)
    # Each STATICCALL: gas, addr, argsOffset, argsSize, retOffset, retSize
    for _ in range(num_calls):
        code += Op.PUSH1(0)      # retSize
        code += Op.PUSH1(0)      # retOffset  
        code += Op.PUSH1(0)      # argsSize
        code += Op.PUSH1(0)      # argsOffset
        code += Op.PUSH20(target_address)  # address
        code += Op.GAS           # gas (forward all)
        code += Op.STATICCALL
        code += Op.POP           # pop success flag
    
    # Success marker
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    OP_COUNTS,
    ids=lambda x: f"op_count_{x}",
)
def test_caller_contract_add(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Test ADD with caller-contract amplification.
    
    Effective op_count = NUM_CALLS × op_count
    This should show linear relationship between gas_used and effective op_count.
    """
    # Deploy target contract with op_count ADDs
    target_code = generate_target_contract_code(op_count)
    target_contract = pre.deploy_contract(code=target_code)
    
    # Deploy caller contract that calls target NUM_CALLS times
    caller_code = generate_caller_contract_code(target_contract, NUM_CALLS)
    caller_contract = pre.deploy_contract(code=caller_code)
    
    # Fund sender
    sender = pre.fund_eoa()
    
    # Transaction calls the caller contract
    tx = Transaction(
        to=caller_contract,
        gas_limit=10_000_000,
        sender=sender,
    )
    
    # Post state: caller contract should have success marker
    post = {
        caller_contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }
    
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )
