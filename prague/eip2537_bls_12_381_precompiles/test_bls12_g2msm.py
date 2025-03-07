"""
abstract: Tests BLS12_G2MSM precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    Tests BLS12_G2MSM precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537).
"""  # noqa: E501

import pytest

from ethereum_test_tools import Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools import Opcodes as Op

from .helpers import vectors_from_file
from .spec import PointG2, Scalar, Spec, ref_spec_2537

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = [
    pytest.mark.valid_from("Prague"),
    pytest.mark.parametrize("precompile_address", [Spec.G2MSM], ids=[""]),
]


@pytest.mark.parametrize(
    "input_data,expected_output,vector_gas_value",
    vectors_from_file("msm_G2_bls.json")
    + [
        pytest.param(
            (Spec.P2 + Scalar(Spec.Q)) * (len(Spec.G2MSM_DISCOUNT_TABLE) - 1),
            Spec.INF_G2,
            None,
            id="max_discount",
            marks=pytest.mark.slow,
        ),
        pytest.param(
            (Spec.P2 + Scalar(Spec.Q)) * len(Spec.G2MSM_DISCOUNT_TABLE),
            Spec.INF_G2,
            None,
            id="max_discount_plus_1",
            marks=pytest.mark.slow,
        ),
    ],
)
def test_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_G2MSM precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input_data",
    vectors_from_file("fail-msm_G2_bls.json")
    + [
        pytest.param(
            PointG2((1, 0), (0, 0)) + Scalar(0),
            id="invalid_point_a_1",
        ),
        pytest.param(
            PointG2((0, 1), (0, 0)) + Scalar(0),
            id="invalid_point_a_2",
        ),
        pytest.param(
            PointG2((0, 0), (1, 0)) + Scalar(0),
            id="invalid_point_a_3",
        ),
        pytest.param(
            PointG2((0, 0), (0, 1)) + Scalar(0),
            id="invalid_point_a_4",
        ),
        pytest.param(
            PointG2((Spec.P, 0), (0, 0)) + Scalar(0),
            id="x_1_equal_to_p",
        ),
        pytest.param(
            PointG2((0, Spec.P), (0, 0)) + Scalar(0),
            id="x_2_equal_to_p",
        ),
        pytest.param(
            PointG2((0, 0), (Spec.P, 0)) + Scalar(0),
            id="y_1_equal_to_p",
        ),
        pytest.param(
            PointG2((0, 0), (0, Spec.P)) + Scalar(0),
            id="y_2_equal_to_p",
        ),
        pytest.param(
            b"\x80" + bytes(Spec.INF_G2)[1:] + Scalar(0),
            id="invalid_encoding",
        ),
        pytest.param(
            Spec.P2_NOT_IN_SUBGROUP + Scalar(1),
            id="bls_g2mul_not_in_subgroup",
        ),
        pytest.param(
            Spec.G2,
            id="bls_g2_truncated_input",
        ),
        # Input length tests can be found in ./test_bls12_variable_length_input_contracts.py
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
def test_invalid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Negative tests for the BLS12_G2MSM precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "call_opcode",
    [
        Op.STATICCALL,
        Op.DELEGATECALL,
        Op.CALLCODE,
    ],
)
@pytest.mark.parametrize(
    "input_data,expected_output",
    [
        pytest.param(
            Spec.INF_G2 + Scalar(0),
            Spec.INF_G2,
            id="inf_times_zero",
        ),
    ],
)
def test_call_types(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_G2MSM precompile using different call types."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
