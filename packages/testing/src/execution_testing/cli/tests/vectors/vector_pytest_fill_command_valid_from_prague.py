"""Vector file for valid_from-based pre-alloc group coverage."""

from typing import Any

import pytest

from execution_testing import Account, Block, TestAddress, Transaction

TEST_ADDRESS = Account(balance=1_000_000)


@pytest.mark.valid_from("Prague")
def test_chain_id_pre_alloc(blockchain_test: Any) -> None:
    """Generate a blockchain test selected by the valid_from marker."""
    blockchain_test(
        pre={TestAddress: TEST_ADDRESS},
        post={},
        blocks=[Block(txs=[Transaction()])],
    )
