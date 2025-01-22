"""
abstract: Tests BLS12_MAP_FP_TO_G1 precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    Tests BLS12_MAP_FP_TO_G1 precompile of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537).
"""  # noqa: E501

import pytest

from ethereum_test_tools import Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools import Opcodes as Op

from .helpers import vectors_from_file
from .spec import FP, PointG1, Spec, ref_spec_2537

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = [
    pytest.mark.valid_from("Prague"),
    pytest.mark.parametrize("precompile_address", [Spec.MAP_FP_TO_G1], ids=[""]),
]

G1_POINT_ZERO_FP = PointG1(
    0x11A9A0372B8F332D5C30DE9AD14E50372A73FA4C45D5F2FA5097F2D6FB93BCAC592F2E1711AC43DB0519870C7D0EA415,  # noqa: E501
    0x92C0F994164A0719F51C24BA3788DE240FF926B55F58C445116E8BC6A47CD63392FD4E8E22BDF9FEAA96EE773222133,  # noqa: E501
)


@pytest.mark.parametrize(
    "input_data,expected_output,vector_gas_value",
    vectors_from_file("map_fp_to_G1_bls.json")
    + [
        pytest.param(
            FP(0),
            G1_POINT_ZERO_FP,
            None,
            id="fp_0",
        ),
        pytest.param(
            FP(Spec.P - 1),
            PointG1(
                0x1073311196F8EF19477219CCEE3A48035FF432295AA9419EED45D186027D88B90832E14C4F0E2AA4D15F54D1C3ED0F93,  # noqa: E501
                0x16B3A3B2E3DDDF6A11459DDAF657FDE21C4F10282A56029D9B55AB3CE1F41E1CF39AD27E0EA35823C7D3250E81FF3D66,  # noqa: E501
            ),
            None,
            id="fp_p_minus_1",
        ),
    ],
)
def test_valid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_MAP_FP_TO_G1 precompile."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(
    "input_data",
    vectors_from_file("fail-map_fp_to_G1_bls.json")
    + [
        pytest.param(b"\x80" + bytes(FP(0))[1:], id="invalid_encoding"),
        pytest.param(bytes(FP(0))[1:], id="input_too_short"),
        pytest.param(b"\x00" + FP(0), id="input_too_long"),
        pytest.param(b"", id="zero_length_input"),
        pytest.param(FP(Spec.P), id="fq_eq_q"),
        pytest.param(FP(2**512 - 1), id="fq_eq_2_512_minus_1"),
        pytest.param(Spec.G1, id="g1_point_input"),
    ],
)
@pytest.mark.parametrize("expected_output", [Spec.INVALID], ids=[""])
def test_invalid(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Negative tests for the BLS12_MAP_FP_TO_G1 precompile."""
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
            FP(0),
            G1_POINT_ZERO_FP,
            1,
            id="extra_gas",
        ),
        pytest.param(
            FP(0),
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
    """Test the BLS12_MAP_FP_TO_G1 precompile gas requirements."""
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
            FP(0),
            G1_POINT_ZERO_FP,
            id="fp_0",
        ),
    ],
)
def test_call_types(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
):
    """Test the BLS12_MAP_FP_TO_G1 precompile using different call types."""
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
