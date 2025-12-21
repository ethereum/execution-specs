"""
Marginal tests for precompiles with low R² in proving time analysis.

These increase op_count and input sizes to increase total gas usage,
improving signal-to-noise ratio in proving time measurements.

Key changes:
1. Larger input sizes for maximum computational work
2. Higher op_count (within gas limit)
3. Higher gas limit (5M) for expensive precompiles
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
    Spec as BLS12Spec,
)

# ============================================================================
# CONSTANTS
# ============================================================================

SUCCESS_SLOT = 0
SUCCESS_MARKER = 0xDEAD
MAX_U256 = 2**256 - 1

# Precompile addresses
SHA256_ADDRESS = Address(0x02)
RIPEMD160_ADDRESS = Address(0x03)
IDENTITY_ADDRESS = Address(0x04)
BN128_ADD_ADDRESS = Address(0x06)
BLS12_G2ADD_ADDRESS = Address(0x0D)


def generate_op_counts(max_op_count: int, step: int) -> List[int]:
    """Generate list of op_counts from 0 to max_op_count with given step."""
    counts = list(range(0, max_op_count + 1, step))
    if counts[-1] != max_op_count:
        counts.append(max_op_count)
    return counts


# ============================================================================
# PRECOMPILE INPUT DATA (worst-case for maximum gas)
# ============================================================================

# SHA256: 8KB input for maximum work
# Gas: 60 + 12 * ceil(8192/32) = 60 + 12 * 256 = 3,132 gas per call
SHA256_INPUT = bytes([0xFF] * 8192)

# RIPEMD160: 2KB input (higher gas per byte than SHA256)
# Gas: 600 + 120 * ceil(2048/32) = 600 + 120 * 64 = 8,280 gas per call
RIPEMD160_INPUT = bytes([0xFF] * 2048)

# IDENTITY: 1KB input
# Gas: 15 + 3 * ceil(1024/32) = 15 + 3 * 32 = 111 gas per call
IDENTITY_INPUT = bytes([0xFF] * 1024)

# BN128_ADD: two valid curve points (128 bytes)
# Gas: 150 (fixed)
BN128_ADD_INPUT = bytes.fromhex(
    "18b18acfb4c2c30276db5411368e7185b311dd124691610c5d3b74034e093dc9"
    "063c909c4720840cb5134cb9f59fa749755796819658d32efc0d288198f37266"
    "07c2b7f58a84bd6145f00c9c2bc0bb1a187f20ff2c92963a88019e7c6a014eed"
    "06614e20c147e940f2d70da3f74c9a17df361706a4485c742bd6788478fa17d7"
)

# BLS12_G2ADD: Valid G2 points from EIP-2537 tests
# Gas: 600 (fixed)
# Using G2 generator + P2 (random test point) from EIP-2537 spec
BLS12_G2ADD_INPUT = bytes(BLS12Spec.G2 + BLS12Spec.P2)


def generate_precompile_program(
    precompile_address: Address,
    input_data: bytes,
    op_count: int,
    max_op_count: int,
) -> tuple[Bytecode, bytes]:
    """
    Generate precompile test program.
    
    Uses CALLDATACOPY to load input, then calls precompile op_count times.
    Noops push the same args but don't call.
    """
    input_size = len(input_data)
    
    code = Bytecode()
    
    # Copy input data to memory at offset 0
    code += Op.PUSH2(input_size)  # size
    code += Op.PUSH1(0)           # offset (from calldata)
    code += Op.PUSH1(0)           # destOffset (to memory)
    code += Op.CALLDATACOPY
    
    # Real precompile calls
    for _ in range(op_count):
        code += Op.PUSH1(0)               # retSize
        code += Op.PUSH1(0)               # retOffset
        code += Op.PUSH2(input_size)      # argsSize
        code += Op.PUSH1(0)               # argsOffset (from memory)
        code += Op.PUSH20(precompile_address)
        code += Op.GAS
        code += Op.STATICCALL
        code += Op.POP
    
    # Noop: push args and pop (to maintain constant stack)
    for _ in range(max_op_count - op_count):
        code += Op.PUSH1(0)
        code += Op.PUSH1(0)
        code += Op.PUSH2(input_size)
        code += Op.PUSH1(0)
        code += Op.PUSH20(precompile_address)
        code += Op.GAS
        # Pop all 6 values to avoid stack overflow
        code += Op.POP
        code += Op.POP
        code += Op.POP
        code += Op.POP
        code += Op.POP
        code += Op.POP
    
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code, input_data


# ============================================================================
# TEST FUNCTIONS - PRECOMPILES
# ============================================================================

@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(100, 10), ids=lambda x: f"op_count_{x}")
def test_fixed_sha256(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """
    Fixed SHA256 precompile with 8KB input and high op_count.
    
    Gas per call: 60 + 12 * 256 = 3,132 gas
    Total for 100 calls: ~313K + overhead
    """
    max_op_count = 100
    code, calldata = generate_precompile_program(
        SHA256_ADDRESS, SHA256_INPUT, op_count, max_op_count
    )
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender, data=calldata)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(50, 5), ids=lambda x: f"op_count_{x}")
def test_fixed_ripemd160(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """
    Fixed RIPEMD160 precompile with 2KB input and high op_count.
    
    Gas per call: 600 + 120 * 64 = 8,280 gas
    Total for 50 calls: ~414K + overhead
    """
    max_op_count = 50
    code, calldata = generate_precompile_program(
        RIPEMD160_ADDRESS, RIPEMD160_INPUT, op_count, max_op_count
    )
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender, data=calldata)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(200, 20), ids=lambda x: f"op_count_{x}")
def test_fixed_identity(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """
    Fixed IDENTITY precompile with 8KB input and high op_count.
    
    Gas per call: 15 + 3 * 256 = 783 gas
    Total for 200 calls: ~156K + overhead
    """
    max_op_count = 200
    code, calldata = generate_precompile_program(
        IDENTITY_ADDRESS, IDENTITY_INPUT, op_count, max_op_count
    )
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender, data=calldata)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(100, 10), ids=lambda x: f"op_count_{x}")
def test_fixed_bn128_add(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """
    Fixed BN128_ADD precompile with valid curve points and high op_count.
    
    Gas per call: 150 (fixed)
    Total for 100 calls: ~15K + overhead
    """
    max_op_count = 100
    code, calldata = generate_precompile_program(
        BN128_ADD_ADDRESS, BN128_ADD_INPUT, op_count, max_op_count
    )
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender, data=calldata)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.benchmark
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("op_count", generate_op_counts(100, 10), ids=lambda x: f"op_count_{x}")
def test_fixed_bls12_g2add(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
    """
    Fixed BLS12_G2ADD precompile with valid G2 points and high op_count.
    
    Gas per call: 600 (fixed)
    Total for 100 calls: ~60K + overhead
    """
    max_op_count = 100
    code, calldata = generate_precompile_program(
        BLS12_G2ADD_ADDRESS, BLS12_G2ADD_INPUT, op_count, max_op_count
    )
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()
    tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender, data=calldata)
    post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
    state_test(env=Environment(), pre=pre, post=post, tx=tx)

