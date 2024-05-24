"""
abstract: Tests BLS12_PAIRING precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    Tests BLS12_PAIRING precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537).
"""  # noqa: E501

import pytest

from ethereum_test_tools import Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, Transaction

from .helpers import vectors_from_file
from .spec import PointG1, PointG2, Spec, ref_spec_2537

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = [
    pytest.mark.valid_from("Prague"),
    pytest.mark.parametrize("precompile_address", [Spec.PAIRING], ids=[""]),
]


@pytest.mark.parametrize(
    "input,expected_output",
    vectors_from_file("pairing_check_bls.json")
    + [
        pytest.param(
            Spec.INF_G1 + Spec.INF_G2,
            Spec.PAIRING_TRUE,
            id="inf_pair",
        ),
        pytest.param(
            (Spec.INF_G1 + Spec.INF_G2) * 1000,
            Spec.PAIRING_TRUE,
            id="multi_inf_pair",
        ),
    ],
)
def test_valid(
    state_test: StateTestFiller,
    pre: dict,
    post: dict,
    tx: Transaction,
):
    """
    Test the BLS12_PAIRING precompile.
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input",
    vectors_from_file("fail-pairing_check_bls.json")
    + [
        pytest.param(
            PointG1(Spec.P, 0) + Spec.INF_G2,
            id="g1_P_g2_inf_1",
        ),
        pytest.param(
            PointG1(0, Spec.P) + Spec.INF_G2,
            id="g1_P_g2_inf_2",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2((Spec.P, 0), (0, 0)),
            id="g1_inf_g2_P_1",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2((0, Spec.P), (0, 0)),
            id="g1_inf_g2_P_2",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2((0, 0), (Spec.P, 0)),
            id="g1_inf_g2_P_3",
        ),
        pytest.param(
            Spec.INF_G1 + PointG2((0, 0), (0, Spec.P)),
            id="g1_inf_g2_P_4",
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
            (Spec.INF_G1 + Spec.INF_G2) * 1000 + PointG1(Spec.P, 0) + Spec.INF_G2,
            id="multi_inf_plus_g1_P_g2_inf_1",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Spec.INF_G2,
            id="P1_not_in_subgroup",
        ),
        pytest.param(
            Spec.INF_G1 + Spec.P2_NOT_IN_SUBGROUP,
            id="P2_not_in_subgroup",
        ),
        # Input length tests can be found in ./test_bls12_variable_length_input_contracts.py
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
def test_invalid(
    state_test: StateTestFiller,
    pre: dict,
    post: dict,
    tx: Transaction,
):
    """
    Negative tests for the BLS12_PAIRING precompile.
    """
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
    "input,expected_output",
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
    pre: dict,
    post: dict,
    tx: Transaction,
):
    """
    Test the BLS12_PAIRING precompile using different call types.
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
