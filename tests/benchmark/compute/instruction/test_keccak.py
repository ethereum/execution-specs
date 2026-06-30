"""
Benchmark keccak instructions.

Supported Opcodes:
- KECCAK256
"""

import math

import pytest
from execution_testing import (
    BenchmarkTestFiller,
    Bytecode,
    Fork,
    JumpLoopGenerator,
    Op,
)

KECCAK_RATE = 136


def test_keccak_max_permutations(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    tx_gas_limit: int,
) -> None:
    """Benchmark KECCAK256 instruction to maximize permutations per block."""
    # Intrinsic gas cost is paid once.
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    available_gas = tx_gas_limit - intrinsic_gas_calculator()

    mem_exp_gas_calculator = fork.memory_expansion_gas_calculator()

    def attack_block_for(input_length: int) -> Bytecode:
        """Return the keccak attack block hashing `input_length` bytes."""
        return Op.POP(Op.SHA3(Op.PUSH0, Op.DUP1, data_size=input_length))

    # Only SHA3's per-word cost varies with the input size, so the attack
    # block's per-call gas is affine in the keccak word count. Precompute
    # the size-independent base once instead of rebuilding the bytecode and
    # recomputing its gas each iteration (the search's bottleneck); the
    # discovered `optimal_input_length`, and so the fixture, is unchanged.
    base_iteration_gas_cost = attack_block_for(0).gas_cost(fork)
    keccak_word_gas_cost = fork.gas_costs().OPCODE_KECCAK256_PER_WORD

    def per_call_gas_cost(input_length: int) -> int:
        """Return the per-call gas of the keccak attack block."""
        word_count = (input_length + 31) // 32
        return base_iteration_gas_cost + keccak_word_gas_cost * word_count

    # The input lengths examined by the discovery search below.
    search_lengths = range(1, 1_000_000, 32)

    # Guard the affine model: if a future fork reprices keccak non-linearly,
    # fail here instead of silently discovering a different optimum. The
    # samples straddle the 32-byte word boundary and span the search range.
    for sample_length in (1, 31, 32, 33, KECCAK_RATE, search_lengths[-1]):
        assert per_call_gas_cost(sample_length) == attack_block_for(
            sample_length
        ).gas_cost(fork), (
            "keccak gas is no longer affine in the input word count; the "
            "analytic search optimization is invalid for this fork"
        )

    # Discover the optimal input size to maximize keccak-permutations,
    # not to maximize keccak calls.
    # The complication of the discovery arises from
    # the non-linear gas cost of memory expansion.
    max_keccak_perm_per_block = 0
    optimal_input_length = 0
    for i in search_lengths:
        # Iteration cost disregarding memory expansion.
        iteration_gas_cost = per_call_gas_cost(i)
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
        target_opcode=Op.SHA3,
        code_generator=JumpLoopGenerator(
            setup=Op.PUSH20[optimal_input_length],
            attack_block=attack_block_for(optimal_input_length),
        ),
    )


@pytest.mark.parametrize("mem_alloc", [b"", b"ff", b"ff" * 32])
@pytest.mark.parametrize("offset", [0, 31, 1024])
@pytest.mark.parametrize("mem_update", [True, False])
def test_keccak(
    benchmark_test: BenchmarkTestFiller,
    offset: int,
    mem_alloc: bytes,
    mem_update: bool,
) -> None:
    """Benchmark KECCAK256 instruction with diff input data and offsets."""
    code_hash = Op.SHA3(offset, Op.CALLDATASIZE)
    attack_block = (
        Op.MSTORE(Op.PUSH0, code_hash) if mem_update else Op.POP(code_hash)
    )

    benchmark_test(
        target_opcode=Op.SHA3,
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(offset, Op.PUSH0, Op.CALLDATASIZE),
            attack_block=attack_block,
            tx_kwargs={"data": mem_alloc},
        ),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("mem_size", [0, 32, 256, 1024])
@pytest.mark.parametrize("msg_size", [0, 32, 256, 1024])
def test_keccak_diff_mem_msg_sizes(
    benchmark_test: BenchmarkTestFiller,
    mem_size: int,
    msg_size: int,
) -> None:
    """Benchmark KECCAK256 instruction with diff memory and message sizes."""
    # Setup expands memory to mem_size bytes (if > 0) by storing a value
    # Then the attack block hashes msg_size bytes starting from offset 0.
    setup = Op.MSTORE8(mem_size - 1, 0xFF) if mem_size > 0 else Bytecode()

    benchmark_test(
        target_opcode=Op.SHA3,
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=Op.MSTORE(Op.PUSH0, Op.SHA3(Op.PUSH0, msg_size)),
        ),
    )
