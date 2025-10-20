"""Tests for BLOCKHASH opcode."""

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Storage,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op


@pytest.mark.valid_from("Frontier")
def test_genesis_hash_available(blockchain_test: BlockchainTestFiller, pre: Alloc) -> None:
    """
    Verify BLOCKHASH returns genesis and block 1 hashes.

    Regression test: Blockchain test infrastructure must populate block hashes
    before execution. Without this, BLOCKHASH returns 0, breaking dynamic
    address computations like BLOCKHASH(0) | TIMESTAMP.

    Tests both genesis (block 0) and first executed block (block 1) hash
    insertion by calling the contract in block 2.

    Bug context: revm blockchaintest runner wasn't inserting block_hashes,
    causing failures in tests with BLOCKHASH-derived addresses.
    """
    storage = Storage()

    # Store ISZERO(BLOCKHASH(0)) and ISZERO(BLOCKHASH(1))
    # Both should be 0 (false) if hashes exist
    code = Op.SSTORE(storage.store_next(0), Op.ISZERO(Op.BLOCKHASH(0))) + Op.SSTORE(
        storage.store_next(0), Op.ISZERO(Op.BLOCKHASH(1))
    )

    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    blocks = [
        Block(
            txs=[
                Transaction(
                    sender=sender,
                    to=contract,
                    gas_limit=100_000,
                    protected=False,
                )
            ]
        ),
        Block(
            txs=[
                Transaction(
                    sender=sender,
                    to=contract,
                    gas_limit=100_000,
                    protected=False,
                )
            ]
        ),
    ]

    post = {
        contract: Account(
            storage={
                0: 0,  # ISZERO(BLOCKHASH(0)) = 0 (genesis hash exists)
                1: 0,  # ISZERO(BLOCKHASH(1)) = 0 (block 1 hash exists)
            }
        )
    }

    blockchain_test(pre=pre, post=post, blocks=blocks)
