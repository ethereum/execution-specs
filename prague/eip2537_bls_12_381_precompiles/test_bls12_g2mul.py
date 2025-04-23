"""
abstract: Tests BLS12_G2MUL precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    Tests BLS12_G2MUL precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537).
"""  # noqa: E501

import pytest

from ethereum_test_tools import Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools import Opcodes as Op

from .conftest import G2_POINTS_NOT_IN_SUBGROUP, G2_POINTS_NOT_ON_CURVE
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
    # Test vectors from the reference spec (from the cryptography team)
    vectors_from_file("mul_G2_bls.json")
    + [
        # Basic multiplication test cases.
        pytest.param(
            Spec.INF_G2 + Scalar(0),
            Spec.INF_G2,
            None,
            id="zero_times_inf",
        ),
        pytest.param(
            Spec.INF_G2 + Scalar(1),
            Spec.INF_G2,
            None,
            id="one_times_inf",
        ),
        pytest.param(
            Spec.INF_G2 + Scalar(2),
            Spec.INF_G2,
            None,
            id="two_times_inf",
        ),
        pytest.param(
            Spec.INF_G2 + Scalar(Spec.Q),
            Spec.INF_G2,
            None,
            id="q_times_inf",
        ),
        pytest.param(
            Spec.INF_G2 + Scalar(2**256 - 1),
            Spec.INF_G2,
            None,
            id="max_scalar_times_inf",
        ),
        pytest.param(
            Spec.G2 + Scalar(0),
            Spec.INF_G2,
            None,
            id="zero_times_generator",
        ),
        pytest.param(
            Spec.P2 + Scalar(0),
            Spec.INF_G2,
            None,
            id="zero_times_point",
        ),
        pytest.param(
            Spec.G2 + Scalar(1),
            Spec.G2,
            None,
            id="one_times_generator",
        ),
        pytest.param(
            Spec.P2 + Scalar(1),
            Spec.P2,
            None,
            id="one_times_point",
        ),
        pytest.param(
            Spec.P2 + Scalar(2**256 - 1),
            PointG2(
                (
                    0x2663E1C3431E174CA80E5A84489569462E13B52DA27E7720AF5567941603475F1F9BC0102E13B92A0A21D96B94E9B22,  # noqa: E501
                    0x6A80D056486365020A6B53E2680B2D72D8A93561FC2F72B960936BB16F509C1A39C4E4174A7C9219E3D7EF130317C05,  # noqa: E501
                ),
                (
                    0xC49EAD39E9EB7E36E8BC25824299661D5B6D0E200BBC527ECCB946134726BF5DBD861E8E6EC946260B82ED26AFE15FB,  # noqa: E501
                    0x5397DAD1357CF8333189821B737172B18099ECF7EE8BDB4B3F05EBCCDF40E1782A6C71436D5ACE0843D7F361CBC6DB2,  # noqa: E501
                ),
            ),
            None,
            id="max_scalar_times_point",
        ),
        # Subgroup related test cases.
        pytest.param(
            Spec.P2 + Scalar(Spec.Q - 1),
            -Spec.P2,  # negated P2
            None,
            id="q_minus_1_times_point",
        ),
        pytest.param(
            Spec.P2 + Scalar(Spec.Q),
            Spec.INF_G2,
            None,
            id="q_times_point",
        ),
        pytest.param(
            Spec.G2 + Scalar(Spec.Q),
            Spec.INF_G2,
            None,
            id="q_times_generator",
        ),
        pytest.param(
            Spec.P2 + Scalar(Spec.Q + 1),
            Spec.P2,
            None,
            id="q_plus_1_times_point",
        ),
        pytest.param(
            Spec.P2 + Scalar(2 * Spec.Q),
            Spec.INF_G2,
            None,
            id="2q_times_point",
        ),
        pytest.param(
            Spec.P2 + Scalar((2**256 // Spec.Q) * Spec.Q),
            Spec.INF_G2,
            None,
            id="large_multiple_of_q_times_point",
        ),
    ],
)
def test_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_G2MUL precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input_data",
    # Test vectors from the reference spec (from the cryptography team)
    vectors_from_file("fail-mul_G2_bls.json")
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
            id="x_1_equal_to_p_times_0",
        ),
        pytest.param(
            PointG2((0, Spec.P), (0, 0)) + Scalar(0),
            id="x_2_equal_to_p_times_0",
        ),
        pytest.param(
            PointG2((0, 0), (Spec.P, 0)) + Scalar(0),
            id="y_1_equal_to_p_times_0",
        ),
        pytest.param(
            PointG2((0, 0), (0, Spec.P)) + Scalar(0),
            id="y_2_equal_to_p_times_0",
        ),
        pytest.param(
            PointG2((Spec.P + 1, 0), (0, 0)) + Scalar(0),
            id="x1_above_modulus_times_0",
        ),
        pytest.param(
            PointG2(
                (0x01, 0),  # x coordinate in Fp2 (1 + 0i)
                (0x07, 0),  # y coordinate satisfying y^2 = x^3 + 5 in Fp2
            )
            + Scalar(0),
            id="point_on_wrong_curve_times_0",
        ),
        pytest.param(
            b"\x80" + bytes(Spec.INF_G2)[1:] + Scalar(0),
            id="invalid_encoding",
        ),
        pytest.param(
            (Spec.INF_G2 + Scalar(0))[:-1],
            id="input_too_short",
        ),
        pytest.param(
            b"\x00" + (Spec.INF_G2 + Scalar(0)),
            id="input_too_long",
        ),
        pytest.param(
            b"",
            id="zero_length_input",
        ),
        pytest.param(
            b"\x00" * 160,
            id="all_zero_160_bytes",
        ),
        pytest.param(
            b"\xff" + b"\x00" * 127 + b"\xff" + b"\x00" * 31,
            id="bad_inf_flag_with_scalar",
        ),
        pytest.param(
            b"\xc0" + b"\x00" * 127 + b"\x00" * 32,
            id="comp_instead_of_uncomp_with_scalar",
        ),
        pytest.param(
            Spec.G1 + Spec.G1,
            id="g1_input_invalid_length",
        ),
        pytest.param(
            Spec.G2 + Spec.G2,
            id="g2_input_invalid_length",
        ),
        pytest.param(
            Spec.G2,
            id="g2_truncated_input",
        ),
        pytest.param(
            Spec.INF_G2 + Scalar(0).x.to_bytes(30, byteorder="big"),
            id="inf_with_short_scalar",
        ),
        pytest.param(
            Spec.INF_G2 + Scalar(0).x.to_bytes(34, byteorder="big"),
            id="inf_with_long_scalar",
        ),
        pytest.param(
            Spec.INF_G2 + (b"\x01" + b"\x00" * 32),
            id="scalar_too_large_bytes",
        ),
        pytest.param(
            Spec.P2 + (b"\x01" + b"\x00" * 32),
            id="scalar_too_large_bytes_with_point",
        ),
        pytest.param(
            Spec.G2 + (b"\x01\x23\x45"),
            id="scalar_too_small_bytes",
        ),
        pytest.param(
            Scalar(1) + Scalar(1),
            id="two_scalars",
        ),
        pytest.param(
            bytes(Spec.G2) + bytes(Scalar(0))[128:],
            id="mixed_g2_scalar_truncated",
        ),
        # Not in the r-order subgroup test cases.
        pytest.param(
            Spec.P2_NOT_IN_SUBGROUP + Scalar(0),
            id="not_in_subgroup_times_0",
        ),
        pytest.param(
            Spec.P2_NOT_IN_SUBGROUP + Scalar(1),
            id="not_in_subgroup_times_1",
        ),
        pytest.param(
            Spec.P2_NOT_IN_SUBGROUP + Scalar(2),
            id="not_in_subgroup_times_2",
        ),
        pytest.param(
            Spec.P2_NOT_IN_SUBGROUP + Scalar(3),
            id="not_in_subgroup_times_3",
        ),
        pytest.param(
            Scalar(Spec.Q) + Spec.P2_NOT_IN_SUBGROUP,
            id="q_times_not_in_subgroup",
        ),
        pytest.param(
            Spec.P2_NOT_IN_SUBGROUP + Scalar(Spec.Q - 1),
            id="not_in_subgroup_times_q_minus_1",
        ),
        pytest.param(
            Spec.P2_NOT_IN_SUBGROUP + Scalar(Spec.Q + 1),
            id="not_in_subgroup_times_q_plus_1",
        ),
        # More not in the r-order subgroup test cases, but using random generated points.
        pytest.param(
            G2_POINTS_NOT_IN_SUBGROUP[0] + Scalar(1),
            id="rand_not_in_subgroup_0_times_1",
        ),
        pytest.param(
            Scalar(2) + G2_POINTS_NOT_IN_SUBGROUP[1],
            id="2_times_rand_not_in_subgroup_1",
        ),
        pytest.param(
            G2_POINTS_NOT_IN_SUBGROUP[2] + Scalar(Spec.Q),
            id="rand_not_in_subgroup_2_times_q",
        ),
        pytest.param(
            Scalar(0) + G2_POINTS_NOT_IN_SUBGROUP[3],
            id="0_times_rand_not_in_subgroup_3",
        ),
        pytest.param(
            G2_POINTS_NOT_IN_SUBGROUP[4] + Scalar(2**255 - 1),
            id="rand_not_in_subgroup_4_times_large_scalar",
        ),
        # Not on the curve cases using random generated points.
        pytest.param(
            G2_POINTS_NOT_ON_CURVE[0] + Scalar(1),
            id="rand_not_on_curve_0_times_1",
        ),
        pytest.param(
            G2_POINTS_NOT_ON_CURVE[1] + Scalar(2),
            id="rand_not_on_curve_1_times_2",
        ),
        pytest.param(
            G2_POINTS_NOT_ON_CURVE[2] + Scalar(Spec.Q),
            id="rand_not_on_curve_2_times_q",
        ),
        pytest.param(
            G2_POINTS_NOT_ON_CURVE[3] + Scalar(0),
            id="rand_not_on_curve_3_times_0",
        ),
        pytest.param(
            G2_POINTS_NOT_ON_CURVE[4] + Scalar(Spec.Q - 1),
            id="rand_not_on_curve_4_times_q_minus_1",
        ),
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
def test_invalid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Negative tests for the BLS12_G2MUL precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input_data,expected_output,precompile_gas_modifier",
    [
        pytest.param(
            Spec.INF_G2 + Scalar(0),
            Spec.INF_G2,
            1,
            id="extra_gas",
        ),
        pytest.param(
            Spec.INF_G2 + Scalar(0),
            Spec.INVALID,
            -1,
            id="insufficient_gas",
        ),
    ],
)
def test_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_G2MUL precompile gas requirements."""
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
            Spec.INF_G2 + Scalar(0),
            Spec.INF_G2,
            id="zero_times_inf",
        ),
        pytest.param(
            Spec.INF_G2 + Scalar(2),
            Spec.INF_G2,
            id="two_times_inf",
        ),
    ],
)
def test_call_types(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_G2MUL precompile using different call types."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
