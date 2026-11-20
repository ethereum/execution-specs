"""
Heads the client reaches by syncing blocks from a peer.

Source mapping and port limitations: ``tests/reorg/README.md``
(test_peer_sync_reorg.py section).
"""

from typing import List

import pytest
from execution_testing import Alloc
from execution_testing.fixtures.reorg import (
    AccountExpectation,
    AssertCanonicalStep,
    AssertHeadStep,
    AssertStateStep,
    AwaitHeadStep,
    ForkchoiceUpdatedStep,
    NewPayloadStep,
    ServePeerStep,
    Step,
)
from execution_testing.specs import ReorgTestFiller

from .helpers import chain, reorg_outcomes

REFERENCE_SPEC_GIT_PATH = "src/engine/paris.md"
REFERENCE_SPEC_VERSION = "execution-apis#786"


@pytest.mark.valid_from("Shanghai")
def test_sync_head_from_peer(reorg_test: ReorgTestFiller, pre: Alloc) -> None:
    """
    Reach a head whose ancestors only the peer has.

    Only a5 is sent, and it is SYNCING; the peer then serves a1..a5, and the
    client syncs a1..a4 and makes a5 its head.
    """
    recipient = pre.fund_eoa(amount=0)
    blocks, _ = chain(pre, "a", 5, recipient=recipient)
    steps: List[Step] = [
        NewPayloadStep(block="a5"),
        ForkchoiceUpdatedStep(head="a5"),
        AssertHeadStep(latest="genesis"),
        ServePeerStep(head="a5"),
        AwaitHeadStep(latest="a5"),
        AssertCanonicalStep(blocks={i: f"a{i}" for i in range(1, 6)}),
        AssertStateStep(
            at="latest", accounts={recipient: AccountExpectation(balance=5)}
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_reorg_to_branch_from_peer(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Reorg from a delivered branch to one only the peer has.

    b4 on a1..a2 is the head and a5 is SYNCING; the peer then serves
    a1..a5, and the client syncs a3..a4, reorgs to a5 and returns to b4.
    """
    a_recipient = pre.fund_eoa(amount=0)
    b_recipient = pre.fund_eoa(amount=0)
    blocks, steps = chain(pre, "a", 2)
    a_branch, _ = chain(
        pre, "a", 3, parent="a2", start=3, recipient=a_recipient
    )
    b_branch, b_steps = chain(
        pre, "b", 2, parent="a2", start=3, recipient=b_recipient
    )
    blocks += a_branch + b_branch
    steps += b_steps
    steps += [
        NewPayloadStep(block="a5"),
        ForkchoiceUpdatedStep(head="a5"),
        ServePeerStep(head="a5"),
        AwaitHeadStep(latest="a5"),
        AssertCanonicalStep(blocks={3: "a3", 4: "a4", 5: "a5"}),
        AssertStateStep(
            at="latest",
            accounts={
                a_recipient: AccountExpectation(balance=3),
                b_recipient: AccountExpectation(balance=0),
            },
        ),
        ForkchoiceUpdatedStep(
            head="b4",
            expect=reorg_outcomes("b4", depth=3),
            branches={
                "applied": [
                    AssertCanonicalStep(blocks={3: "b3", 4: "b4", 5: None})
                ]
            },
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)
