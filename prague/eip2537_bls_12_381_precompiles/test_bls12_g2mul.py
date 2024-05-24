"""
abstract: Tests BLS12_G2MUL precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    Tests BLS12_G2MUL precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537).
"""  # noqa: E501

import pytest

from ethereum_test_tools import Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, Transaction

from .helpers import vectors_from_file
from .spec import PointG2, Scalar, Spec, ref_spec_2537

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = [
    pytest.mark.valid_from("Prague"),
    pytest.mark.parametrize("precompile_address", [Spec.G2MUL], ids=[""]),
]


@pytest.mark.parametrize(
    "input,expected_output",
    vectors_from_file("mul_G2_bls.json")
    + [
        pytest.param(
            Spec.INF_G2 + Scalar(0),
            Spec.INF_G2,
            id="bls_g2mul_(0*inf=inf)",
        ),
        pytest.param(
            Spec.INF_G2 + Scalar(2**256 - 1),
            Spec.INF_G2,
            id="bls_g2mul_(2**256-1*inf=inf)",
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
            id="bls_g2mul_(2**256-1*P2)",
        ),
        pytest.param(
            Spec.P2 + Scalar(Spec.Q - 1),
            -Spec.P2,  # negated P2
            id="bls_g2mul_(q-1*P2)",
        ),
        pytest.param(
            Spec.P2 + Scalar(Spec.Q),
            Spec.INF_G2,
            id="bls_g2mul_(q*P2)",
        ),
        pytest.param(
            Spec.G2 + Scalar(Spec.Q),
            Spec.INF_G2,
            id="bls_g2mul_(q*G2)",
        ),
        pytest.param(
            Spec.P2 + Scalar(Spec.Q + 1),
            Spec.P2,
            id="bls_g2mul_(q+1*P2)",
        ),
        pytest.param(
            Spec.P2 + Scalar(2 * Spec.Q),
            Spec.INF_G2,
            id="bls_g2mul_(2q*P2)",
        ),
        pytest.param(
            Spec.P2 + Scalar((2**256 // Spec.Q) * Spec.Q),
            Spec.INF_G2,
            id="bls_g2mul_(Nq*P2)",
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
    Test the BLS12_G2MUL precompile.
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input",
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
            Spec.P2_NOT_IN_SUBGROUP + Scalar(1),
            id="bls_g2mul_not_in_subgroup",
        ),
        pytest.param(
            Spec.P2_NOT_IN_SUBGROUP + Scalar(2),
            id="bls_g2mul_not_in_subgroup_times_2",
        ),
        pytest.param(
            Spec.P2_NOT_IN_SUBGROUP + Scalar(Spec.Q),
            id="bls_g2mul_not_in_subgroup_times_q",
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
            Spec.G2,
            id="bls_g2_truncated_input",
        ),
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
    Negative tests for the BLS12_G2MUL precompile.
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input,expected_output,precompile_gas_modifier",
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
    pre: dict,
    post: dict,
    tx: Transaction,
):
    """
    Test the BLS12_G1MUL precompile gas requirements.
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
            Spec.INF_G2 + Scalar(0),
            Spec.INF_G2,
            id="bls_g2mul_(0*inf=inf)",
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
    Test the BLS12_G2MUL using different call types.
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
