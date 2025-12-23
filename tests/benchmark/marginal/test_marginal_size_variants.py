"""
Size variant tests for opcodes with variable gas costs based on data size.

This module tests the hypothesis that smaller data sizes lead to higher cycles/gas
ratios in zkVMs because:
- Smaller size = lower gas per operation = more iterations in gas budget
- More iterations = more opcode overhead to prove
- Result: higher cycles/gas ratio for smaller sizes

Each opcode is tested with small, medium, and large data sizes.
"""

from dataclasses import dataclass
from typing import List

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
SUCCESS_MARKER = 0xDEAD
SUCCESS_SLOT = 0
MAX_U256 = (1 << 256) - 1


@dataclass
class SizeVariantConfig:
    """Configuration for a size variant test."""
    name: str
    opcode: Op
    max_op_count: int
    step: int
    stack_args: List[int]
    pops_per_op: int
    pushes_per_op: int
    setup_code: Bytecode | None = None


def generate_op_counts(max_op_count: int, step: int) -> List[int]:
    """Generate list of op_counts from 0 to max_op_count with given step."""
    counts = list(range(0, max_op_count + 1, step))
    if counts[-1] != max_op_count:
        counts.append(max_op_count)
    return counts


def generate_marginal_program(config: SizeVariantConfig, op_count: int) -> Bytecode:
    """Generate a marginal test program for the given opcode and op_count."""
    max_op_count = config.max_op_count
    code = Bytecode()
    
    # Add setup code if present
    if config.setup_code:
        code += config.setup_code
    
    if config.pushes_per_op > 0:
        # Strategy 1: POP-based padding for returning opcodes
        # Pre-push dummy values for POPs
        for _ in range(max_op_count * config.pushes_per_op):
            code += Op.PUSH0
        
        # Push arguments for all operations
        for _ in range(max_op_count):
            for arg in config.stack_args:
                if arg == 0:
                    code += Op.PUSH0
                elif arg <= 0xFF:
                    code += Op.PUSH1[arg]
                elif arg <= 0xFFFF:
                    code += Op.PUSH2[arg]
                elif arg <= 0xFFFFFF:
                    code += Op.PUSH3[arg]
                else:
                    code += Op.PUSH32[arg]
        
        # Execute op_count operations with interleaved POPs
        for i in range(op_count):
            code += config.opcode
            for _ in range(config.pushes_per_op):
                code += Op.POP
        
        # Pop remaining dummy values
        remaining_pops = (max_op_count - op_count) * config.pushes_per_op
        for _ in range(remaining_pops):
            code += Op.POP
    else:
        # Strategy 2: Simple approach for non-returning opcodes
        # Only push args and execute opcode for op_count iterations
        # No padding needed - bytecode size varies but that's fine for marginal tests
        for _ in range(op_count):
            for arg in config.stack_args:
                if arg == 0:
                    code += Op.PUSH0
                elif arg <= 0xFF:
                    code += Op.PUSH1[arg]
                elif arg <= 0xFFFF:
                    code += Op.PUSH2[arg]
                elif arg <= 0xFFFFFF:
                    code += Op.PUSH3[arg]
                else:
                    code += Op.PUSH32[arg]
            code += config.opcode
    
    # Success marker
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    
    return code


def _create_size_variant_test(config: SizeVariantConfig):
    """Factory function to create a size variant test."""
    
    @pytest.mark.valid_from("Prague")
    @pytest.mark.parametrize(
        "op_count",
        generate_op_counts(config.max_op_count, config.step),
        ids=lambda x: f"op_count_{x}",
    )
    def test_func(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
        code = generate_marginal_program(config, op_count)
        contract = pre.deploy_contract(code=code)
        sender = pre.fund_eoa()
        tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender)
        post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
        state_test(env=Environment(), pre=pre, post=post, tx=tx)
    
    test_func.__name__ = f"test_{config.name}"
    test_func.__doc__ = f"Marginal cost test for {config.name}"
    return test_func


# ============================================================================
# KECCAK256 SIZE VARIANTS
# Gas formula: 30 + 6 * ceil(size/32)
# ============================================================================

def _generate_keccak256_setup(size: int) -> Bytecode:
    """Generate setup code that fills memory with data."""
    code = Bytecode()
    words_needed = (size + 31) // 32
    for i in range(min(words_needed, 256)):
        code += Op.MSTORE(i * 32, MAX_U256)
    return code

