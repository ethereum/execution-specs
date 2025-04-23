"""
abstract: Tests BLS12_G1MSM precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    Tests BLS12_G1MSM precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537).
"""  # noqa: E501

import pytest

from ethereum_test_tools import Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools import Opcodes as Op

from .conftest import G1_POINTS_NOT_IN_SUBGROUP, G1_POINTS_NOT_ON_CURVE
from .helpers import vectors_from_file
from .spec import Scalar, Spec, ref_spec_2537

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = [
    pytest.mark.valid_from("Prague"),
    pytest.mark.parametrize("precompile_address", [Spec.G1MSM], ids=[""]),
]


@pytest.mark.parametrize(
    "input_data,expected_output,vector_gas_value",
    # Test vectors from the reference spec (from the cryptography team)
    vectors_from_file("msm_G1_bls.json")
    + [
        # Multiple pair scalar multiplication cases.
        pytest.param(
            Spec.G1 + Scalar(1) + Spec.INF_G1 + Scalar(1),
            Spec.G1,
            None,
            id="g1_plus_inf",
        ),
        pytest.param(
            Spec.G1 + Scalar(0) + Spec.P1 + Scalar(0) + Spec.INF_G1 + Scalar(0),
            Spec.INF_G1,
            None,
            id="all_zero_scalars",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + (-Spec.G1) + Scalar(1),
            Spec.INF_G1,
            None,
            id="sum_to_identity_opposite",
        ),
        pytest.param(
            Spec.G1 + Scalar(Spec.Q - 1) + Spec.G1 + Scalar(1),
            Spec.INF_G1,
            None,
            id="scalars_sum_to_q",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + Spec.G1 + Scalar(0) + Spec.INF_G1 + Scalar(5),
            Spec.G1,
            None,
            id="combined_basic_cases",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + Spec.INF_G1 + Scalar(500),
            Spec.G1,
            None,
            id="identity_with_large_scalar",
        ),
        pytest.param(
            Spec.G1 + Scalar(0) + Spec.P1 + Scalar(0) + (-Spec.G1) + Scalar(0),
            Spec.INF_G1,
            None,
            id="multiple_points_zero_scalar",
        ),
        # Cases with maximum discount table (test vector for gas cost calculation)
        pytest.param(
            (Spec.P1 + Scalar(Spec.Q)) * (len(Spec.G1MSM_DISCOUNT_TABLE) - 1),
            Spec.INF_G1,
            None,
            id="max_discount",
        ),
        pytest.param(
            (Spec.P1 + Scalar(Spec.Q)) * len(Spec.G1MSM_DISCOUNT_TABLE),
            Spec.INF_G1,
            None,
            id="max_discount_plus_1",
        ),
    ],
)
def test_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test valid calls to the BLS12_G1MSM precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input_data",
    # Test vectors from the reference spec (from the cryptography team)
    vectors_from_file("fail-msm_G1_bls.json")
    + [
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Scalar(Spec.Q),
            id="not_in_subgroup_1_pos_0",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP_TIMES_2 + Scalar(Spec.Q),
            id="not_in_subgroup_2_pos_0",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + Spec.P1_NOT_IN_SUBGROUP + Scalar(Spec.Q),
            id="not_in_subgroup_1_pos_1",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + Spec.P1_NOT_IN_SUBGROUP_TIMES_2 + Scalar(Spec.Q),
            id="not_in_subgroup_2_pos_1",
        ),
        pytest.param(
            Spec.G1,
            id="bls_g1_truncated_input",
        ),
        pytest.param(
            G1_POINTS_NOT_IN_SUBGROUP[0] + Scalar(0),
            id="rand_not_in_subgroup_0_pos_0",
        ),
        pytest.param(
            G1_POINTS_NOT_IN_SUBGROUP[1] + Scalar(1),
            id="rand_not_in_subgroup_1_pos_0",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + G1_POINTS_NOT_IN_SUBGROUP[0] + Scalar(0),
            id="rand_not_in_subgroup_0_pos_1",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + G1_POINTS_NOT_IN_SUBGROUP[1] + Scalar(1),
            id="rand_not_in_subgroup_1_pos_1",
        ),
        pytest.param(
            G1_POINTS_NOT_ON_CURVE[0] + Scalar(0),
            id="not_on_curve_0_pos_0",
        ),
        pytest.param(
            G1_POINTS_NOT_ON_CURVE[1] + Scalar(1),
            id="not_on_curve_1_pos_0",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + G1_POINTS_NOT_ON_CURVE[0] + Scalar(0),
            id="not_on_curve_0_pos_1",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + G1_POINTS_NOT_ON_CURVE[1] + Scalar(1),
            id="not_on_curve_1_pos_1",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + Spec.G1,
            id="incomplete_input_missing_scalar",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + bytes([0]),
            id="incomplete_input_extra_byte",
        ),
        pytest.param(
            Spec.G1 + Scalar(1) + Spec.G2 + Scalar(1),
            id="mixing_g1_with_g2",
        ),
        pytest.param(
            Spec.G1 + (b"\x01" + b"\x00" * 32),  # Scalar > UINT256_MAX
            id="scalar_too_large",
        ),
        pytest.param(
            Spec.G1 + Scalar(1).x.to_bytes(16, byteorder="big"),  # Invalid scalar length
            id="scalar_too_short",
        ),
        pytest.param(
            bytes([0]) * 159,  # Just under minimum valid length
            id="input_too_short_by_1",
        ),
    ],
    # Input length tests can be found in ./test_bls12_variable_length_input_contracts.py
)
@pytest.mark.parametrize(
    "precompile_gas_modifier", [100_000], ids=[""]
)  # Add gas so that won't be the cause of failure
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
def test_invalid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test invalid calls to the BLS12_G1MSM precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "call_opcode",  # Note `Op.CALL` is used for all the `test_valid` cases.
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
            Spec.INF_G1 + Scalar(0),
            Spec.INF_G1,
            id="single_inf_times_zero",
        ),
        pytest.param(
            (Spec.P1 + Scalar(Spec.Q)) * (len(Spec.G1MSM_DISCOUNT_TABLE) - 1),
            Spec.INF_G1,
            id="max_discount",
        ),
    ],
)
def test_call_types(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_G1MSM precompile using different call types."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
