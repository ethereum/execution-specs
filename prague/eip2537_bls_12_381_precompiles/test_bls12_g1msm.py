"""
abstract: Tests BLS12_G1MSM precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    Tests BLS12_G1MSM precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537).
"""  # noqa: E501

import pytest

from ethereum_test_tools import Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools import Opcodes as Op

from .helpers import vectors_from_file
from .spec import PointG1, Scalar, Spec, ref_spec_2537

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = [
    pytest.mark.valid_from("Prague"),
    pytest.mark.parametrize("precompile_address", [Spec.G1MSM], ids=[""]),
]


@pytest.mark.parametrize(
    "input_data,expected_output",
    vectors_from_file("multiexp_G1_bls.json")
    + [
        pytest.param(
            (Spec.P1 + Scalar(Spec.Q)) * (len(Spec.G1MSM_DISCOUNT_TABLE) - 1),
            Spec.INF_G1,
            id="max_discount",
        ),
        pytest.param(
            (Spec.P1 + Scalar(Spec.Q)) * len(Spec.G1MSM_DISCOUNT_TABLE),
            Spec.INF_G1,
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
    """Test the BLS12_G1MSM precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input_data",
    vectors_from_file("fail-multiexp_G1_bls.json")
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
            b"\x80" + bytes(Spec.INF_G1)[1:] + Scalar(0),
            id="invalid_encoding",
        ),
        pytest.param(
            b"\x80" + bytes(Spec.INF_G1)[1:] + Scalar(0),
            id="invalid_encoding",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Scalar(Spec.Q),
            id="not_in_subgroup_1",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP_TIMES_2 + Scalar(Spec.Q),
            id="not_in_subgroup_2",
        ),
        pytest.param(
            Spec.G1,
            id="bls_g1_truncated_input",
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
    """Test the BLS12_G1MSM precompile."""
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
            Spec.INF_G1 + Scalar(0),
            Spec.INF_G1,
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
    """Test the BLS12_G1MSM precompile using different call types."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