# Small: 32 bytes = 30 + 6 = 36 gas
KECCAK256_SMALL_CONFIG = SizeVariantConfig(
    name="keccak256_small",
    opcode=Op.SHA3,
    max_op_count=100,
    step=10,
    stack_args=[32, 0],  # size=32, offset=0
    pops_per_op=2,
    pushes_per_op=1,
    setup_code=Op.MSTORE(0, MAX_U256),
)

# Medium: 1KB = 30 + 6*32 = 222 gas
KECCAK256_MEDIUM_CONFIG = SizeVariantConfig(
    name="keccak256_medium",
    opcode=Op.SHA3,
    max_op_count=50,
    step=5,
    stack_args=[1024, 0],  # size=1KB, offset=0
    pops_per_op=2,
    pushes_per_op=1,
    setup_code=_generate_keccak256_setup(1024),
)

# Large: 8KB = 30 + 6*256 = 1566 gas
KECCAK256_LARGE_CONFIG = SizeVariantConfig(
    name="keccak256_large",
    opcode=Op.SHA3,
    max_op_count=30,
    step=5,
    stack_args=[8192, 0],  # size=8KB, offset=0
    pops_per_op=2,
    pushes_per_op=1,
    setup_code=_generate_keccak256_setup(8192),
)

test_keccak256_small = _create_size_variant_test(KECCAK256_SMALL_CONFIG)
test_keccak256_medium = _create_size_variant_test(KECCAK256_MEDIUM_CONFIG)
test_keccak256_large = _create_size_variant_test(KECCAK256_LARGE_CONFIG)


# ============================================================================
# CODECOPY SIZE VARIANTS
# Gas formula: 3 + 3 * ceil(size/32)
# ============================================================================

# Small: 0 bytes = 3 gas (minimum)
CODECOPY_SMALL_CONFIG = SizeVariantConfig(
    name="codecopy_small",
    opcode=Op.CODECOPY,
    max_op_count=200,
    step=20,
    stack_args=[0, 0, 0],  # size=0, offset=0, destOffset=0
    pops_per_op=3,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, 0),
)

# Medium: 1KB = 3 + 3*32 = 99 gas
CODECOPY_MEDIUM_CONFIG = SizeVariantConfig(
    name="codecopy_medium",
    opcode=Op.CODECOPY,
    max_op_count=100,
    step=10,
    stack_args=[1024, 0, 0],  # size=1KB, offset=0, destOffset=0
    pops_per_op=3,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, 0),
)

# Large: 8KB = 3 + 3*256 = 771 gas
CODECOPY_LARGE_CONFIG = SizeVariantConfig(
    name="codecopy_large",
    opcode=Op.CODECOPY,
    max_op_count=30,
    step=5,
    stack_args=[8192, 0, 0],  # size=8KB, offset=0, destOffset=0
    pops_per_op=3,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, 0),
)

test_codecopy_small = _create_size_variant_test(CODECOPY_SMALL_CONFIG)
test_codecopy_medium = _create_size_variant_test(CODECOPY_MEDIUM_CONFIG)
test_codecopy_large = _create_size_variant_test(CODECOPY_LARGE_CONFIG)


# ============================================================================
# CALLDATACOPY SIZE VARIANTS
# Gas formula: 3 + 3 * ceil(size/32)
# ============================================================================

# Small: 0 bytes = 3 gas
CALLDATACOPY_SMALL_CONFIG = SizeVariantConfig(
    name="calldatacopy_small",
    opcode=Op.CALLDATACOPY,
    max_op_count=200,
    step=20,
    stack_args=[0, 0, 0],  # size=0, offset=0, destOffset=0
    pops_per_op=3,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, 0),
)

# Medium: 1KB = 3 + 3*32 = 99 gas
CALLDATACOPY_MEDIUM_CONFIG = SizeVariantConfig(
    name="calldatacopy_medium",
    opcode=Op.CALLDATACOPY,
    max_op_count=100,
    step=10,
    stack_args=[1024, 0, 0],  # size=1KB, offset=0, destOffset=0
    pops_per_op=3,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, 0),
)

