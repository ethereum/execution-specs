"""
abstract: Tests BLS12_PAIRING precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    Tests BLS12_PAIRING precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537).
"""  # noqa: E501

import pytest

from ethereum_test_tools import Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools import Opcodes as Op

from .conftest import (
    G1_POINTS_NOT_IN_SUBGROUP,
    G1_POINTS_NOT_ON_CURVE,
    G2_POINTS_NOT_IN_SUBGROUP,
    G2_POINTS_NOT_ON_CURVE,
)
from .helpers import vectors_from_file
from .spec import PointG1, PointG2, Spec, ref_spec_2537

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = [
    pytest.mark.valid_from("Prague"),
    pytest.mark.parametrize("precompile_address", [Spec.PAIRING], ids=[""]),
]


@pytest.mark.parametrize(
    "input_data,expected_output,vector_gas_value",
    # Test vectors from the reference spec (from the cryptography team)
    vectors_from_file("pairing_check_bls.json")
    + [
        pytest.param(
            Spec.G1 + Spec.INF_G2,
            Spec.PAIRING_TRUE,
            None,
            id="generator_with_inf_g2",
        ),
        pytest.param(
            Spec.INF_G1 + Spec.G2,
            Spec.PAIRING_TRUE,
            None,
            id="inf_g1_with_generator",
        ),
        pytest.param(  # e(inf, inf) == 1
            Spec.INF_G1 + Spec.INF_G2,
            Spec.PAIRING_TRUE,
            None,
            id="inf_pair",
        ),
        pytest.param(  # 1000 copies of e(inf, inf) == 1
            (Spec.INF_G1 + Spec.INF_G2) * 1000,
            Spec.PAIRING_TRUE,
            None,
            id="multi_inf_pair",
        ),
        pytest.param(  # e(P, Q) . e(P, −Q) == 1 (inverse pair, factors cancel)
            Spec.G1 + Spec.G2 + Spec.G1 + (-Spec.G2),
            Spec.PAIRING_TRUE,
            None,
            id="g1_g2_and_inverse",
        ),
        pytest.param(  # e(P,Q) · e(P,−Q) · e(−P,Q) · e(−P,−Q) == 1 (full sign cancellation)
            Spec.G1
            + Spec.G2
            + Spec.G1
            + (-Spec.G2)
            + (-Spec.G1)
            + Spec.G2
            + (-Spec.G1)
            + (-Spec.G2),
            Spec.PAIRING_TRUE,
            None,
            id="full_sign_cancellation",
        ),
        pytest.param(  # 127 × e(inf, inf) . e(P, Q) + e(P, −Q) == 1
            (Spec.INF_G1 + Spec.INF_G2) * 127 + Spec.G1 + Spec.G2 + Spec.G1 + (-Spec.G2),
            Spec.PAIRING_TRUE,
            None,
            id="large_input_with_cancellation",
        ),
        pytest.param(  # e(P, Q) . e(−P, −Q) =  e(P, Q)^2
            Spec.G1 + Spec.G2 + (-Spec.G1) + (-Spec.G2),
            Spec.PAIRING_FALSE,
            None,
            id="negated_both_pairs",
        ),
        pytest.param(  # e(inf, inf) . e(P, −Q)
            (Spec.INF_G1 + Spec.INF_G2) + (Spec.G1 + (-Spec.G2)),
            Spec.PAIRING_FALSE,
            None,
            id="multi_inf_g1_neg_g2",
        ),
        pytest.param(
            (Spec.G1 + (-Spec.G2)) + (Spec.INF_G1 + Spec.INF_G2),
            Spec.PAIRING_FALSE,
            None,
            id="g1_neg_g2_multi_inf",
        ),
        pytest.param(
            Spec.G1 + Spec.G2,
            Spec.PAIRING_FALSE,
            None,
            id="single_generator_pair",
        ),
        pytest.param(
            (Spec.INF_G1 + Spec.INF_G2) + (Spec.G1 + Spec.G2),
            Spec.PAIRING_FALSE,
            None,
            id="inf_plus_generator_pair",
        ),
        pytest.param(  # e(P, Q) . e(P, −Q) . e(−P, Q)
            Spec.G1 + Spec.G2 + Spec.G1 + (-Spec.G2) + (-Spec.G1) + Spec.G2,
            Spec.PAIRING_FALSE,
            None,
            id="partial_sign_cancellation",
        ),
    ],
)
def test_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_PAIRING precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input_data",
    # Test vectors from the reference spec (from the cryptography team)
    vectors_from_file("fail-pairing_check_bls.json")
    + [
        # Coordinate equal to p (modulus) in G1
        pytest.param(
            PointG1(Spec.P, 0) + Spec.INF_G2,
            id="g1_p_g2_inf_1",
        ),
        pytest.param(
            PointG1(0, Spec.P) + Spec.INF_G2,
            id="g1_p_g2_inf_2",
        ),
        # Coordinate equal to p (modulus) in G2
        pytest.param(
            Spec.INF_G1 + PointG2((Spec.P, 0), (0, 0)),
            id="g1_inf_g2_p_1",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2((0, Spec.P), (0, 0)),
            id="g1_inf_g2_p_2",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2((0, 0), (Spec.P, 0)),
            id="g1_inf_g2_p_3",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2((0, 0), (0, Spec.P)),
            id="g1_inf_g2_p_4",
        ),
        pytest.param(
            b"\x80" + bytes(Spec.INF_G1)[1:] + Spec.INF_G2,
            id="invalid_encoding_g1",
        ),
        pytest.param(
            Spec.INF_G1 + b"\x80" + bytes(Spec.INF_G2)[1:],
            id="invalid_encoding_g2",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Spec.INF_G2,
            id="p1_not_in_subgroup",
        ),
        pytest.param(
            Spec.INF_G1 + Spec.P2_NOT_IN_SUBGROUP,
            id="p2_not_in_subgroup",
        ),
        pytest.param(
            (Spec.INF_G1 + Spec.INF_G2) * 1000 + PointG1(Spec.P, 0) + Spec.INF_G2,
            id="long_input_with_invalid_tail",
        ),
        # Points not in the subgroup or not on the curve randomly generated.
        pytest.param(
            G1_POINTS_NOT_ON_CURVE[0] + Spec.INF_G2,
            id="rand_not_on_curve_g1_0_plus_inf",
        ),
        pytest.param(
            G1_POINTS_NOT_ON_CURVE[1] + Spec.G2,
            id="rand_not_on_curve_g1_1_plus_g2",
        ),
        pytest.param(
            G1_POINTS_NOT_IN_SUBGROUP[0] + Spec.G2,
            id="rand_not_in_subgroup_g1_0_plus_g2",
        ),
        pytest.param(
            G1_POINTS_NOT_IN_SUBGROUP[1] + Spec.INF_G2,
            id="rand_not_in_subgroup_g1_1_plus_inf",
        ),
        pytest.param(
            Spec.INF_G1 + G2_POINTS_NOT_ON_CURVE[0],
            id="inf_plus_rand_not_on_curve_g2_0",
        ),
        pytest.param(
            Spec.G1 + G2_POINTS_NOT_ON_CURVE[1],
            id="g1_plus_rand_not_on_curve_g2_1",
        ),
        pytest.param(
            Spec.INF_G1 + G2_POINTS_NOT_IN_SUBGROUP[0],
            id="inf_plus_rand_not_in_subgroup_g2_0",
        ),
        pytest.param(
            Spec.G1 + G2_POINTS_NOT_IN_SUBGROUP[1],
            id="g1_plus_rand_not_in_subgroup_g2_1",
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
    """Negative tests for the BLS12_PAIRING precompile."""
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
            Spec.INF_G1 + Spec.INF_G2,
            Spec.PAIRING_TRUE,
            1,
            id="extra_gas",
        ),
        pytest.param(
            Spec.INF_G1 + Spec.INF_G2,
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
    """Test the BLS12_PAIRING precompile gas requirements."""
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
            Spec.INF_G1 + Spec.INF_G2,
            Spec.PAIRING_TRUE,
            id="inf_pair",
        ),
    ],
)
def test_call_types(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_PAIRING precompile using different call types."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
