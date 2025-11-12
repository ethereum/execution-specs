"""
Benchmark keccak instructions.

Supported Opcodes:
- KECCAK256
"""

import math

import pytest
from execution_testing import (
    BenchmarkTestFiller,
    Fork,
    JumpLoopGenerator,
    Op,
)

KECCAK_RATE = 136


@pytest.mark.repricing
def test_keccak_max_permutations(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    tx_gas_limit: int,
) -> None:
    """Benchmark KECCAK256 instruction to maximize permutations per block."""
    # Intrinsic gas cost is paid once.
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    available_gas = tx_gas_limit - intrinsic_gas_calculator()

    gsc = fork.gas_costs()
    mem_exp_gas_calculator = fork.memory_expansion_gas_calculator()

    # Discover the optimal input size to maximize keccak-permutations,
    # not to maximize keccak calls.
    # The complication of the discovery arises from
    # the non-linear gas cost of memory expansion.
    max_keccak_perm_per_block = 0
    optimal_input_length = 0
    for i in range(1, 1_000_000, 32):
        iteration_gas_cost = (
            2 * gsc.G_VERY_LOW  # PUSHN + PUSH1
            + gsc.G_KECCAK_256  # KECCAK256 static cost
            + math.ceil(i / 32) * gsc.G_KECCAK_256_WORD  # KECCAK256 dynamic
            # cost
            + gsc.G_BASE  # POP
        )
        # From the available gas, we subtract the mem expansion costs
        # considering we know the current input size length i.
        available_gas_after_expansion = max(
            0, available_gas - mem_exp_gas_calculator(new_bytes=i)
        )
        # Calculate how many calls we can do.
        num_keccak_calls = available_gas_after_expansion // iteration_gas_cost
        # KECCAK does 1 permutation every 136 bytes.
        num_keccak_permutations = num_keccak_calls * math.ceil(i / KECCAK_RATE)

        # If we found an input size that is better (reg permutations/gas), then
        # save it.
        if num_keccak_permutations > max_keccak_perm_per_block:
            max_keccak_perm_per_block = num_keccak_permutations
            optimal_input_length = i

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=Op.PUSH20[optimal_input_length],
            attack_block=Op.POP(Op.SHA3(Op.PUSH0, Op.DUP1)),
        ),
    )


@pytest.mark.parametrize("mem_alloc", [b"", b"ff", b"ff" * 32])
@pytest.mark.parametrize("offset", [0, 31, 1024])
def test_keccak(
    benchmark_test: BenchmarkTestFiller,
    offset: int,
    mem_alloc: bytes,
) -> None:
    """Benchmark KECCAK256 instruction with diff input data and offsets."""
    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(offset, Op.PUSH0, Op.CALLDATASIZE),
            attack_block=Op.POP(Op.SHA3(offset, Op.CALLDATASIZE)),
            tx_kwargs={"data": mem_alloc},
        ),
    )
