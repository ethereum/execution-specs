"""Benchmark BLS12_381 precompile."""

import pytest
from execution_testing import (
    Address,
    BenchmarkTestFiller,
    Fork,
    JumpLoopGenerator,
    Op,
)

from tests.benchmark.compute.helpers import concatenate_parameters
from tests.prague.eip2537_bls_12_381_precompiles import spec as bls12381_spec


@pytest.mark.parametrize(
    "precompile_address,calldata",
    [
        pytest.param(
            bls12381_spec.Spec.G1ADD,
            concatenate_parameters(
                [
                    bls12381_spec.Spec.G1,
                    bls12381_spec.Spec.P1,
                ]
            ),
            id="bls12_g1add",
        ),
        pytest.param(
            bls12381_spec.Spec.G1MSM,
            concatenate_parameters(
                [
                    (
                        bls12381_spec.Spec.P1
                        + bls12381_spec.Scalar(bls12381_spec.Spec.Q)
                    )
                    * (len(bls12381_spec.Spec.G1MSM_DISCOUNT_TABLE) - 1),
                ]
            ),
            id="bls12_g1msm",
        ),
        pytest.param(
            bls12381_spec.Spec.G2ADD,
            concatenate_parameters(
                [
                    bls12381_spec.Spec.G2,
                    bls12381_spec.Spec.P2,
                ]
            ),
            id="bls12_g2add",
        ),
        pytest.param(
            bls12381_spec.Spec.G2MSM,
            concatenate_parameters(
                [
                    # TODO: the //2 is required due to a limitation of the max
                    # contract size limit. In a further iteration we can insert
                    # inputs as calldata or storage and avoid doing PUSHes
                    # which has this limitation. This also applies to G1MSM.
                    (
                        bls12381_spec.Spec.P2
                        + bls12381_spec.Scalar(bls12381_spec.Spec.Q)
                    )
                    * (len(bls12381_spec.Spec.G2MSM_DISCOUNT_TABLE) // 2),
                ]
            ),
            id="bls12_g2msm",
        ),
        pytest.param(
            bls12381_spec.Spec.PAIRING,
            concatenate_parameters(
                [
                    bls12381_spec.Spec.G1,
                    bls12381_spec.Spec.G2,
                ]
            ),
            id="bls12_pairing_check",
        ),
        pytest.param(
            bls12381_spec.Spec.MAP_FP_TO_G1,
            concatenate_parameters(
                [
                    bls12381_spec.FP(bls12381_spec.Spec.P - 1),
                ]
            ),
            id="bls12_fp_to_g1",
        ),
        pytest.param(
            bls12381_spec.Spec.MAP_FP2_TO_G2,
            concatenate_parameters(
                [
                    bls12381_spec.FP2(
                        (bls12381_spec.Spec.P - 1, bls12381_spec.Spec.P - 1)
                    ),
                ]
            ),
            id="bls12_fp_to_g2",
        ),
    ],
)
def test_bls12_381(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    precompile_address: Address,
    calldata: bytes,
) -> None:
    """Benchmark BLS12_381 precompile."""
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