# Large: 8KB = 3 + 3*256 = 771 gas
CALLDATACOPY_LARGE_CONFIG = SizeVariantConfig(
    name="calldatacopy_large",
    opcode=Op.CALLDATACOPY,
    max_op_count=30,
    step=5,
    stack_args=[8192, 0, 0],  # size=8KB, offset=0, destOffset=0
    pops_per_op=3,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, 0),
)

test_calldatacopy_small = _create_size_variant_test(CALLDATACOPY_SMALL_CONFIG)
test_calldatacopy_medium = _create_size_variant_test(CALLDATACOPY_MEDIUM_CONFIG)
test_calldatacopy_large = _create_size_variant_test(CALLDATACOPY_LARGE_CONFIG)


# ============================================================================
# MCOPY SIZE VARIANTS
# Gas formula: 3 + 3 * ceil(size/32)
# ============================================================================

# Small: 0 bytes = 3 gas
MCOPY_SMALL_CONFIG = SizeVariantConfig(
    name="mcopy_small",
    opcode=Op.MCOPY,
    max_op_count=200,
    step=20,
    stack_args=[0, 0, 4096],  # size=0, srcOffset=0, destOffset=4096
    pops_per_op=3,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, MAX_U256) + Op.MSTORE(4096, 0),
)

# Medium: 1KB = 3 + 3*32 = 99 gas
MCOPY_MEDIUM_CONFIG = SizeVariantConfig(
    name="mcopy_medium",
    opcode=Op.MCOPY,
    max_op_count=100,
    step=10,
    stack_args=[1024, 0, 4096],  # size=1KB, srcOffset=0, destOffset=4096
    pops_per_op=3,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, MAX_U256) + Op.MSTORE(4096, 0),
)

# Large: 8KB = 3 + 3*256 = 771 gas
MCOPY_LARGE_CONFIG = SizeVariantConfig(
    name="mcopy_large",
    opcode=Op.MCOPY,
    max_op_count=30,
    step=5,
    stack_args=[8192, 0, 16384],  # size=8KB, srcOffset=0, destOffset=16KB
    pops_per_op=3,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, MAX_U256) + Op.MSTORE(16384, 0),
)

test_mcopy_small = _create_size_variant_test(MCOPY_SMALL_CONFIG)
test_mcopy_medium = _create_size_variant_test(MCOPY_MEDIUM_CONFIG)
test_mcopy_large = _create_size_variant_test(MCOPY_LARGE_CONFIG)


# ============================================================================
# EXTCODECOPY SIZE VARIANTS
# Gas formula: 100 (warm) + 3 * ceil(size/32)
# ============================================================================

# Small: 0 bytes = 100 gas (warm access only)
EXTCODECOPY_SMALL_CONFIG = SizeVariantConfig(
    name="extcodecopy_small",
    opcode=Op.EXTCODECOPY,
    max_op_count=100,
    step=10,
    stack_args=[0, 0, 0, 0xDEAD],  # size=0, offset=0, destOffset=0, address
    pops_per_op=4,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, 0) + Op.POP(Op.EXTCODESIZE(0xDEAD)),
)

# Medium: 256 bytes = 100 + 3*8 = 124 gas
EXTCODECOPY_MEDIUM_CONFIG = SizeVariantConfig(
    name="extcodecopy_medium",
    opcode=Op.EXTCODECOPY,
    max_op_count=80,
    step=10,
    stack_args=[256, 0, 0, 0xDEAD],  # size=256, offset=0, destOffset=0, address
    pops_per_op=4,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, 0) + Op.POP(Op.EXTCODESIZE(0xDEAD)),
)

# Large: 8KB = 100 + 3*256 = 868 gas
EXTCODECOPY_LARGE_CONFIG = SizeVariantConfig(
    name="extcodecopy_large",
    opcode=Op.EXTCODECOPY,
    max_op_count=30,
    step=5,
    stack_args=[8192, 0, 0, 0xDEAD],  # size=8KB, offset=0, destOffset=0, address
    pops_per_op=4,
    pushes_per_op=0,
    setup_code=Op.MSTORE(0, 0) + Op.POP(Op.EXTCODESIZE(0xDEAD)),
)

test_extcodecopy_small = _create_size_variant_test(EXTCODECOPY_SMALL_CONFIG)
test_extcodecopy_medium = _create_size_variant_test(EXTCODECOPY_MEDIUM_CONFIG)
test_extcodecopy_large = _create_size_variant_test(EXTCODECOPY_LARGE_CONFIG)


