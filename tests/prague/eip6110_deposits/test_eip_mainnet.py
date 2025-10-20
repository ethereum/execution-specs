"""
abstract: Crafted tests for mainnet of [EIP-6110: Supply validator deposits on chain](https://eips.ethereum.org/EIPS/eip-6110).
"""  # noqa: E501

from typing import List

import pytest

from ethereum_test_tools import (
    Alloc,
    Block,
    BlockchainTestFiller,
)

from .helpers import DepositRequest, DepositTransaction
from .spec import ref_spec_6110

REFERENCE_SPEC_GIT_PATH = ref_spec_6110.git_path
REFERENCE_SPEC_VERSION = ref_spec_6110.version

pytestmark = [pytest.mark.valid_at("Prague"), pytest.mark.mainnet]


@pytest.mark.parametrize(
    "requests",
    [
        pytest.param(
            [
                DepositTransaction(
                    # TODO: Use a real public key to allow recovery of
                    #  the funds.
                    requests=[
                        DepositRequest(
                            pubkey=0x01,
                            withdrawal_credentials=0x02,
                            amount=1_000_000_000,
                            signature=0x03,
                            index=0x0,
                        )
                    ],
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
