"""
Reorgs across a fork boundary (Shanghai -> Cancun at timestamp 15000).

Ports of hive ``WithdrawalsReorgSpec`` (``suites/withdrawals/tests.go``:
"Withdrawals Fork on Block N - M Block Re-Org" via NewPayload), hive
``suites/cancun`` fork-transition payload-version tests, geth
``TestSetCanonical``-style fork-crossing reorgs, besu
``MergeCoordinatorTest`` post-fork payload handling, nethermind
``forkchoiceUpdatedV2/V3`` version tests (wrong version -> -38005).

Genesis is Shanghai; blocks after timestamp 15000 are Cancun and use
``engine_newPayloadV3``; pre-fork blocks use V2. A reorg may move the head
from a Cancun block to a Shanghai block and back.
"""

from typing import List

import pytest
from execution_testing import Address, Alloc, Transaction
from execution_testing.fixtures.reorg import (
    AssertCanonicalStep,
    AssertHeadStep,
    ForkchoiceUpdatedStep,
    NewPayloadStep,
    Outcome,
    Step,
)
from execution_testing.specs import ReorgBlock, ReorgTestFiller

REFERENCE_SPEC_GIT_PATH = "src/engine/cancun.md"
REFERENCE_SPEC_VERSION = "execution-apis#786"

FORK_TS = 15_000


def applied(head: str) -> List[Outcome]:
    """Single legal outcome."""
    return [Outcome(id="applied", status="VALID", latest_valid_hash=head)]


@pytest.mark.valid_at_transition_to("Cancun")
def test_reorg_across_fork_boundary(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Canonical: a1..a3 Shanghai, a4 first Cancun block (ts 15000), a5 Cancun.
    Side chain off a3: s4 Shanghai (ts 14988), s5 Cancun (ts 15000).
    Head moves a5 -> s4 (back before the fork) -> s5 -> a5. Every FCU is
    VALID and the canonical mapping follows.
    """
    ca = pre.fund_eoa()
    cs = pre.fund_eoa()
    sink = Address(0xC0DE)
    blocks = [
        ReorgBlock(
            label="a1",
            parent="genesis",
            txs=[Transaction(sender=ca, nonce=0, to=sink, value=1)],
        ),
        ReorgBlock(
            label="a2", txs=[Transaction(sender=ca, nonce=1, to=sink, value=1)]
        ),
        ReorgBlock(
            label="a3", txs=[Transaction(sender=ca, nonce=2, to=sink, value=1)]
        ),
        ReorgBlock(
            label="a4",
            timestamp=FORK_TS,
            txs=[Transaction(sender=ca, nonce=3, to=sink, value=1)],
        ),
        ReorgBlock(
            label="a5", txs=[Transaction(sender=ca, nonce=4, to=sink, value=1)]
        ),
        ReorgBlock(
            label="s4",
            parent="a3",
            timestamp=FORK_TS - 12,
            txs=[Transaction(sender=cs, nonce=0, to=sink, value=2)],
        ),
        ReorgBlock(
            label="s5",
            timestamp=FORK_TS,
            txs=[Transaction(sender=cs, nonce=1, to=sink, value=2)],
        ),
    ]
    steps: List[Step] = []
    for label in ("a1", "a2", "a3", "a4", "a5"):
        steps += [
            NewPayloadStep(block=label),
            ForkchoiceUpdatedStep(head=label),
        ]
    steps += [
        NewPayloadStep(block="s4"),
        NewPayloadStep(block="s5"),
        ForkchoiceUpdatedStep(
            head="s4",
            expect=applied("s4"),
            branches={
                "applied": [AssertCanonicalStep(blocks={4: "s4", 5: None})]
            },
        ),
        ForkchoiceUpdatedStep(
            head="s5",
            expect=applied("s5"),
            branches={
                "applied": [AssertCanonicalStep(blocks={4: "s4", 5: "s5"})]
            },
        ),
        ForkchoiceUpdatedStep(
            head="a5",
            expect=applied("a5"),
            branches={
                "applied": [
                    AssertCanonicalStep(blocks={3: "a3", 4: "a4", 5: "a5"})
                ]
            },
        ),
        AssertHeadStep(latest="a5"),
    ]
    reorg_test(
        pre=pre,
        blocks=blocks,
        steps=steps,
        meta={"class": "shallow", "forkBoundary": True},
    )


@pytest.mark.valid_at_transition_to("Cancun")
def test_sibling_first_fork_blocks(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Two competing *first* Cancun blocks on the last Shanghai block (hive
    ``WithdrawalsReorgSpec`` "Fork on Block 8 - 10 Block Re-Org" reduced):
    both VALID, head switches between them, then a child of the loser
    extends and takes the head.
    """
    ca = pre.fund_eoa()
    cs = pre.fund_eoa()
    sink = Address(0xC0DE)
    blocks = [
        ReorgBlock(
            label="a1",
            parent="genesis",
            txs=[Transaction(sender=ca, nonce=0, to=sink, value=1)],
        ),
        ReorgBlock(
            label="a2",
            timestamp=FORK_TS,
            txs=[Transaction(sender=ca, nonce=1, to=sink, value=1)],
        ),
        ReorgBlock(
            label="b2",
            parent="a1",
            timestamp=FORK_TS + 12,
            txs=[Transaction(sender=cs, nonce=0, to=sink, value=2)],
        ),
        ReorgBlock(
            label="b3", txs=[Transaction(sender=cs, nonce=1, to=sink, value=2)]
        ),
    ]
    steps: List[Step] = [
        NewPayloadStep(block="a1"),
        ForkchoiceUpdatedStep(head="a1"),
        NewPayloadStep(
            block="a2",
            expect=[
                Outcome(id="valid", status="VALID", latest_valid_hash="a2")
            ],
        ),
        NewPayloadStep(
            block="b2",
            expect=[
                Outcome(id="valid", status="VALID", latest_valid_hash="b2")
            ],
        ),
        ForkchoiceUpdatedStep(head="a2", expect=applied("a2")),
        ForkchoiceUpdatedStep(
            head="b2",
            expect=applied("b2"),
            branches={"applied": [AssertCanonicalStep(blocks={2: "b2"})]},
        ),
        ForkchoiceUpdatedStep(head="a2", expect=applied("a2")),
        NewPayloadStep(block="b3"),
        ForkchoiceUpdatedStep(
            head="b3",
            expect=applied("b3"),
            branches={
                "applied": [AssertCanonicalStep(blocks={2: "b2", 3: "b3"})]
            },
        ),
    ]
    reorg_test(
        pre=pre,
        blocks=blocks,
        steps=steps,
        meta={"class": "shallow", "forkBoundary": True},
    )
