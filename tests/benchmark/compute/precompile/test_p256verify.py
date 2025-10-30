"""Benchmark P256VERIFY precompile."""

import pytest
from execution_testing import (
    Address,
    BenchmarkTestFiller,
    Fork,
    JumpLoopGenerator,
    Op,
)

from tests.benchmark.compute.helpers import concatenate_parameters
from tests.osaka.eip7951_p256verify_precompiles import spec as p256verify_spec


@pytest.mark.parametrize(
    "precompile_address,calldata",
    [
        pytest.param(
            p256verify_spec.Spec.P256VERIFY,
            concatenate_parameters(
                [
                    p256verify_spec.Spec.H0,
                    p256verify_spec.Spec.R0,
                    p256verify_spec.Spec.S0,
                    p256verify_spec.Spec.X0,
                    p256verify_spec.Spec.Y0,
                ]
            ),
            id="p256verify",
            marks=[
                pytest.mark.eip_checklist(
                    "precompile/test/excessive_gas_usage", eip=[7951]
                )
            ],
        ),
        pytest.param(
            p256verify_spec.Spec.P256VERIFY,
            concatenate_parameters(
                [
                    "235060CAFE19A407880C272BC3E73600E3A12294F56143ED61929C2FF4525ABB",
                    "182E5CBDF96ACCB859E8EEA1850DE5FF6E430A19D1D9A680ECD5946BBEA8A32B",
                    "76DDFAE6797FA6777CAAB9FA10E75F52E70A4E6CEB117B3C5B2F445D850BD64C",
                    "3828736CDFC4C8696008F71999260329AD8B12287846FEDCEDE3BA1205B12729",
                    "3E5141734E971A8D55015068D9B3666760F4608A49B11F92E500ACEA647978C7",
                ]
            ),
            id="p256verify_wrong_endianness",
        ),
        pytest.param(
            p256verify_spec.Spec.P256VERIFY,
            concatenate_parameters(
                [
                    "BB5A52F42F9C9261ED4361F59422A1E30036E7C32B270C8807A419FECA605023",
                    "000000000000000000000000000000004319055358E8617B0C46353D039CDAAB",
                    "FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC63254E",
                    "0AD99500288D466940031D72A9F5445A4D43784640855BF0A69874D2DE5FE103",
                    "C5011E6EF2C42DCD50D5D3D29F99AE6EBA2C80C9244F4C5422F0979FF0C3BA5E",
                ]
            ),
            id="p256verify_modular_comp_x_coordinate_exceeds_n",
        ),
    ],
)
def test_p256verify(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    precompile_address: Address,
    calldata: bytes,
) -> None:
    """Benchmark P256VERIFY precompile."""
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
