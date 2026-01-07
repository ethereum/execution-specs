"""Benchmark IDENTITY precompile."""

import pytest
from execution_testing import (
    BenchmarkTestFiller,
    Fork,
    JumpLoopGenerator,
    Op,
)

from tests.benchmark.compute.helpers import calculate_optimal_input_length


def test_identity(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    tx_gas_limit: int,
) -> None:
    """Benchmark IDENTITY precompile."""
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    gas_available = tx_gas_limit - intrinsic_gas_calculator()

    optimal_input_length = calculate_optimal_input_length(
        available_gas=gas_available,
        fork=fork,
        static_cost=15,
        per_word_dynamic_cost=3,
        bytes_per_unit_of_work=1,
    )

    attack_block = Op.POP(
        Op.STATICCALL(
            Op.GAS, 0x04, Op.PUSH0, optimal_input_length, Op.PUSH0, Op.PUSH0
        )
    )

    benchmark_test(
        target_opcode=Op.STATICCALL,
        code_generator=JumpLoopGenerator(
            setup=Op.CODECOPY(0, 0, optimal_input_length),
            attack_block=attack_block,
        ),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("size", [0, 32, 256, 1024])
def test_identity_fixed_size(
    benchmark_test: BenchmarkTestFiller, size: int
) -> None:
    """Benchmark IDENTITY with fixed size input."""
    attack_block = Op.POP(
        Op.STATICCALL(Op.GAS, 0x04, Op.PUSH0, size, Op.PUSH0, Op.PUSH0)
    )

    benchmark_test(
        target_opcode=Op.STATICCALL,
        code_generator=JumpLoopGenerator(
            setup=Op.CODECOPY(0, 0, size), attack_block=attack_block
        ),
    )
