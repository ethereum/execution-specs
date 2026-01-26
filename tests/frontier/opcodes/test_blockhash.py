"""Tests for BLOCKHASH opcode."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Op,
    Transaction,
)
from execution_testing.forks.helpers import Fork


@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize(
    "setup_blocks_num,setup_blocks_empty",
    [
        pytest.param(0, True, id="no_blocks"),
        pytest.param(1, False, id="one_empty_block"),
        pytest.param(1, True, id="one_block_with_tx"),
        pytest.param(256, True, id="256_empty_blocks"),
    ],
)
@pytest.mark.slow()
def test_genesis_hash_available(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    setup_blocks_num: int,
    setup_blocks_empty: bool,
) -> None:
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
    # Store ISZERO(BLOCKHASH(0)) and ISZERO(BLOCKHASH(1))
    # Both should be 0 (false) if hashes exist
    code = Op.SSTORE(0, Op.ISZERO(Op.BLOCKHASH(0))) + Op.SSTORE(
        1, Op.ISZERO(Op.BLOCKHASH(1))
    )

    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    blocks = (
        [
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=contract,
                        gas_limit=100_000,
                        protected=fork.supports_protected_txs(),
                    )
                ]
                if not setup_blocks_empty
                else []
            )
            for _ in range(setup_blocks_num)
        ]
    ) + (
        [
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=contract,
                        gas_limit=100_000,
                        protected=fork.supports_protected_txs(),
                    )
                ]
            )
        ]
    )

    post = {
        contract: Account(
            storage={
                # ISZERO(BLOCKHASH(0)) = 0 (genesis hash exists)
                0: 1 if setup_blocks_num >= 256 else 0,
                # ISZERO(BLOCKHASH(1)) = 0 (if block 1 hash exists)
                1: 1 if setup_blocks_num == 0 else 0,
            }
        )
    }

    blockchain_test(pre=pre, post=post, blocks=blocks)
