"""
abstract: Crafted tests for mainnet of
[EIP-2537: Precompile for BLS12-381 curve operations](https://eips.ethereum.org/EIPS/eip-2537).
"""  # noqa: E501

import pytest

from ethereum_test_tools import Alloc, StateTestFiller, Transaction

from .spec import FP, FP2, Scalar, Spec, ref_spec_2537

REFERENCE_SPEC_GIT_PATH = ref_spec_2537.git_path
REFERENCE_SPEC_VERSION = ref_spec_2537.version

pytestmark = [pytest.mark.valid_at("Prague"), pytest.mark.mainnet]


@pytest.mark.parametrize(
    "precompile_address,input_data,expected_output,vector_gas_value",
    [
        pytest.param(
            Spec.G1ADD,
            Spec.G1 + Spec.INF_G1,
            Spec.G1,
            None,
            id="G1ADD",
        ),
        pytest.param(
            Spec.G1MSM,
            Spec.G1 + Scalar(1) + Spec.INF_G1 + Scalar(1),
            Spec.G1,
            None,
            id="G1MSM",
        ),
        pytest.param(
            Spec.G2ADD,
            Spec.G2 + Spec.INF_G2,
            Spec.G2,
            None,
            id="G2ADD",
        ),
        pytest.param(
            Spec.G2MSM,
            Spec.G2 + Scalar(1) + Spec.INF_G2 + Scalar(1),
            Spec.G2,
            None,
            id="G2MSM",
        ),
        pytest.param(
            Spec.PAIRING,
            Spec.G1 + Spec.INF_G2,
            Spec.PAIRING_TRUE,
            None,
            id="PAIRING",
        ),
        pytest.param(
            Spec.MAP_FP_TO_G1,
            FP(
                799950832265136997107648781861994410980648980263584507133499364313075404851459407870655748616451882783569609925573  # noqa: E501
            ),
            Spec.INF_G1,
            None,
            id="fp_map_to_inf",
        ),
        pytest.param(
            Spec.MAP_FP2_TO_G2,
            FP2(
                (
                    3510328712861478240121438855244276237335901234329585006107499559909114695366216070652508985150831181717984778988906,  # noqa: E501
                    2924545590598115509050131525615277284817672420174395176262156166974132393611647670391999011900253695923948997972401,  # noqa: E501
                )
            ),
            Spec.INF_G2,
            None,
            id="fp_map_to_inf",
        ),
    ],
)
def test_eip_2537(
    state_test: StateTestFiller,
    pre: Alloc,
    post: dict,
    tx: Transaction,
) -> None:
    """Test the all precompiles of EIP-2537."""
    state_test(
        pre=pre,
        tx=tx,
        post=post,
    )
