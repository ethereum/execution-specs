"""
Crafted tests for mainnet of [EIP-7251: Increase the MAX_EFFECTIVE_BALANCE](https://eips.ethereum.org/EIPS/eip-7251).
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    ConsolidationRequest,
    SystemContractInteractionTransaction,
)

from .spec import ref_spec_7251

REFERENCE_SPEC_GIT_PATH = ref_spec_7251.git_path
REFERENCE_SPEC_VERSION = ref_spec_7251.version

pytestmark = [pytest.mark.valid_at("Prague"), pytest.mark.mainnet]


@pytest.mark.parametrize(
    "system_contract_interactions_per_block",
    [
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            ConsolidationRequest(
                                source_pubkey=0x01,
                                target_pubkey=0x02,
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
