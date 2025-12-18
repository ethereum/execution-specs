"""
Marginal cost estimation tests for EVM precompiles.

This module implements the "marginal approach" for gas cost estimation of precompiles.
Precompiles require a different approach than opcodes since they are called via
CALL/STATICCALL rather than being executed directly.

Program layout for precompile marginal measurement:
    | Setup memory with precompile input |
    | STATICCALL to precompile × op_count |
    | Dummy work (NOPs) × (max_op_count - op_count) |
    | SSTORE success marker |
    | STOP |

The "dummy work" ensures the program structure remains constant regardless of op_count.
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

# Precompile addresses
ECRECOVER_ADDRESS = Address(0x01)
MODEXP_ADDRESS = Address(0x05)


@dataclass
class MarginalPrecompileConfig:
    """Configuration for a marginal precompile test."""

    name: str
    """Name of the precompile for test identification."""

    address: Address
    """Address of the precompile."""

    max_op_count: int
    """Maximum number of precompile calls."""

    step: int
    """Step size for op_count increments."""

    input_data: bytes
    """Input data for the precompile call."""

    input_size: int
    """Size of input data in memory."""


def create_ecrecover_input(
    msg_hash: bytes,
    v: int,
    r: bytes,
    s: bytes,
) -> bytes:
    """
    Create ECRECOVER precompile input.
    
    Input format: hash (32 bytes) | v (32 bytes) | r (32 bytes) | s (32 bytes) = 128 bytes
    """
    return (
        msg_hash
        + v.to_bytes(32, "big")
        + r
        + s
    )


def create_modexp_input(
    base: bytes,
    exponent: bytes,
    modulus: bytes,
) -> bytes:
    """
    Create MODEXP precompile input.
    
    Input format:
        base_length (32 bytes) | exponent_length (32 bytes) | modulus_length (32 bytes)
        | base (base_length bytes) | exponent (exponent_length bytes) | modulus (modulus_length bytes)
    """
    return (
        len(base).to_bytes(32, "big")
        + len(exponent).to_bytes(32, "big")
        + len(modulus).to_bytes(32, "big")
        + base
        + exponent
        + modulus
    )


# Valid ECRECOVER input that performs full signature recovery (worst case)
# This is a valid signature that will actually recover an address
# Taken from gas-cost-estimator's ECRECOVER test case
ECRECOVER_INPUT = create_ecrecover_input(
    msg_hash=bytes.fromhex("456e9aea5e197a1f1af7a3e85a3212fa4049a3ba34c2289b4c860fc0b0c64ef3"),
    v=28,  # 0x1c
    r=bytes.fromhex("9242685bf161793cc25603c231bc2f568eb630ea16aa137d2664ac8038825608"),
    s=bytes.fromhex("4f8ae3bd7535248d0bd448298cc2e2071e56992d0774dc340c368ae950852ada"),
)

ECRECOVER_CONFIG = MarginalPrecompileConfig(
    name="ECRECOVER",
    address=ECRECOVER_ADDRESS,
    max_op_count=4,  # ECRECOVER costs 3000 gas, so we can do many calls
    step=1,
    input_data=ECRECOVER_INPUT,
    input_size=len(ECRECOVER_INPUT),  # 128 bytes
)

# MODEXP true worst-case input: 256-byte (2048-bit) inputs
# B = 2^2048 - 1 (all 0xff for 256 bytes)
# E = 2^2048 - 1 (all 0xff for 256 bytes)
# M = 2^2048 - 3 (all 0xff except last byte is 0xfd for odd modulus)
# This costs ~698,709 gas per call (EIP-2565)
MODEXP_INPUT = create_modexp_input(
    base=bytes.fromhex("ff" * 256),      # 2^2048 - 1
    exponent=bytes.fromhex("ff" * 256),  # 2^2048 - 1
    modulus=bytes.fromhex("ff" * 255 + "fd"),  # 2^2048 - 3 (odd)
)

MODEXP_CONFIG = MarginalPrecompileConfig(
    name="MODEXP",
    address=MODEXP_ADDRESS,
    max_op_count=3,  # ~699K gas per call, need high gas limit
    step=1,
    input_data=MODEXP_INPUT,
    input_size=len(MODEXP_INPUT),  # 96 + 256 + 256 + 256 = 864 bytes
)


def generate_marginal_precompile_program(
    config: MarginalPrecompileConfig,
    op_count: int,
) -> tuple[Bytecode, bytes]:
    """
    Generate a marginal program for a precompile.

    Returns:
        Tuple of (bytecode, calldata) where calldata contains the precompile input
    """
    assert 0 <= op_count <= config.max_op_count

    code = Bytecode()

    # 1. Copy calldata (precompile input) to memory at offset 0
    code += Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)

    # 2. Call precompile op_count times
    # Each call: STATICCALL(gas, addr, argsOffset, argsSize, retOffset, retSize)
    # Pass all available gas - unused gas is returned after the call
    # IMPORTANT: ret_offset must be AFTER the input data to avoid corrupting it!
    # Input is at [0, input_size), so we write result at input_size
    ret_offset = config.input_size
    for _ in range(op_count):
        code += Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=config.address,
                args_offset=0,
                args_size=config.input_size,
                ret_offset=ret_offset,
                ret_size=32,
            )
        )

    # 3. "Dummy work" for remaining iterations to keep bytecode structure similar
    # Use cheap operations that don't affect state
    # We use PUSH0 + POP as a no-op that takes minimal gas
    nop_count = config.max_op_count - op_count
    for _ in range(nop_count):
        # This is a lightweight placeholder - adjust if needed for better calibration
        code += Op.PUSH0 + Op.POP

    # 4. Write success marker to storage
    code += Op.SSTORE(SUCCESS_SLOT, SUCCESS_MARKER)

    # 5. Stop
    code += Op.STOP

    return code, config.input_data


def generate_op_counts(max_op_count: int, step: int) -> List[int]:
    """Generate list of op_counts from 0 to max_op_count with given step."""
    counts = list(range(0, max_op_count + 1, step))
    # Ensure max_op_count is included even if not aligned with step
    if counts[-1] != max_op_count:
        counts.append(max_op_count)
    return counts


# ============================================================================
# ECRECOVER precompile tests (3000 gas per call)
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(ECRECOVER_CONFIG.max_op_count, ECRECOVER_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_ecrecover(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for ECRECOVER precompile.

    Generates a program with exactly `op_count` ECRECOVER calls.
    Uses a valid signature input that performs full EC recovery (worst case).
    ECRECOVER has a fixed gas cost of 3000 per call.

    The test verifies execution completed successfully via storage marker.
    """
    code, calldata = generate_marginal_precompile_program(ECRECOVER_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=1_000_000,
        data=calldata,
        sender=sender,
    )

    # Verify execution completed successfully (didn't revert)
    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


