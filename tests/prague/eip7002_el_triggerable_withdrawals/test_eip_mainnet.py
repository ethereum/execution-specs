"""
abstract: Crafted tests for mainnet of [EIP-7002: Execution layer triggerable withdrawals](https://eips.ethereum.org/EIPS/eip-7002).
"""  # noqa: E501

from typing import List

import pytest
from ethereum_test_tools import (
    Alloc,
    Block,
    BlockchainTestFiller,
)

from .helpers import WithdrawalRequest, WithdrawalRequestTransaction
from .spec import Spec, ref_spec_7002

REFERENCE_SPEC_GIT_PATH = ref_spec_7002.git_path
REFERENCE_SPEC_VERSION = ref_spec_7002.version

pytestmark = [pytest.mark.valid_at("Prague"), pytest.mark.mainnet]


@pytest.mark.parametrize(
    "blocks_withdrawal_requests",
    [
        pytest.param(
            [
                [
                    WithdrawalRequestTransaction(
                        requests=[
                            WithdrawalRequest(
                                validator_pubkey=0x01,
                                amount=0,
                                fee=Spec.get_fee(0),
                            )
                        ],
                    ),
                ],
            ],
            id="single_withdrawal_request",
        ),
    ],
)
def test_eip_7002(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
) -> None:
    """Test making a withdrawal request."""
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
    )
