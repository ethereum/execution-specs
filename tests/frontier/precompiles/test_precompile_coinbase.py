"""Test using a precompile address as the block coinbase."""

import pytest
from execution_testing import (
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Transaction,
)


@pytest.mark.valid_from("Frontier")
@pytest.mark.with_all_precompiles
def test_precompile_as_coinbase(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    precompile: int,
) -> None:
    """
    Verify that an enabled precompile as block coinbase still yields
    a valid state transition, and a later call to that precompile
    succeeds.
    """
    sender = pre.fund_eoa()
    coinbase = Address(precompile)

    blocks = [
        Block(
            fee_recipient=coinbase,
            txs=[
                Transaction(
                    sender=sender,
                    to=sender,
                    protected=fork.supports_protected_txs(),
                ),
            ],
        ),
        Block(
            fee_recipient=coinbase,
            txs=[
                Transaction(
                    sender=sender,
                    to=coinbase,
                    gas_limit=100_000,
                    protected=fork.supports_protected_txs(),
                ),
            ],
        ),
    ]
    blockchain_test(pre=pre, post={}, blocks=blocks)
