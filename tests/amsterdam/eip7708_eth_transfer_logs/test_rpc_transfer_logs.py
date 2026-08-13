"""
Tests that clients report EIP-7708 transfer logs correctly over JSON-RPC.

EIP-7708 makes plain value transfers emit logs, so a receipt now carries
entries for transactions that touch no contract at all. That reaches the
`eth_` namespace directly: `logIndex` must number those entries across the
whole block, and a client that assembles receipts only from contract
events will report an incomplete list.
"""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Transaction,
)

from .spec import ref_spec_7708

REFERENCE_SPEC_GIT_PATH = ref_spec_7708.git_path
REFERENCE_SPEC_VERSION = ref_spec_7708.version

pytestmark = [pytest.mark.valid_from("EIP7708"), pytest.mark.rpc]


def test_rpc_reports_transfer_logs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Several value transfers in one block, queried over JSON-RPC.

    More than one log-emitting transaction is needed: `logIndex` is scoped
    to the block, so a per-transaction counter only diverges once a second
    transaction emits.
    """
    senders = [pre.fund_eoa() for _ in range(3)]
    recipient = pre.fund_eoa(amount=0)

    transactions = [
        Transaction(sender=sender, to=recipient, value=1) for sender in senders
    ]

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=transactions)],
        post={},
    )
