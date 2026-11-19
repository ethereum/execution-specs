"""
Reorg depth matrix: side-chain reorgs and canonical-ancestor rewinds of depth
D at client-default and tuned depth caps.

Source mapping and port limitations: ``tests/reorg/README.md``
(test_depth_matrix.py section).

Client depth knobs (as run in hive wrappers): geth ``--engine.maxreorgdepth``
(default 32, 0 = unlimited), erigon ``MAX_REORG_DEPTH`` (512), nethermind
``Reorganization.MaxDepth`` (64), besu ``--bonsai-historical-block-limit``
(512 trie logs), reth: none. ``HIVE_ENGINE_MAX_REORG_DEPTH`` reaches only
the geth and erigon wrappers.

These are capability measurements as much as conformance tests: how deep a
side chain a client can still execute is not fixed by the specification, and
a client that answers ``-38006`` beyond ``MIN_APPLIED_REORG_DEPTH`` is
behaving correctly. A depth that no client can serve is therefore reported
per client rather than treated as a single expected answer, and the
per-step ``Outcomes`` list in the consumer log is what the capability table
for EIP-8252 is derived from.
"""

from typing import List

import pytest
from execution_testing import Address, Alloc, EngineAPIError
from execution_testing.fixtures.reorg import (
    AssertCanonicalStep,
    AssertHeadStep,
    ForkchoiceUpdatedStep,
    NewPayloadStep,
    Outcome,
    Step,
)
from execution_testing.specs import ReorgBlock, ReorgTestFiller

from .helpers import MIN_APPLIED_REORG_DEPTH, chain, reorg_outcomes

REFERENCE_SPEC_GIT_PATH = "src/engine/paris.md"
REFERENCE_SPEC_VERSION = "execution-apis#786"

DISPUTED_STATE_WINDOW = (
    "execution-apis: no state retention depth is specified; go-ethereum "
    "keeps 128 state layers and cannot execute a side chain forking off "
    "below them"
)


def two_branches(
    pre: Alloc, depth: int, probe: bool = False
) -> tuple[List[ReorgBlock], List[Step]]:
    """
    Fork point a1; canonical a2..a{depth+1} (depth blocks); side chain
    s2..s{depth+2} (depth+1 blocks). Steps deliver and apply the canonical
    chain then deliver every side payload; a ``probe`` also accepts SYNCING
    for them, disputed.
    """
    sink = Address(0xC0DE)
    blocks, steps = chain(pre, "a", depth + 1, recipient=sink)
    side, side_steps = chain(
        pre,
        "s",
        depth + 1,
        parent="a1",
        start=2,
        value=2,
        recipient=sink,
        with_fcu=False,
    )
    if probe:
        side_steps = [
            NewPayloadStep(
                block=b.label,
                expect=[
                    Outcome(
                        id="valid", status="VALID", latest_valid_hash=b.label
                    ),
                    Outcome(
                        id="accepted",
                        status="ACCEPTED",
                        latest_valid_hash="null",
                    ),
                    Outcome(
                        id="syncing",
                        status="SYNCING",
                        disputed=DISPUTED_STATE_WINDOW,
                    ),
                ],
            )
            for b in side
        ]
    return blocks + side, steps + side_steps


def matrix_steps(
    depth: int, applied_only: bool, probe: bool = False
) -> List[Step]:
    """
    FCU to the side tip, then (if applied) back to the canonical tip; a
    ``probe`` also accepts SYNCING for the first, disputed.
    """
    side_tip = f"s{depth + 2}"
    canon_tip = f"a{depth + 1}"
    expect = [
        Outcome(id="applied", status="VALID", latest_valid_hash=side_tip)
    ]
    if not applied_only:
        expect.append(
            Outcome(id="refused", error_code=EngineAPIError.TooDeepReorg)
        )
    if probe:
        expect.append(
            Outcome(
                id="syncing", status="SYNCING", disputed=DISPUTED_STATE_WINDOW
            )
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
                **(
                    {"syncing": [AssertHeadStep(latest=canon_tip)]}
                    if probe
                    else {}
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
    Client defaults: a reorg within ``MIN_APPLIED_REORG_DEPTH`` must be
    applied by every client; deeper reorgs may be refused with ``-38006``
    (recorded per client) but must never corrupt the canonical mapping.
    """
    blocks, steps = two_branches(pre, depth)
    steps += matrix_steps(depth, applied_only=depth <= MIN_APPLIED_REORG_DEPTH)
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("depth", [1, 8, 31, 32, 64, 128])
def test_canonical_ancestor_reorg_depth_default(
    reorg_test: ReorgTestFiller, pre: Alloc, depth: int
) -> None:
    """
    Client defaults, rewinding instead of switching branches: FCU from
    a{depth+1} back to its canonical ancestor a1, finalizing genesis.

    A side-chain head never meets go-ethereum's depth cap, which it checks
    only when the requested head is canonical and below the current one, so
    this row is the one where geth may answer ``-38006``. Within
    ``MIN_APPLIED_REORG_DEPTH`` the rewind must be applied.
    """
    blocks, steps = chain(pre, "a", depth + 1, recipient=Address(0xC0DE))
    steps.append(
        ForkchoiceUpdatedStep(
            head="a1",
            safe="genesis",
            finalized="genesis",
            expect=reorg_outcomes("a1", depth),
            branches={
                "applied": [AssertCanonicalStep(blocks={1: "a1", 2: None})]
            },
        )
    )
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("depth", [64, 129])
def test_side_chain_reorg_depth_tuned(
    reorg_test: ReorgTestFiller, pre: Alloc, depth: int
) -> None:
    """
    Tuned: the client is started with ``HIVE_ENGINE_MAX_REORG_DEPTH`` above
    the reorg depth, so the reorg must be applied. Clients without such a
    knob run their defaults here.

    Depths above 128 are capability probes rather than conformance
    assertions: no state retention depth is specified, so a client that
    cannot execute the side chain may answer its payloads and the FCU to
    its tip with SYNCING, accepted as disputed.
    """
    probe = depth > 128
    blocks, steps = two_branches(pre, depth, probe=probe)
    steps += matrix_steps(depth, applied_only=True, probe=probe)
    reorg_test(pre=pre, blocks=blocks, steps=steps, min_reorg_depth=depth + 8)
