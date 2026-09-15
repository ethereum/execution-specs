"""
Reorg depth matrix: side-chain reorgs of depth D at client-default and tuned
depth caps.

Ports of geth ``testReorgLong``/``TestLargeReorgTrieGC`` (256+ deep reorg
across the state-pruning horizon), reth ``test_long_reorg`` /
``test_reorg_through_backfill`` (e2e, depth ~100), erigon
``TestReorgsWithInsertChain`` (deep unwind), besu ``BackwardSyncContextTest``
(deep reorg via backward sync), nethermind ``Can_reorganize_to_longer_path``
scaled up, and hive ``ReOrgBackToCanonicalTest`` for side chains.

Client depth knobs (as run in hive wrappers): geth ``--engine.maxreorgdepth``
(default 32, 0 = unlimited), erigon ``MAX_REORG_DEPTH`` (512), nethermind
``Reorganization.MaxDepth`` (64), besu ``--bonsai-historical-block-limit``
(512 trie logs), reth: none. ``HIVE_ENGINE_MAX_REORG_DEPTH`` is honoured by
the geth and erigon wrappers.
"""

from typing import List

import pytest
from execution_testing import Address, Alloc, Transaction
from execution_testing.fixtures.reorg import (
    AssertCanonicalStep,
    ForkchoiceUpdatedStep,
    NewPayloadStep,
    Outcome,
    Step,
)
from execution_testing.specs import ReorgBlock, ReorgTestFiller

REFERENCE_SPEC_GIT_PATH = "src/engine/paris.md"
REFERENCE_SPEC_VERSION = "execution-apis#786"

TOO_DEEP_REORG = -38006


def two_branches(
    pre: Alloc, depth: int
) -> tuple[List[ReorgBlock], List[Step]]:
    """
    Fork point a1; canonical a2..a{depth+1} (depth blocks); side chain
    s2..s{depth+2} (depth+1 blocks). Steps deliver and apply the canonical
    chain then deliver every side payload.
    """
    ca = pre.fund_eoa()
    cs = pre.fund_eoa()
    sink = Address(0xC0DE)
    blocks = [
        ReorgBlock(
            label="a1",
            parent="genesis",
            txs=[Transaction(sender=ca, nonce=0, to=sink, value=1)],
        )
    ]
    steps: List[Step] = [
        NewPayloadStep(block="a1"),
        ForkchoiceUpdatedStep(head="a1"),
    ]
    for i in range(depth):
        label = f"a{i + 2}"
        blocks.append(
            ReorgBlock(
                label=label,
                txs=[Transaction(sender=ca, nonce=i + 1, to=sink, value=1)],
            )
        )
        steps += [
            NewPayloadStep(block=label),
            ForkchoiceUpdatedStep(head=label),
        ]
    for i in range(depth + 1):
        label = f"s{i + 2}"
        blocks.append(
            ReorgBlock(
                label=label,
                parent="a1" if i == 0 else None,
                txs=[Transaction(sender=cs, nonce=i, to=sink, value=2)],
            )
        )
        steps.append(NewPayloadStep(block=label))
    return blocks, steps


def matrix_steps(depth: int, applied_only: bool) -> List[Step]:
    """FCU to the side tip, then back to the canonical tip."""
    side_tip = f"s{depth + 2}"
    canon_tip = f"a{depth + 1}"
    expect = [
        Outcome(id="applied", status="VALID", latest_valid_hash=side_tip)
    ]
    if not applied_only:
        expect.append(Outcome(id="refused", error_code=TOO_DEEP_REORG))
    return [
        ForkchoiceUpdatedStep(
            head=side_tip,
            safe="a1",
            finalized="a1",
            expect=expect,
            branches={
                "applied": [
                    AssertCanonicalStep(
                        blocks={
                            2: "s2",
                            depth + 1: f"s{depth + 1}",
                            depth + 2: side_tip,
                        }
                    )
                ],
                "refused": [
                    AssertCanonicalStep(blocks={2: "a2", depth + 1: canon_tip})
                ],
            },
        ),
        ForkchoiceUpdatedStep(
            head=canon_tip,
            safe="a1",
            finalized="a1",
            expect=[
                Outcome(
                    id="applied", status="VALID", latest_valid_hash=canon_tip
                ),
                *(
                    []
                    if applied_only
                    else [Outcome(id="refused", error_code=TOO_DEEP_REORG)]
                ),
            ],
            branches={
                "applied": [
                    AssertCanonicalStep(
                        blocks={2: "a2", depth + 1: canon_tip, depth + 2: None}
                    )
                ],
            },
        ),
    ]


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("depth", [1, 8, 31, 32, 64, 128])
def test_side_chain_reorg_depth_default(
    reorg_test: ReorgTestFiller, pre: Alloc, depth: int
) -> None:
    """
    Client defaults: depth ≤ 8 must be applied by every client; deeper
    reorgs may be refused with ``-38006`` (recorded per client) but must
    never corrupt the canonical mapping.
    """
    blocks, steps = two_branches(pre, depth)
    steps += matrix_steps(depth, applied_only=depth <= 8)
    reorg_test(
        pre=pre,
        blocks=blocks,
        steps=steps,
        meta={"class": "deep", "reorgDepth": depth, "variant": "default"},
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("depth", [64, 256])
def test_side_chain_reorg_depth_tuned(
    reorg_test: ReorgTestFiller, pre: Alloc, depth: int
) -> None:
    """
    Tuned: the client is started with ``HIVE_ENGINE_MAX_REORG_DEPTH`` above
    the reorg depth, so the reorg must be applied. Clients without such a
    knob run their defaults here (reth: unlimited; nethermind: 64; besu 512).
    """
    blocks, steps = two_branches(pre, depth)
    steps += matrix_steps(depth, applied_only=True)
    reorg_test(
        pre=pre,
        blocks=blocks,
        steps=steps,
        requires={"HIVE_ENGINE_MAX_REORG_DEPTH": str(depth + 8)},
        meta={"class": "deep", "reorgDepth": depth, "variant": "tuned"},
    )
