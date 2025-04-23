"""
abstract: Tests BLS12_G1MUL precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    Tests BLS12_G1MUL precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537).
"""  # noqa: E501

import pytest

from ethereum_test_tools import Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools import Opcodes as Op

from .conftest import G1_POINTS_NOT_IN_SUBGROUP, G1_POINTS_NOT_ON_CURVE
from .helpers import vectors_from_file
from .spec import PointG1, Scalar, Spec, ref_spec_2537

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = [
    pytest.mark.valid_from("Prague"),
    pytest.mark.parametrize("precompile_address", [Spec.G1MSM], ids=[""]),
]


@pytest.mark.parametrize(
    "input_data,expected_output,vector_gas_value",
    # Test vectors from the reference spec (from the cryptography team)
    vectors_from_file("mul_G1_bls.json")
    + [
        # Basic multiplication test cases.
        pytest.param(
            Spec.INF_G1 + Scalar(0),
            Spec.INF_G1,
            None,
            id="zero_times_inf",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(1),
            Spec.INF_G1,
            None,
            id="one_times_inf",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(2),
            Spec.INF_G1,
            None,
            id="two_times_inf",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(Spec.Q),
            Spec.INF_G1,
            None,
            id="q_times_inf",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(2**256 - 1),
            Spec.INF_G1,
            None,
            id="max_scalar_times_inf",
        ),
        pytest.param(
            Spec.G1 + Scalar(0),
            Spec.INF_G1,
            None,
            id="zero_times_generator",
        ),
        pytest.param(
            Spec.P1 + Scalar(0),
            Spec.INF_G1,
            None,
            id="zero_times_point",
        ),
        pytest.param(
            Spec.G1 + Scalar(1),
            Spec.G1,
            None,
            id="one_times_generator",
        ),
        pytest.param(
            Spec.P1 + Scalar(1),
            Spec.P1,
            None,
            id="one_times_point",
        ),
        pytest.param(
            Spec.P1 + Scalar(2**256 - 1),
            PointG1(
                0x3DA1F13DDEF2B8B5A46CD543CE56C0A90B8B3B0D6D43DEC95836A5FD2BACD6AA8F692601F870CF22E05DDA5E83F460B,  # noqa: E501
                0x18D64F3C0E9785365CBDB375795454A8A4FA26F30B9C4F6E33CA078EB5C29B7AEA478B076C619BC1ED22B14C95569B2D,  # noqa: E501
            ),
            None,
            id="max_scalar_times_point",
        ),
        # Subgroup related test cases.
        pytest.param(
            Spec.P1 + Scalar(Spec.Q - 1),
            -Spec.P1,  # negated P1
            None,
            id="q_minus_1_times_point",
        ),
        pytest.param(
            Spec.P1 + Scalar(Spec.Q),
            Spec.INF_G1,
            None,
            id="q_times_point",
        ),
        pytest.param(
            Spec.G1 + Scalar(Spec.Q),
            Spec.INF_G1,
            None,
            id="q_times_generator",
        ),
        pytest.param(
            Spec.P1 + Scalar(Spec.Q + 1),
            Spec.P1,
            None,
            id="q_plus_1_times_point",
        ),
        pytest.param(
            Spec.P1 + Scalar(2 * Spec.Q),
            Spec.INF_G1,
            None,
            id="2q_times_point",
        ),
        pytest.param(
            Spec.P1 + Scalar((2**256 // Spec.Q) * Spec.Q),
            Spec.INF_G1,
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
    """Test the BLS12_G1MUL precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input_data",
    # Test vectors from the reference spec (from the cryptography team)
    vectors_from_file("fail-mul_G1_bls.json")
    + [
        pytest.param(
            PointG1(0, 1) + Scalar(0),
            id="invalid_point_1",
        ),
        pytest.param(
            PointG1(Spec.P1.x, Spec.P1.y - 1) + Scalar(0),
            id="invalid_point_2",
        ),
        pytest.param(
            PointG1(Spec.P1.x, Spec.P1.y + 1) + Scalar(0),
            id="invalid_point_3",
        ),
        pytest.param(
            PointG1(Spec.P1.x, Spec.P1.x) + Scalar(0),
            id="invalid_point_4",
        ),
        pytest.param(
            PointG1(Spec.P, 0) + Scalar(0),
            id="x_equal_to_p_times_0",
        ),
        pytest.param(
            PointG1(0, Spec.P) + Scalar(0),
            id="y_equal_to_p_times_0",
        ),
        pytest.param(
            PointG1(Spec.P + 1, 0) + Scalar(0),
            id="x_above_modulus_times_0",
        ),
        pytest.param(
            PointG1(Spec.P1.y, Spec.P1.x) + Scalar(0),
            id="swapped_coordinates_times_0",
        ),
        pytest.param(
            PointG1(0x01, 0x07) + Scalar(0),  # Point on wrong curve y^2 = x^3 + 5
            id="point_on_wrong_curve_times_0",
        ),
        pytest.param(
            b"\x80" + bytes(Spec.INF_G1)[1:] + Scalar(0),
            id="invalid_encoding",
        ),
        pytest.param(
            (Spec.INF_G1 + Scalar(0))[:-1],
            id="input_too_short",
        ),
        pytest.param(
            b"\x00" + (Spec.INF_G1 + Scalar(0)),
            id="input_too_long",
        ),
        pytest.param(
            b"",
            id="zero_length_input",
        ),
        pytest.param(
            b"\x00" * 96,
            id="all_zero_96_bytes",
        ),
        pytest.param(
            b"\xff" + b"\x00" * 47 + b"\xff" + b"\x00" * 31,
            id="bad_inf_flag_with_scalar",
        ),
        pytest.param(
            b"\xc0" + b"\x00" * 47 + b"\x00" * 32,
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
            Spec.G1,
            id="g1_truncated_input",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(0).x.to_bytes(30, byteorder="big"),
            id="inf_with_short_scalar",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(0).x.to_bytes(34, byteorder="big"),
            id="inf_with_long_scalar",
        ),
        pytest.param(
            Spec.INF_G1 + (b"\x01" + b"\x00" * 32),
            id="scalar_too_large_bytes",
        ),
        pytest.param(
            Spec.P1 + (b"\x01" + b"\x00" * 32),
            id="scalar_too_large_bytes_with_point",
        ),
        pytest.param(
            Spec.G1 + (b"\x01\x23\x45"),
            id="scalar_too_small_bytes",
        ),
        pytest.param(
            Scalar(1) + Scalar(1),
            id="two_scalars",
        ),
        # Not in the r-order subgroup test cases.
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Scalar(1),
            id="not_in_subgroup_times_1",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Scalar(2),
            id="not_in_subgroup_times_2",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Scalar(3),
            id="not_in_subgroup_times_3",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Scalar(0),
            id="not_in_subgroup_times_0",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP_TIMES_2 + Scalar(1),
            id="doubled_not_in_subgroup_times_1",
        ),
        pytest.param(
            Scalar(Spec.Q) + Spec.P1_NOT_IN_SUBGROUP,
            id="q_times_not_in_subgroup",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Scalar(Spec.Q - 1),
            id="not_in_subgroup_times_q_minus_1",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP_TIMES_2 + Scalar(Spec.Q),
            id="doubled_not_in_subgroup_times_q",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Scalar(Spec.Q + 1),
            id="not_in_subgroup_times_q_plus_1",
        ),
        # More not in the r-order subgroup test cases, but using random generated points.
        pytest.param(
            G1_POINTS_NOT_IN_SUBGROUP[0] + Scalar(1),
            id="rand_not_in_subgroup_0_times_1",
        ),
        pytest.param(
            Scalar(2) + G1_POINTS_NOT_IN_SUBGROUP[1],
            id="2_times_rand_not_in_subgroup_1",
        ),
        pytest.param(
            G1_POINTS_NOT_IN_SUBGROUP[2] + Scalar(Spec.Q),
            id="rand_not_in_subgroup_2_times_q",
        ),
        pytest.param(
            Scalar(0) + G1_POINTS_NOT_IN_SUBGROUP[3],
            id="0_times_rand_not_in_subgroup_3",
        ),
        pytest.param(
            G1_POINTS_NOT_IN_SUBGROUP[4] + Scalar(2**255 - 1),
            id="rand_not_in_subgroup_4_times_large_scalar",
        ),
        # Not on the curve cases using random generated points.
        pytest.param(
            G1_POINTS_NOT_ON_CURVE[0] + Scalar(1),
            id="rand_not_on_curve_0_times_1",
        ),
        pytest.param(
            G1_POINTS_NOT_ON_CURVE[1] + Scalar(2),
            id="rand_not_on_curve_1_times_2",
        ),
        pytest.param(
            G1_POINTS_NOT_ON_CURVE[2] + Scalar(Spec.Q),
            id="rand_not_on_curve_2_times_q",
        ),
        pytest.param(
            G1_POINTS_NOT_ON_CURVE[3] + Scalar(0),
            id="rand_not_on_curve_3_times_0",
        ),
        pytest.param(
            G1_POINTS_NOT_ON_CURVE[4] + Scalar(Spec.Q - 1),
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
    """Negative tests for the BLS12_G1MUL precompile."""
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
            Spec.INF_G1 + Scalar(0),
            Spec.INF_G1,
            1,
            id="extra_gas",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(0),
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
    """Test the BLS12_G1MUL precompile gas requirements."""
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
            id="zero_times_inf",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(2),
            Spec.INF_G1,
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
    """Test the BLS12_G1MUL precompile using different call types."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
