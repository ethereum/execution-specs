"""
Marginal tests for opcodes/precompiles with low R² in proving time analysis.

These use the caller-contract approach to amplify effective op_count by NUM_CALLS,
increasing total gas usage to improve signal-to-noise ratio in proving time measurements.

Key changes:
1. NUM_CALLS = 100 for amplification (within 1M gas limit per test)
2. Worst-case arguments where applicable
3. Higher max_op_count where possible
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

# ============================================================================
# CONSTANTS
# ============================================================================

SUCCESS_SLOT = 0
SUCCESS_MARKER = 0xDEAD
MAX_U256 = 2**256 - 1

# Caller-contract approach: amplify op_count by calling target N times
NUM_CALLS = 100
CALLER_GAS_LIMIT = 1_000_000  # 1M gas limit

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_op_counts(max_op_count: int, step: int) -> List[int]:
    """Generate list of op_counts from 0 to max_op_count with given step."""
    counts = list(range(0, max_op_count + 1, step))
    if counts[-1] != max_op_count:
        counts.append(max_op_count)
    return counts


# ============================================================================
# CALLER CONTRACT GENERATOR
# ============================================================================

def generate_caller_contract(target_address: Address, use_call: bool = False) -> Bytecode:
    """
    Generate caller that calls target NUM_CALLS times.
    
    Args:
        target_address: Address of target contract
        use_call: If True, use CALL instead of STATICCALL (needed for LOG ops)
    """
    code = Bytecode()
    
    for _ in range(NUM_CALLS):
        code += Op.PUSH1(0)      # retSize
        code += Op.PUSH1(0)      # retOffset
        code += Op.PUSH1(0)      # argsSize
        code += Op.PUSH1(0)      # argsOffset
        if use_call:
            code += Op.PUSH1(0)  # value (for CALL)
        code += Op.PUSH20(target_address)
        code += Op.GAS
        if use_call:
            code += Op.CALL
        else:
            code += Op.STATICCALL
        code += Op.POP
    
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code


# ============================================================================
# TARGET CONTRACT GENERATORS
# ============================================================================

def generate_target_memory_op(opcode_name: str, op_count: int, max_op_count: int) -> Bytecode:
    """Generate target for memory ops (MLOAD, MSTORE, MSTORE8)."""
    code = Bytecode()
    
    # Setup: pre-expand memory
    code += Op.MSTORE(0, MAX_U256)
    
    if opcode_name == "MLOAD":
        for _ in range(op_count):
            code += Op.PUSH1(0)
            code += Op.MLOAD
            code += Op.POP
        for _ in range(max_op_count - op_count):
            code += Op.PUSH1(0)
    elif opcode_name == "MSTORE":
        for _ in range(op_count):
            code += Op.PUSH1(0)       # offset
            code += Op.PUSH1(0xFF)    # value (use small value to reduce bytecode size)
            code += Op.MSTORE
        for _ in range(max_op_count - op_count):
            code += Op.PUSH1(0)
            code += Op.PUSH1(0xFF)
    elif opcode_name == "MSTORE8":
        for _ in range(op_count):
            code += Op.PUSH1(0)   # offset
            code += Op.PUSH1(0xFF)  # value
            code += Op.MSTORE8
        for _ in range(max_op_count - op_count):
            code += Op.PUSH1(0)
            code += Op.PUSH1(0xFF)
    
    code += Op.STOP
    return code


def generate_target_copy_op(opcode_name: str, op_count: int, max_op_count: int, size: int = 256) -> Bytecode:
    """Generate target for copy ops."""
    code = Bytecode()
    
    # Setup memory
    code += Op.MSTORE(0, 0)
    code += Op.MSTORE(4096, 0)
    
    if opcode_name == "CODECOPY":
        for _ in range(op_count):
            code += Op.PUSH2(size)
            code += Op.PUSH1(0)
            code += Op.PUSH1(0)
            code += Op.CODECOPY
        for _ in range(max_op_count - op_count):
            code += Op.PUSH2(size)
            code += Op.PUSH1(0)
            code += Op.PUSH1(0)
    elif opcode_name == "CALLDATACOPY":
        for _ in range(op_count):
            code += Op.PUSH2(size)
            code += Op.PUSH1(0)
            code += Op.PUSH1(0)
            code += Op.CALLDATACOPY
        for _ in range(max_op_count - op_count):
            code += Op.PUSH2(size)
            code += Op.PUSH1(0)
            code += Op.PUSH1(0)
    elif opcode_name == "MCOPY":
        for _ in range(op_count):
            code += Op.PUSH2(size)
            code += Op.PUSH1(0)
            code += Op.PUSH2(4096)
            code += Op.MCOPY
        for _ in range(max_op_count - op_count):
            code += Op.PUSH2(size)
            code += Op.PUSH1(0)
            code += Op.PUSH2(4096)
    
    code += Op.STOP
    return code


def generate_target_storage_op(opcode_name: str, op_count: int, max_op_count: int) -> Bytecode:
    """Generate target for storage ops."""
    code = Bytecode()
    
    if opcode_name == "SLOAD":
        # Warm up slot 100
        code += Op.POP(Op.SLOAD(100))
        for _ in range(op_count):
            code += Op.PUSH1(100)
            code += Op.SLOAD
            code += Op.POP
        for _ in range(max_op_count - op_count):
            code += Op.PUSH1(100)
    elif opcode_name == "TLOAD":
        for _ in range(op_count):
            code += Op.PUSH1(0)
            code += Op.TLOAD
            code += Op.POP
        for _ in range(max_op_count - op_count):
            code += Op.PUSH1(0)
    elif opcode_name == "TSTORE":
        for _ in range(op_count):
            code += Op.PUSH1(0xFF)  # value (smaller for bytecode)
            code += Op.PUSH1(0)
            code += Op.TSTORE
        for _ in range(max_op_count - op_count):
            code += Op.PUSH1(0xFF)
            code += Op.PUSH1(0)
    
    code += Op.STOP
    return code


def generate_target_log(log_n: int, op_count: int, max_op_count: int, data_size: int = 32) -> Bytecode:
    """Generate target for LOG0-LOG4."""
    code = Bytecode()
    
    # Setup memory
    code += Op.MSTORE(0, MAX_U256)
    
    log_ops = [Op.LOG0, Op.LOG1, Op.LOG2, Op.LOG3, Op.LOG4]
    log_op = log_ops[log_n]
    
    for _ in range(op_count):
        # Push topics
        for _ in range(log_n):
            code += Op.PUSH32(0xDEADBEEF)
        code += Op.PUSH1(data_size)
        code += Op.PUSH1(0)
        code += log_op
    
    # Noops
    for _ in range(max_op_count - op_count):
        for _ in range(log_n):
            code += Op.PUSH32(0xDEADBEEF)
        code += Op.PUSH1(data_size)
        code += Op.PUSH1(0)
    
    code += Op.STOP
    return code


def generate_target_keccak256(op_count: int, max_op_count: int, size: int = 256) -> Bytecode:
    """Generate target for KECCAK256."""
    code = Bytecode()
    
    # Setup memory
    for i in range(0, min(size, 256), 32):
        code += Op.MSTORE(i, MAX_U256)
    
    for _ in range(op_count):
        code += Op.PUSH2(size)
        code += Op.PUSH1(0)
        code += Op.SHA3
        code += Op.POP
    
    for _ in range(max_op_count - op_count):
        code += Op.PUSH2(size)
        code += Op.PUSH1(0)
    
    code += Op.STOP
    return code


def generate_target_dup(n: int, op_count: int, max_op_count: int) -> Bytecode:
    """Generate target for DUP1-16."""
    code = Bytecode()
    
    # Setup: push n values
    for i in range(n):
        code += Op.PUSH1(i)
    
    dup_ops = [Op.DUP1, Op.DUP2, Op.DUP3, Op.DUP4, Op.DUP5, Op.DUP6, Op.DUP7, Op.DUP8,
               Op.DUP9, Op.DUP10, Op.DUP11, Op.DUP12, Op.DUP13, Op.DUP14, Op.DUP15, Op.DUP16]
    dup_op = dup_ops[n - 1]
    
    for _ in range(op_count):
        code += dup_op
        code += Op.POP
    
    for _ in range(max_op_count - op_count):
        code += Op.PUSH1(0)
        code += Op.POP
    
    # Cleanup
    for _ in range(n):
        code += Op.POP
    
    code += Op.STOP
    return code


def generate_target_swap(n: int, op_count: int, max_op_count: int) -> Bytecode:
    """Generate target for SWAP1-16."""
    code = Bytecode()
    
    # Setup: push n+1 values (SWAP n requires n+1 items on stack)
    for i in range(n + 1):
        code += Op.PUSH1(i)
    
    swap_ops = [Op.SWAP1, Op.SWAP2, Op.SWAP3, Op.SWAP4, Op.SWAP5, Op.SWAP6, Op.SWAP7, Op.SWAP8,
                Op.SWAP9, Op.SWAP10, Op.SWAP11, Op.SWAP12, Op.SWAP13, Op.SWAP14, Op.SWAP15, Op.SWAP16]
    swap_op = swap_ops[n - 1]
    
    for _ in range(op_count):
        code += swap_op
    
    for _ in range(max_op_count - op_count):
        code += Op.PUSH0
        code += Op.POP
    
    # Cleanup
    for _ in range(n + 1):
        code += Op.POP
    
    code += Op.STOP
    return code


def generate_target_simple(opcode, op_count: int, max_op_count: int, has_result: bool = True) -> Bytecode:
    """Generate target for simple opcodes."""
    code = Bytecode()
    
    # For MSIZE, expand memory first
    if opcode == Op.MSIZE:
        code += Op.MSTORE(1024, 0)
    
    for _ in range(op_count):
        code += opcode
        if has_result:
            code += Op.POP
    
    for _ in range(max_op_count - op_count):
        code += Op.PUSH0
        code += Op.POP
    
    code += Op.STOP
    return code


def generate_target_balance_like(opcode, op_count: int, max_op_count: int) -> Bytecode:
    """Generate target for BALANCE, EXTCODESIZE, EXTCODEHASH."""
    code = Bytecode()
    
    # Warm up address
    code += Op.POP(Op.BALANCE(0xDEAD))
    
    for _ in range(op_count):
        code += Op.PUSH20(0xDEAD)
        code += opcode
        code += Op.POP
    
    for _ in range(max_op_count - op_count):
        code += Op.PUSH20(0xDEAD)
    
    code += Op.STOP
    return code


def generate_target_extcodecopy(op_count: int, max_op_count: int, size: int = 256) -> Bytecode:
    """Generate target for EXTCODECOPY."""
    code = Bytecode()
    
    # Setup memory and warm up
    code += Op.MSTORE(0, 0)
    code += Op.POP(Op.EXTCODESIZE(0xDEAD))
    
    for _ in range(op_count):
        code += Op.PUSH2(size)
        code += Op.PUSH1(0)
        code += Op.PUSH1(0)
        code += Op.PUSH20(0xDEAD)
        code += Op.EXTCODECOPY
    
    for _ in range(max_op_count - op_count):
        code += Op.PUSH2(size)
        code += Op.PUSH1(0)
        code += Op.PUSH1(0)
        code += Op.PUSH20(0xDEAD)
    
    code += Op.STOP
    return code


def generate_target_calldataload(op_count: int, max_op_count: int) -> Bytecode:
    """Generate target for CALLDATALOAD."""
    code = Bytecode()
    
    for _ in range(op_count):
        code += Op.PUSH1(0)
        code += Op.CALLDATALOAD
        code += Op.POP
    
    for _ in range(max_op_count - op_count):
        code += Op.PUSH1(0)
    
    code += Op.STOP
    return code


def generate_target_blobhash(op_count: int, max_op_count: int) -> Bytecode:
    """Generate target for BLOBHASH."""
    code = Bytecode()
    
    for _ in range(op_count):
        code += Op.PUSH1(0)
        code += Op.BLOBHASH
        code += Op.POP
    
    for _ in range(max_op_count - op_count):
        code += Op.PUSH1(0)
    
    code += Op.STOP
    return code


# ============================================================================
# TEST FUNCTIONS - MEMORY OPS
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_mload(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed MLOAD with caller amplification."""
    max_op_count = 50
    target_code = generate_target_memory_op("MLOAD", op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(20, 4), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_mstore(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed MSTORE with caller amplification."""
    max_op_count = 20
    target_code = generate_target_memory_op("MSTORE", op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_mstore8(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed MSTORE8 with caller amplification."""
    max_op_count = 50
    target_code = generate_target_memory_op("MSTORE8", op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# TEST FUNCTIONS - COPY OPS
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(30, 3), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_codecopy(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed CODECOPY with caller amplification."""
    max_op_count = 30
    target_code = generate_target_copy_op("CODECOPY", op_count, max_op_count, size=256)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(30, 3), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_calldatacopy(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed CALLDATACOPY with caller amplification."""
    max_op_count = 30
    target_code = generate_target_copy_op("CALLDATACOPY", op_count, max_op_count, size=256)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender, data=bytes(256))
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(30, 3), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_mcopy(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed MCOPY with caller amplification."""
    max_op_count = 30
    target_code = generate_target_copy_op("MCOPY", op_count, max_op_count, size=256)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# TEST FUNCTIONS - STORAGE OPS
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(20, 2), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_sload(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed SLOAD with caller amplification."""
    max_op_count = 20
    target_code = generate_target_storage_op("SLOAD", op_count, max_op_count)
    target = pre.deploy_contract(code=target_code, storage={100: MAX_U256})
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(20, 2), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_tload(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed TLOAD with caller amplification."""
    max_op_count = 20
    target_code = generate_target_storage_op("TLOAD", op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(20, 2), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_tstore(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed TSTORE with caller amplification."""
    max_op_count = 20
    target_code = generate_target_storage_op("TSTORE", op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target, use_call=True)  # TSTORE needs CALL
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# TEST FUNCTIONS - LOG OPS
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(10, 2), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_log0(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed LOG0 with caller amplification."""
    max_op_count = 10
    target_code = generate_target_log(0, op_count, max_op_count, data_size=32)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target, use_call=True)  # LOG needs CALL
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(8, 2), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_log1(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed LOG1 with caller amplification."""
    max_op_count = 8
    target_code = generate_target_log(1, op_count, max_op_count, data_size=32)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target, use_call=True)  # LOG needs CALL
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(6, 2), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_log2(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed LOG2 with caller amplification."""
    max_op_count = 6
    target_code = generate_target_log(2, op_count, max_op_count, data_size=32)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target, use_call=True)  # LOG needs CALL
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(4, 1), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_log3(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed LOG3 with caller amplification."""
    max_op_count = 4
    target_code = generate_target_log(3, op_count, max_op_count, data_size=32)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target, use_call=True)  # LOG needs CALL
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(4, 1), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_log4(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed LOG4 with caller amplification."""
    max_op_count = 4
    target_code = generate_target_log(4, op_count, max_op_count, data_size=32)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target, use_call=True)  # LOG needs CALL
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# TEST FUNCTIONS - KECCAK256
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(30, 3), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_keccak256(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed KECCAK256 with caller amplification."""
    max_op_count = 30
    target_code = generate_target_keccak256(op_count, max_op_count, size=256)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# TEST FUNCTIONS - DUP OPS
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_dup1(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed DUP1 with caller amplification."""
    max_op_count = 50
    target_code = generate_target_dup(1, op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_dup8(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed DUP8 with caller amplification."""
    max_op_count = 50
    target_code = generate_target_dup(8, op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_dup16(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed DUP16 with caller amplification."""
    max_op_count = 50
    target_code = generate_target_dup(16, op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# TEST FUNCTIONS - SWAP OPS
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_swap1(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed SWAP1 with caller amplification."""
    max_op_count = 50
    target_code = generate_target_swap(1, op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_swap8(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed SWAP8 with caller amplification."""
    max_op_count = 50
    target_code = generate_target_swap(8, op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_swap16(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed SWAP16 with caller amplification."""
    max_op_count = 50
    target_code = generate_target_swap(16, op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# TEST FUNCTIONS - SIMPLE OPS
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_jumpdest(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed JUMPDEST with caller amplification."""
    max_op_count = 50
    target_code = generate_target_simple(Op.JUMPDEST, op_count, max_op_count, has_result=False)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_msize(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed MSIZE with caller amplification."""
    max_op_count = 50
    target_code = generate_target_simple(Op.MSIZE, op_count, max_op_count, has_result=True)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_pop(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed POP with caller amplification."""
    max_op_count = 50
    
    code = Bytecode()
    for _ in range(op_count):
        code += Op.PUSH1(0)
        code += Op.POP
    for _ in range(max_op_count - op_count):
        code += Op.PUSH1(0)
    code += Op.STOP
    
    target = pre.deploy_contract(code=code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# TEST FUNCTIONS - BALANCE-LIKE OPS
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(20, 2), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_balance(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed BALANCE with caller amplification."""
    max_op_count = 20
    target_code = generate_target_balance_like(Op.BALANCE, op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(20, 2), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_extcodesize(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed EXTCODESIZE with caller amplification."""
    max_op_count = 20
    target_code = generate_target_balance_like(Op.EXTCODESIZE, op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(20, 2), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_extcodehash(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed EXTCODEHASH with caller amplification."""
    max_op_count = 20
    target_code = generate_target_balance_like(Op.EXTCODEHASH, op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(10, 2), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_extcodecopy(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed EXTCODECOPY with caller amplification."""
    max_op_count = 10
    target_code = generate_target_extcodecopy(op_count, max_op_count, size=256)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# TEST FUNCTIONS - CALLDATA/BLOB OPS
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_calldataload(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed CALLDATALOAD with caller amplification."""
    max_op_count = 50
    target_code = generate_target_calldataload(op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender, data=bytes(64))
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_blobhash(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed BLOBHASH with caller amplification."""
    max_op_count = 50
    target_code = generate_target_blobhash(op_count, max_op_count)
    target = pre.deploy_contract(code=target_code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# TEST FUNCTIONS - XOR, PUSH1 (already have caller tests but included for completeness)
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_xor(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed XOR with caller amplification."""
    max_op_count = 50
    
    code = Bytecode()
    for _ in range(op_count):
        code += Op.PUSH32(MAX_U256)
        code += Op.PUSH32(MAX_U256)
        code += Op.XOR
        code += Op.POP
    for _ in range(max_op_count - op_count):
        code += Op.PUSH32(MAX_U256)
        code += Op.PUSH32(MAX_U256)
    code += Op.STOP
    
    target = pre.deploy_contract(code=code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(100, 10), ids=lambda x: f"op_count_{x}")
def test_caller_fixed_push1(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """Fixed PUSH1 with caller amplification."""
    max_op_count = 100
    
    code = Bytecode()
    for _ in range(op_count):
        code += Op.PUSH1(0xFF)
        code += Op.POP
    for _ in range(max_op_count - op_count):
        code += Op.PUSH0
        code += Op.POP
    code += Op.STOP
    
    target = pre.deploy_contract(code=code)
    caller_code = generate_caller_contract(target)
    caller = pre.deploy_contract(code=caller_code)
    sender = pre.fund_eoa()
    tx = Transaction(to=caller, gas_limit=CALLER_GAS_LIMIT, sender=sender)
    post = {caller: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)

