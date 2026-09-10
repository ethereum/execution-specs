"""
Crafted tests for mainnet of [EIP-8282: Builder Execution Requests](https://eips.ethereum.org/EIPS/eip-8282).
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    BuilderDepositRequest,
    BuilderExitRequest,
    SystemContractInteractionTransaction,
)

from .spec import ref_spec_8282

REFERENCE_SPEC_GIT_PATH = ref_spec_8282.git_path
REFERENCE_SPEC_VERSION = ref_spec_8282.version

pytestmark = [pytest.mark.valid_at("Amsterdam"), pytest.mark.mainnet]

MIN_DEPOSIT_GWEI = BuilderDepositRequest.min_deposit_wei // 10**9


@pytest.mark.parametrize(
    "system_contract_interactions_per_block",
    [
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            )
                        ],
                    ),
                ],
            ],
            id="single_builder_deposit_request",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[BuilderExitRequest(pubkey=0x01)],
                    ),
                ],
            ],
            id="single_builder_exit_request",
        ),
        pytest.param(
            [
                [
                    SystemContractInteractionTransaction(
                        requests=[
                            BuilderDepositRequest(
                                pubkey=0x01,
                                withdrawal_credentials=0x02,
                                amount=MIN_DEPOSIT_GWEI,
                                signature=0x03,
                            ),
                            BuilderExitRequest(pubkey=0x04),
                        ],
                    ),
                ],
            ],
            id="single_builder_deposit_and_exit_request",
        ),
    ],
)
def test_eip_8282(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
) -> None:
    """Test making builder deposit and exit requests."""
    blockchain_test(pre=pre, post={}, blocks=blocks)
