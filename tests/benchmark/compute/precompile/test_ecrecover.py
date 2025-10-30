"""Benchmark ECRECOVER precompile."""

import pytest
from execution_testing import (
    Address,
    BenchmarkTestFiller,
    Fork,
    JumpLoopGenerator,
    Op,
)

from tests.benchmark.compute.helpers import concatenate_parameters


@pytest.mark.parametrize(
    "precompile_address,calldata",
    [
        pytest.param(
            0x01,
            concatenate_parameters(
                [
                    # Inputs below are a valid signature, thus ECRECOVER call
                    # will perform full computation, not blocked by validation.
                    "38D18ACB67D25C8BB9942764B62F18E17054F66A817BD4295423ADF9ED98873E",
                    "000000000000000000000000000000000000000000000000000000000000001B",
                    "38D18ACB67D25C8BB9942764B62F18E17054F66A817BD4295423ADF9ED98873E",
                    "789D1DD423D25F0772D2748D60F7E4B81BB14D086EBA8E8E8EFB6DCFF8A4AE02",
                ]
            ),
            id="ecrecover",
        )
    ],
)
def test_ecrecover(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    precompile_address: Address,
    calldata: bytes,
) -> None:
    """Benchmark ECRECOVER precompile."""
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
