"""
abstract: Tests BLS12 precompiles of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    Tests BLS12 precompiles of [EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537)
    before the Prague hard fork is active
"""  # noqa: E501

import pytest

from ethereum_test_tools import Environment, StateTestFiller, Transaction

from .spec import FP, FP2, Scalar, Spec, ref_spec_2537

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = pytest.mark.valid_at_transition_to("Prague")


@pytest.mark.parametrize(
    "precompile_address,input",
    [
        pytest.param(
            Spec.G1ADD,
            Spec.INF_G1 + Spec.INF_G1,
            id="G1ADD",
        ),
        pytest.param(
            Spec.G1MSM,
            Spec.INF_G1 + Scalar(0),
            id="G1MSM",
        ),
        pytest.param(
            Spec.G1MUL,
            Spec.INF_G1 + Scalar(0),
            id="G1MUL",
        ),
        pytest.param(
            Spec.G2ADD,
            Spec.INF_G2 + Spec.INF_G2,
            id="G2ADD",
        ),
        pytest.param(
            Spec.G2MSM,
            Spec.INF_G2 + Scalar(0),
            id="G2MSM",
        ),
        pytest.param(
            Spec.G2MUL,
            Spec.INF_G2 + Scalar(0),
            id="G2MUL",
        ),
        pytest.param(
            Spec.PAIRING,
            Spec.INF_G1 + Spec.INF_G2,
            id="PAIRING",
        ),
        pytest.param(
            Spec.MAP_FP_TO_G1,
            FP(0),
            id="MAP_FP_TO_G1",
        ),
        pytest.param(
            Spec.MAP_FP2_TO_G2,
            FP2((0, 0)),
            id="MAP_FP2_TO_G2",
        ),
    ],
)
@pytest.mark.parametrize("expected_output,call_succeeds", [pytest.param(b"", True, id="")])
def test_precompile_before_fork(
    state_test: StateTestFiller,
    pre: dict,
    post: dict,
    tx: Transaction,
):
    """
    Test all BLS12 precompiles before the Prague hard fork is active.

    The call must succeed but the output must be empty.
    """
    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
