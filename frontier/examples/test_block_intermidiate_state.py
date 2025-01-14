"""Test the SELFDESTRUCT opcode."""

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Transaction,
)


@pytest.mark.valid_from("Frontier")
@pytest.mark.valid_until("Homestead")
def test_block_intermidiate_state(blockchain_test: BlockchainTestFiller, pre: Alloc):
    """Verify intermidiate block states."""
    env = Environment()
    sender = pre.fund_eoa()

    tx = Transaction(gas_limit=100_000, to=None, data=b"", sender=sender)
    tx_2 = Transaction(gas_limit=100_000, to=None, data=b"", sender=sender)

    block_1 = Block(
        txs=[tx],
        expected_post_state={
            sender: Account(
                nonce=1,
            ),
        },
    )

    block_2 = Block(txs=[])

    block_3 = Block(
        txs=[tx_2],
        expected_post_state={
            sender: Account(
                nonce=2,
            ),
        },
    )

    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post=block_3.expected_post_state,
        blocks=[block_1, block_2, block_3],
    )