# ============================================================================
# LOG0 SIZE VARIANTS
# Gas formula: 375 + 8 * size
# ============================================================================

def generate_log0_program(data_size: int, op_count: int, max_op_count: int) -> Bytecode:
    """Generate a LOG0 test program."""
    code = Bytecode()
    
    # Setup: fill memory with data
    if data_size > 0:
        words_needed = (data_size + 31) // 32
        for i in range(min(words_needed, 32)):
            code += Op.MSTORE(i * 32, MAX_U256)
    
    # Push arguments for all operations
    for _ in range(max_op_count):
        code += Op.PUSH0  # offset = 0
        if data_size <= 0xFF:
            code += Op.PUSH1[data_size]
        elif data_size <= 0xFFFF:
            code += Op.PUSH2[data_size]
        else:
            code += Op.PUSH3[data_size]
    
    # Execute op_count LOG0 operations
    for _ in range(op_count):
        code += Op.LOG0
    
    # Pop remaining unused arguments
    for _ in range((max_op_count - op_count) * 2):
        code += Op.POP
    
    # Success marker
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)
    code += Op.STOP
    return code


def _create_log0_size_variant_test(data_size: int, max_op_count: int, step: int, name: str):
    """Factory for LOG0 size variant tests."""
    
    @pytest.mark.valid_from("Prague")
    @pytest.mark.parametrize(
        "op_count",
        generate_op_counts(max_op_count, step),
        ids=lambda x: f"op_count_{x}",
    )
    def test_func(state_test: StateTestFiller, pre: Alloc, op_count: int) -> None:
        code = generate_log0_program(data_size, op_count, max_op_count)
        contract = pre.deploy_contract(code=code)
        sender = pre.fund_eoa()
        tx = Transaction(to=contract, gas_limit=5_000_000, sender=sender)
        post = {contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})}
        state_test(env=Environment(), pre=pre, post=post, tx=tx)
    
    test_func.__name__ = f"test_{name}"
    test_func.__doc__ = f"Marginal cost test for LOG0 with {data_size} bytes data"
    return test_func


# Small: 0 bytes = 375 gas
test_log0_small = _create_log0_size_variant_test(
    data_size=0, max_op_count=50, step=5, name="log0_small"
)

# Medium: 32 bytes = 375 + 8*32 = 631 gas
test_log0_medium = _create_log0_size_variant_test(
    data_size=32, max_op_count=30, step=5, name="log0_medium"
)

# Large: 1KB = 375 + 8*1024 = 8567 gas
test_log0_large = _create_log0_size_variant_test(
    data_size=1024, max_op_count=15, step=3, name="log0_large"
)


# ============================================================================
# EXP SIZE VARIANTS (exponent byte length)
# Gas formula: 10 + 50 * byte_length(exponent)
# ============================================================================

# Small: 1-byte exponent = 10 + 50 = 60 gas
EXP_SMALL_CONFIG = SizeVariantConfig(
    name="exp_small",
    opcode=Op.EXP,
    max_op_count=100,
    step=10,
    stack_args=[0xFF, 2],  # exponent=255 (1 byte), base=2
    pops_per_op=2,
    pushes_per_op=1,
    setup_code=None,
)

# Medium: 8-byte exponent = 10 + 50*8 = 410 gas
EXP_MEDIUM_CONFIG = SizeVariantConfig(
    name="exp_medium",
    opcode=Op.EXP,
    max_op_count=50,
    step=5,
    stack_args=[0xFFFFFFFFFFFFFFFF, 2],  # exponent=8 bytes, base=2
    pops_per_op=2,
    pushes_per_op=1,
    setup_code=None,
)

# Large: 32-byte exponent = 10 + 50*32 = 1610 gas
EXP_LARGE_CONFIG = SizeVariantConfig(
    name="exp_large",
    opcode=Op.EXP,
    max_op_count=30,
    step=5,
    stack_args=[MAX_U256, 2],  # exponent=32 bytes (max), base=2
    pops_per_op=2,
    pushes_per_op=1,
    setup_code=None,
)

test_exp_small = _create_size_variant_test(EXP_SMALL_CONFIG)
test_exp_medium = _create_size_variant_test(EXP_MEDIUM_CONFIG)
test_exp_large = _create_size_variant_test(EXP_LARGE_CONFIG)
