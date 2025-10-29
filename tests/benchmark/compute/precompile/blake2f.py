"""Benchmark BLAKE2F precompile."""

import pytest
from execution_testing import (
    Address,
    BenchmarkTestFiller,
    Fork,
    JumpLoopGenerator,
    Op,
)

from tests.benchmark.compute.helpers import concatenate_parameters
from tests.istanbul.eip152_blake2.common import Blake2bInput
from tests.istanbul.eip152_blake2.spec import Spec as Blake2bSpec


@pytest.mark.parametrize(
    "precompile_address,calldata",
    [
        pytest.param(
            Blake2bSpec.BLAKE2_PRECOMPILE_ADDRESS,
            concatenate_parameters(
                [
                    Blake2bInput(
                        rounds=0xFFFF, f=True
                    ).create_blake2b_tx_data(),
                ]
            ),
            id="blake2f",
        ),
    ],
)
def test_blake2f(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    precompile_address: Address,
    calldata: bytes,
) -> None:
    """Benchmark BLAKE2F precompile."""
    if precompile_address not in fork.precompiles():
        pytest.skip("Precompile not enabled")

    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS, address=precompile_address, args_size=Op.CALLDATASIZE
        ),
    )

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),
            attack_block=attack_block,
            tx_kwargs={"data": calldata},
        ),
    )