# ============================================================================
# MODEXP precompile tests (variable gas cost based on input sizes)
# ============================================================================


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "op_count",
    generate_op_counts(MODEXP_CONFIG.max_op_count, MODEXP_CONFIG.step),
    ids=lambda x: f"op_count_{x}",
)
def test_marginal_modexp(
    state_test: StateTestFiller,
    pre: Alloc,
    op_count: int,
) -> None:
    """
    Marginal cost estimation test for MODEXP precompile.

    Generates a program with exactly `op_count` MODEXP calls.
    Uses true worst-case input: 256-byte (2048-bit) base, exponent, and modulus,
    all set to maximum values for maximum computational work.
    - B = 2^2048 - 1, E = 2^2048 - 1, M = 2^2048 - 3
    - Gas cost: ~698,709 per call (EIP-2565)

    The test verifies execution completed successfully via storage marker.
    """
    code, calldata = generate_marginal_precompile_program(MODEXP_CONFIG, op_count)
    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=10_000_000,  # High limit for worst-case MODEXP (~700K gas per call)
        data=calldata,
        sender=sender,
    )

    # Verify execution completed successfully (didn't revert)
    post = {
        contract: Account(storage={SUCCESS_SLOT: SUCCESS_MARKER})
    }

    state_test(env=Environment(gas_limit=100_000_000), pre=pre, post=post, tx=tx)
