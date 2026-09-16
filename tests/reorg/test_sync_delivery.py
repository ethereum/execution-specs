"""
Chains delivered to a client by syncing from a peer rather than by
``engine_newPayload``.

Post-merge clients do not gossip blocks, so a client that is told a head it
has never been sent can only reach it by syncing the chain from a peer over
devp2p. That is the delivery path hive's ``ReOrgViaSync`` variants exercise
and the one no single-client fixture can express.
"""

from typing import List

import pytest
from execution_testing import Address, Alloc, Transaction
from execution_testing.fixtures.reorg import (
    AssertHeadStep,
    FixtureClient,
    ForkchoiceUpdatedStep,
    NewPayloadStep,
    Outcome,
    Step,
    WaitForHeadStep,
)
from execution_testing.specs import ReorgBlock, ReorgTestFiller

PEER = "peer"
CANON = 5


@pytest.mark.valid_from("Cancun")
def test_head_synced_from_peer(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    A head that was never delivered to the client must be reached by syncing.

    The peer receives the whole chain through the Engine API; the main client
    receives nothing and is then given that head. It has to answer ``SYNCING``
    (it cannot validate a payload it does not have) and then converge on the
    head by pulling the chain from its peer.
    """
    sender = pre.fund_eoa()
    sink = Address(0xC0DE)
    blocks = [
        ReorgBlock(
            label=f"a{i}",
            parent="genesis" if i == 1 else None,
            txs=[Transaction(sender=sender, nonce=i - 1, to=sink, value=1)],
        )
        for i in range(1, CANON + 1)
    ]
    steps: List[Step] = []
    # The peer gets the whole chain; main gets nothing.
    for i in range(1, CANON + 1):
        steps += [
            NewPayloadStep(block=f"a{i}", on=PEER),
            ForkchoiceUpdatedStep(head=f"a{i}", on=PEER),
        ]
    steps += [
        AssertHeadStep(latest=f"a{CANON}", on=PEER),
        AssertHeadStep(latest="genesis"),
        # Main has no payloads, so it must start syncing from the peer.
        ForkchoiceUpdatedStep(
            head=f"a{CANON}",
            expect=[
                Outcome(id="syncing", status="SYNCING"),
                Outcome(
                    id="applied", status="VALID", latest_valid_hash=f"a{CANON}"
                ),
            ],
            branches={"syncing": [WaitForHeadStep(latest=f"a{CANON}")]},
        ),
        AssertHeadStep(latest=f"a{CANON}"),
    ]
    reorg_test(
        pre=pre,
        blocks=blocks,
        steps=steps,
        clients={
            PEER: FixtureClient(description="serves the chain over devp2p")
        },
        meta={"class": "shallow", "delivery": "sync"},
    )
