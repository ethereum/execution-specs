"""
abstract: Crafted tests for mainnet of [EIP-7251: Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251).
"""  # noqa: E501

from typing import List

import pytest
from ethereum_test_tools import (
    Alloc,
    Block,
    BlockchainTestFiller,
)

from .helpers import ConsolidationRequest, ConsolidationRequestTransaction
from .spec import Spec, ref_spec_7251

REFERENCE_SPEC_GIT_PATH = ref_spec_7251.git_path
REFERENCE_SPEC_VERSION = ref_spec_7251.version

pytestmark = [pytest.mark.valid_at("Prague"), pytest.mark.mainnet]


@pytest.mark.parametrize(
    "blocks_consolidation_requests",
    [
        pytest.param(
            [
                [
                    ConsolidationRequestTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
                                fee=Spec.get_fee(0),
                            )
                        ],
                    ),
                ],
            ],
            id="single_consolidation_request",
        ),
    ],
)
def test_eip_7251(
    blockchain_test: BlockchainTestFiller,
    blocks: List[Block],
    pre: Alloc,
) -> None:
    """Test making a consolidation request."""
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
    )
