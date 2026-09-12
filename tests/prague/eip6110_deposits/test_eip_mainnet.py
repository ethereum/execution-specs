"""
Crafted tests for mainnet of [EIP-6110: Supply validator deposits on chain](https://eips.ethereum.org/EIPS/eip-6110).
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    SystemContractInteractionTransaction,
)

from .helpers import recoverable_deposit_request
from .spec import ref_spec_6110

REFERENCE_SPEC_GIT_PATH = ref_spec_6110.git_path
REFERENCE_SPEC_VERSION = ref_spec_6110.version

pytestmark = [pytest.mark.valid_at("Prague"), pytest.mark.mainnet]


@pytest.mark.parametrize(
    "requests",
    [
        pytest.param(
            [
                SystemContractInteractionTransaction(
                    requests=[recoverable_deposit_request()],
                ),
            ],
            id="single_deposit_from_eoa_minimum",
        ),
    ],
)
def test_eip_6110(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    blocks: List[Block],
) -> None:
    """Test making a deposit to the beacon chain deposit contract."""
    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
    )
