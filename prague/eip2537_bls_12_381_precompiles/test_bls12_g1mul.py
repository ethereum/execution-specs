"""
abstract: Tests BLS12_G1MUL precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    Tests BLS12_G1MUL precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537).
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
    vectors_from_file("mul_G1_bls.json")
    + [
        pytest.param(
            Spec.INF_G1 + Scalar(0),
            Spec.INF_G1,
            id="bls_g1mul_(0*inf=inf)",
        ),
        pytest.param(
            Spec.INF_G1 + Scalar(2**256 - 1),
            Spec.INF_G1,
            id="bls_g1mul_(2**256-1*inf=inf)",
        ),
        pytest.param(
            Spec.P1 + Scalar(2**256 - 1),
            PointG1(
                0x3DA1F13DDEF2B8B5A46CD543CE56C0A90B8B3B0D6D43DEC95836A5FD2BACD6AA8F692601F870CF22E05DDA5E83F460B,  # noqa: E501
                0x18D64F3C0E9785365CBDB375795454A8A4FA26F30B9C4F6E33CA078EB5C29B7AEA478B076C619BC1ED22B14C95569B2D,  # noqa: E501
            ),
            id="bls_g1mul_(2**256-1*P1)",
        ),
        pytest.param(
            Spec.P1 + Scalar(Spec.Q - 1),
            -Spec.P1,  # negated P1
            id="bls_g1mul_(q-1*P1)",
        ),
        pytest.param(
            Spec.P1 + Scalar(Spec.Q),
            Spec.INF_G1,
            id="bls_g1mul_(q*P1)",
        ),
        pytest.param(
            Spec.P1 + Scalar(Spec.Q + 1),
            Spec.P1,
            id="bls_g1mul_(q+1*P1)",
        ),
        pytest.param(
            Spec.P1 + Scalar(2 * Spec.Q),
            Spec.INF_G1,
            id="bls_g1mul_(2q*P1)",
        ),
        pytest.param(
            Spec.P1 + Scalar((2**256 // Spec.Q) * Spec.Q),
            Spec.INF_G1,
            id="bls_g1mul_(Nq*P1)",
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
            Spec.P1_NOT_IN_SUBGROUP + Scalar(1),
            id="bls_g1mul_not_in_subgroup_1",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP_TIMES_2 + Scalar(1),
            id="bls_g1mul_not_in_subgroup_2",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP_TIMES_2 + Scalar(Spec.Q),
            id="bls_g1mul_not_in_subgroup_times_q",
        ),
        pytest.param(
            Spec.P1_NOT_IN_SUBGROUP + Scalar(Spec.Q),
            id="bls_g1mul_not_in_subgroup_times_q_2",
        ),
        pytest.param(
            Spec.G1 + Spec.G1,
            id="bls_g1_add_input_invalid_length",
        ),
        pytest.param(
            Spec.G2 + Spec.G2,
            id="bls_g2_add_input_invalid_length",
        ),
        pytest.param(
            Spec.G1,
            id="bls_g1_truncated_input",
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
            id="bls_g1mul_(0*inf=inf)",
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
