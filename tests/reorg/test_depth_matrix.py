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

These are capability measurements as much as conformance tests: how deep a
side chain a client can still execute is not fixed by the specification, and
a client that answers ``-38006`` is behaving correctly. A depth that no
client can serve is therefore reported per client rather than treated as a
single expected answer, and the per-step ``Outcomes`` list in the consumer
log is what the capability table for EIP-8252 is derived from.
"""

from typing import List

import pytest
from execution_testing import Address, Alloc, Transaction
from execution_testing.exceptions import EngineAPIError
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
    """FCU to the side tip, then (if applied) back to the canonical tip."""
    side_tip = f"s{depth + 2}"
    canon_tip = f"a{depth + 1}"
    expect = [
        Outcome(id="applied", status="VALID", latest_valid_hash=side_tip)
    ]
    if not applied_only:
        expect.append(
            Outcome(id="refused", error_code=EngineAPIError.TooDeepReorg)
        )
    # Only reachable once the side reorg was applied; if refused, the head
    # is already the canonical tip.
    canonical_tip_fcu = ForkchoiceUpdatedStep(
        head=canon_tip,
        safe="a1",
        finalized="a1",
        expect=[
            Outcome(id="applied", status="VALID", latest_valid_hash=canon_tip),
            *(
                []
                if applied_only
                else [
                    Outcome(
                        id="refused",
                        error_code=EngineAPIError.TooDeepReorg,
                    )
                ]
            ),
        ],
        branches={
            "applied": [
                AssertCanonicalStep(
                    blocks={2: "a2", depth + 1: canon_tip, depth + 2: None}
                )
            ],
        },
    )
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
                    ),
                    canonical_tip_fcu,
                ],
                **(
                    {}
                    if applied_only
                    else {
                        "refused": [
                            AssertCanonicalStep(
                                blocks={2: "a2", depth + 1: canon_tip}
                            )
                        ],
                    }
                ),
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
@pytest.mark.parametrize("depth", [64, 129])
def test_side_chain_reorg_depth_tuned(
    reorg_test: ReorgTestFiller, pre: Alloc, depth: int
) -> None:
    """
    Tuned: the client is started with ``HIVE_ENGINE_MAX_REORG_DEPTH`` above
    the reorg depth, so the reorg must be applied. Clients without such a
    knob run their defaults here (reth: unlimited; nethermind: 64; besu 512).

    Depths above 128 are capability probes rather than conformance
    assertions. Measured 2026-09-16 (Cancun, five clients):

    ===== ======= ======= ========== ======= =======
    depth geth    reth    nethermind besu    erigon
    ===== ======= ======= ========== ======= =======
    128   applied applied applied    applied applied
    129   SYNCING applied applied    applied applied
    256   SYNCING applied applied    applied applied
    512   SYNCING applied SYNCING    INVALID applied
    ===== ======= ======= ========== ======= =======

    Only 64 and 129 are in the corpus: 129 pins go-ethereum's ceiling, and
    256 measured the same behaviour for twice the steps. 512 costs ~1500
    steps per client and is where besu answers ``INVALID`` with ``"Unable to
    process block because parent world state ... is not available"``, i.e.
    reports missing state as block invalidity where the others report a sync
    state. Add either depth above to reproduce.

    go-ethereum's ceiling is exactly the 128 in-memory trie layers
    (`state.scheme=path`): raising the Engine API depth cap does not help,
    because ``newPayload`` for a side block whose parent state has fallen out
    of the window is answered ``ACCEPTED`` without the block being executed,
    so the next side block has an unknown parent and is answered
    ``SYNCING``. Archive mode makes no difference - the layer window, not
    history retention, is the limit.

    No client returned ``-38006`` at any depth, which is the datum EIP-8252
    needs: the specified refusal code is unused, and clients instead degrade
    into sync states (or, for besu, into ``INVALID``).
    """
    blocks, steps = two_branches(pre, depth)
    steps += matrix_steps(depth, applied_only=True)
    reorg_test(
        pre=pre,
        blocks=blocks,
        steps=steps,
        min_reorg_depth=depth + 8,
        meta={
            "class": "deep",
            "reorgDepth": depth,
            "variant": "tuned",
            # Beyond the in-memory trie window no client is required to serve
            # the reorg; the result is a capability measurement.
            **(
                {"capabilityProbe": "beyond the in-memory trie window"}
                if depth > 128
                else {}
            ),
        },
    )
