"""
Tests that a client tracks `safe` and `finalized` as separate pointers.

Neither tag is a property of the chain. The consensus layer names both
through `engine_forkchoiceUpdated` and the execution client's only job is
to remember them, so the expectation here is a round trip rather than
something the spec derives — the only such assertion in this suite.

What makes it worth asserting is that the three tags can name three
different blocks. The recorded `rpc-compat` corpus points head, safe and
finalized at one block, so a client that ignores both fields and answers
every tag with the head passes it. This chain is generated, so `finalized`
is block 1, `safe` is block 2 and the head is block 3, and only a client
holding three distinct pointers can answer all three.
"""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Op,
    Transaction,
)

pytestmark = [pytest.mark.valid_from("Paris"), pytest.mark.rpc]


def test_forkchoice_tags_name_three_different_blocks(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    A three-block chain with a distinct block behind each tag.

    Every block logs its own number, so a client resolving a tag to the
    wrong block is caught by the log topic and the receipt as well as by
    the block hash. Answering with the head — the failure mode a
    same-block declaration cannot see — is what this is built to catch.
    """
    marker = pre.deploy_contract(Op.LOG1(0, 0, Op.NUMBER) + Op.STOP)
    sender = pre.fund_eoa()

    def marking_transaction() -> Transaction:
        """Return a transaction that records the block it lands in."""
        return Transaction(sender=sender, to=marker, gas_limit=100_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[marking_transaction()], forkchoice_tag="finalized"),
            Block(txs=[marking_transaction()], forkchoice_tag="safe"),
            Block(txs=[marking_transaction()]),
        ],
        post={},
    )
