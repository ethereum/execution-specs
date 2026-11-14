"""
Reorg depth matrix: side-chain reorgs and canonical-ancestor rewinds of depth
D at client-default and tuned depth caps.

Source mapping and port limitations: ``tests/reorg/README.md``
(test_depth_matrix.py section).

Client depth knobs (as run in hive wrappers): geth ``--engine.maxreorgdepth``
(default 32, 0 = unlimited), erigon ``MAX_REORG_DEPTH`` (512), nethermind
``Reorganization.MaxDepth`` (64), besu ``--bonsai-historical-block-limit``
(512 trie logs), reth: none. ``HIVE_ENGINE_MAX_REORG_DEPTH`` reaches only
the geth and erigon wrappers, and only with ethereum/hive#1608.

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

    reth's Ethereum engine answers such a rewind VALID and keeps its head
    (``apply_chain_update``), which #786 does not allow, so it is expected
    to fail here:
    https://github.com/paradigmxyz/reth/blob/7c1ffbe6619ef07a53256489c5f5fd89a602202d/crates/engine/tree/src/tree/mod.rs#L1299-L1352
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
    knob run their defaults here (reth: unlimited; nethermind: 64; besu 512).

    Depths above 128 are capability probes rather than conformance
    assertions: no state retention depth is specified, so a client that
    cannot execute the side chain may answer its payloads and the FCU to
    its tip with SYNCING, accepted as disputed. Measured 2026-11-12 (Cancun,
    client defaults; go-ethereum v1.17.11, reth 2.11.0, nethermind 2.3.0,
    besu 26.11, erigon 3.9.0):

    ===== ======= ======= ========== ======= =======
    depth geth    reth    nethermind besu    erigon
    ===== ======= ======= ========== ======= =======
    128   applied applied applied    applied applied
    129   SYNCING applied applied    applied applied
    256   SYNCING applied SYNCING    applied applied
    512   SYNCING applied SYNCING    SYNCING applied
    ===== ======= ======= ========== ======= =======

    Only 64 and 129 are in the corpus: 129 pins go-ethereum's ceiling.
    nethermind's ceiling lies between 129 and 256 and besu's between 256
    and 512; 512 costs ~1500 steps per client. Add either depth above to
    reproduce. On 2026-09-16 nethermind still applied 256, and besu answered
    512 with ``INVALID``, reporting missing parent state as block invalidity
    (besu-eth/besu#11314, fixed since).

    go-ethereum's ceiling is exactly the 128 in-memory trie layers
    (`state.scheme=path`): raising the Engine API depth cap does not help,
    because ``newPayload`` for a side block whose parent state has fallen out
    of the window is answered ``ACCEPTED`` without the block being executed,
    so the next side block has an unknown parent and is answered
    ``SYNCING``. Archive mode makes no difference - the layer window, not
    history retention, is the limit.

    No client returned ``-38006`` here: on side chains clients degrade into
    sync states. go-ethereum checks its depth cap only for canonical-ancestor
    rewinds, which ``test_canonical_ancestor_reorg_depth_default`` covers.
    """
    probe = depth > 128
    blocks, steps = two_branches(pre, depth, probe=probe)
    steps += matrix_steps(depth, applied_only=True, probe=probe)
    reorg_test(pre=pre, blocks=blocks, steps=steps, min_reorg_depth=depth + 8)
