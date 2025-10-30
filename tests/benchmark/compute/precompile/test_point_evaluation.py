"""Benchmark POINT EVALUATION precompile."""

import pytest
from execution_testing import (
    Address,
    BenchmarkTestFiller,
    Fork,
    JumpLoopGenerator,
    Op,
)

from tests.benchmark.compute.helpers import concatenate_parameters
from tests.cancun.eip4844_blobs.spec import Spec as BlobsSpec


@pytest.mark.parametrize(
    "precompile_address,calldata",
    [
        pytest.param(
            BlobsSpec.POINT_EVALUATION_PRECOMPILE_ADDRESS,
            concatenate_parameters(
                [
                    "01E798154708FE7789429634053CBF9F99B619F9F084048927333FCE637F549B",
                    "564C0A11A0F704F4FC3E8ACFE0F8245F0AD1347B378FBF96E206DA11A5D36306",
                    "24D25032E67A7E6A4910DF5834B8FE70E6BCFEEAC0352434196BDF4B2485D5A1",
                    "8F59A8D2A1A625A17F3FEA0FE5EB8C896DB3764F3185481BC22F91B4AAFFCCA25F26936857BC3A7C2539EA8EC3A952B7",
                    "873033E038326E87ED3E1276FD140253FA08E9FC25FB2D9A98527FC22A2C9612FBEAFDAD446CBC7BCDBDCD780AF2C16A",
                ]
            ),
            id="point_evaluation",
        ),
    ],
)
def test_point_evaluation(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    precompile_address: Address,
    calldata: bytes,
) -> None:
    """Benchmark POINT EVALUATION precompile."""
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
