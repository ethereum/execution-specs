"""Benchmark SHA256 precompile."""

from ethereum_test_benchmark import JumpLoopGenerator
from ethereum_test_forks import Fork
from ethereum_test_tools import (
    BenchmarkTestFiller,
)
from ethereum_test_vm import Opcodes as Op

from tests.benchmark.compute.helpers import calculate_optimal_input_length


def test_sha256(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    tx_gas_limit: int,
) -> None:
    """Benchmark SHA256 precompile."""
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    gas_available = tx_gas_limit - intrinsic_gas_calculator()

    optimal_input_length = calculate_optimal_input_length(
        available_gas=gas_available,
        fork=fork,
        static_cost=60,
        per_word_dynamic_cost=12,
        bytes_per_unit_of_work=64,
    )

    attack_block = Op.POP(
        Op.STATICCALL(
            Op.GAS, 0x02, Op.PUSH0, optimal_input_length, Op.PUSH0, Op.PUSH0
        )
    )

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=Op.CODECOPY(0, 0, optimal_input_length),
            attack_block=attack_block,
        ),
    )
