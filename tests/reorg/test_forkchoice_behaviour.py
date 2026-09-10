"""
Forkchoice behaviour across reorganizations (post-merge: the head follows
``forkchoiceUpdated`` regardless of chain length).

Ports of:
- geth ``testShorterFork/testLongerFork/testEqualFork`` (AfterMerge),
  ``testReorgLong/Short``, ``testBlockchainHeaderchainReorgConsistency``,
  ``testSideLogRebirth`` (side chain with lower difficulty still wins).
- besu ``DefaultBlockchainTest.appendBlockWithReorgTo{ChainAtEqualHeight,
  ShorterChain,LongerChain}``, ``appendBlockForFork``,
  ``MergeCoordinatorTest.forkchoiceUpdateShouldIgnoreAncestorOfChainHead``,
  ``AbstractEngineForkchoiceUpdatedTest`` (invalid forkchoice state
  variants, ignore update to old head),
  ``updateForkChoiceShouldPersistFirstFinalizedBlockHash``.
- nethermind ``Can_reorganize_to_{shorter,longer,same}_path``,
  ``Can_reorganize_there_and_back``,
  ``forkchoiceUpdatedV1_can_reorganize_to_last_block``,
  ``forkchoiceUpdatedV1_head_block_after_reorg``,
  ``block_should_not_be_canonical_before_forkchoiceUpdatedV1``,
  ``block_should_not_be_canonical_after_reorg``,
  ``forkChoiceUpdatedV1_to_unknown_block_fails``,
  ``forkChoiceUpdatedV1_to_unknown_safeBlock_hash_should_fail``,
  ``forkchoiceUpdatedV1_should_update_{finalized,safe}_block_hash``,
  ``forkchoiceUpdatedV1_should_work_with_zero_keccak_as_safe_block``,
  ``forkchoiceUpdatedV1_should_change_head_when_all_parameters_are_the_newHeadHash``,
  ``payloadV1_invalid_parent_hash``,
  ``inconsistent_{finalized,safe}_hash``.
- erigon
  ``TestValidateChainAndUpdateForkChoiceWithSideForksThatGoBackAndForwardInHeight``,
  ``TestReorgsWithInsertChain``,
  ``TestFcuAllowsReorgBackOnCanonicalChainWhenAfterFinalisedHash``.
- reth ``test_tree_state_on_new_head_deep_fork``,
  ``test_engine_tree_fcu_reorg_with_all_blocks``,
  ``test_engine_tree_valid_forks_with_older_canonical_head`` (+invalid
  variant), ``test_engine_tree_fcu_extends_canon_chain``,
  ``test_engine_tree_buffered_blocks_are_eventually_connected``,
  ``test_reorg_to_fork_behind_finalized``,
  ``test_testsuite_{create_fork,reorg_with_tagging,deep_reorg}``,
  ``test_handle_canonical_head``,
  ``test_on_forkchoice_updated_integration``.
- hive ``ReOrgBackToCanonicalTest``, ``ReOrgBackFromSyncingTest``,
  ``SafeReOrgToSideChainTest``, ``BlockStatus``,
  ``InconsistentForkchoiceTest``,
  ``ForkchoiceUpdatedUnknownBlockHashTest``,
  ``NewPayloadWithMissingFcUTest``, ``ReExecutePayloadTest``,
  ``MultiplePayloadsExtendingCanonicalChainTest``,
  ``NewPayloadOnSyncingClientTest``.
"""

from typing import List, Tuple

import pytest
from execution_testing import Alloc, BlockException, Hash, Header, Transaction
from execution_testing.fixtures.reorg import (
    AssertCanonicalStep,
    AssertHeadStep,
    ForkchoiceUpdatedStep,
    NewPayloadStep,
    Outcome,
    Step,
)
from execution_testing.specs import ReorgBlock, ReorgTestFiller

REFERENCE_SPEC_GIT_PATH = "src/engine/paris.md"
REFERENCE_SPEC_VERSION = "execution-apis#786"

INVALID_FORKCHOICE_STATE = -38002
TOO_DEEP_REORG = -38006

DISPUTED_FORK_BEHIND_FINALIZED = (
    "execution-apis paris.md step 5 requires -38002 when finalized is not on "
    "head's chain; reth trusts the CL and applies the update (VALID)"
)
DISPUTED_ZERO_SAFE = (
    "paris.md allows a zero finalizedBlockHash before finality but does "
    "not say whether a zero safeBlockHash with a non-zero finalized is "
    "legal; besu rejects it with -38002, nethermind/geth/reth accept it"
)
DISPUTED_PRE_786_NOOP = (
    "paris.md before execution-apis#786: client MAY skip the update when head "
    "is an ancestor of the canonical head"
)


def rewind_outcomes(head: str) -> List[Outcome]:
    """FCU to a canonical ancestor: applied, skipped (pre-#786) or too deep."""
    return [
        Outcome(id="applied", status="VALID", latest_valid_hash=head),
        Outcome(
            id="noop",
            status="VALID",
            latest_valid_hash=head,
            disputed=DISPUTED_PRE_786_NOOP,
        ),
        Outcome(id="refused", error_code=TOO_DEEP_REORG),
    ]


def applied(head: str) -> List[Outcome]:
    """Single legal outcome: applied."""
    return [Outcome(id="applied", status="VALID", latest_valid_hash=head)]


def chain(
    pre: Alloc,
    prefix: str,
    length: int,
    parent: str = "genesis",
    start: int = 1,
    value: int = 1,
) -> Tuple[List[ReorgBlock], List[Step]]:
    """
    ``length`` blocks ``{prefix}{start}..`` on ``parent``, each with one value
    transfer from a fresh sender (nonces independent per chain), plus the
    NP/FCU steps that make the last one the head.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    blocks: List[ReorgBlock] = []
    steps: List[Step] = []
    for i in range(length):
        label = f"{prefix}{start + i}"
        blocks.append(
            ReorgBlock(
                label=label,
                parent=parent if i == 0 else None,
                txs=[
                    Transaction(
                        sender=sender, nonce=i, to=recipient, value=value
                    )
                ],
            )
        )
        steps += [
            NewPayloadStep(block=label),
            ForkchoiceUpdatedStep(head=label),
        ]
    return blocks, steps


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "canonical_len,fork_point,fork_len",
    [
        pytest.param(4, 1, 1, id="shorter"),
        pytest.param(3, 1, 2, id="equal"),
        pytest.param(3, 1, 4, id="longer"),
        pytest.param(4, 3, 2, id="near_tip_longer"),
        pytest.param(4, 0, 2, id="from_genesis_shorter"),
    ],
)
def test_head_follows_fcu_regardless_of_length(
    reorg_test: ReorgTestFiller,
    pre: Alloc,
    canonical_len: int,
    fork_point: int,
    fork_len: int,
) -> None:
    """
    Post-merge fork choice: the head is whatever FCU names, whether the fork
    is shorter, equal or longer than the canonical chain. Heights beyond the
    new head must no longer be canonical.
    """
    a_blocks, steps = chain(pre, "a", canonical_len)
    parent = "genesis" if fork_point == 0 else f"a{fork_point}"
    b_blocks, b_steps = chain(
        pre, "b", fork_len, parent=parent, start=fork_point + 1
    )
    blocks = a_blocks + b_blocks
    fork_tip = f"b{fork_point + fork_len}"
    canonical_after = {
        i: f"b{i}" for i in range(fork_point + 1, fork_point + fork_len + 1)
    }
    canonical_after.update({i: f"a{i}" for i in range(1, fork_point + 1)})
    for i in range(fork_point + fork_len + 1, canonical_len + 1):
        canonical_after[i] = None  # type: ignore[assignment]
    steps += [NewPayloadStep(block=b.label) for b in b_blocks]
    steps.append(
        ForkchoiceUpdatedStep(
            head=fork_tip,
            expect=applied(fork_tip),
            branches={
                "applied": [AssertCanonicalStep(blocks=canonical_after)]
            },
        )
    )
    # And back to the original tip.
    a_tip = f"a{canonical_len}"
    steps.append(
        ForkchoiceUpdatedStep(
            head=a_tip,
            expect=applied(a_tip),
            branches={
                "applied": [
                    AssertCanonicalStep(
                        blocks={
                            i: f"a{i}" for i in range(1, canonical_len + 1)
                        }
                    )
                ]
            },
        )
    )
    _ = b_steps
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_reorg_back_and_forth_between_branches(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Reth ``test_tree_state_on_new_head_deep_fork`` / nethermind
    ``Can_reorganize_there_and_back`` / erigon ``TestReorgsWithInsertChain``:
    two 6-block branches off a 3-block base; the head ping-pongs between
    branch B's blocks and branch A's tip.
    """
    base, steps = chain(pre, "a", 3)
    a_ext, _ = chain(pre, "a", 6, parent="a3", start=4)
    b_ext, _ = chain(pre, "b", 6, parent="a3", start=4, value=2)
    blocks = base + a_ext + b_ext
    steps += [NewPayloadStep(block=b.label) for b in a_ext + b_ext]
    steps.append(
        ForkchoiceUpdatedStep(
            head="a9",
            expect=applied("a9"),
            branches={
                "applied": [AssertCanonicalStep(blocks={9: "a9", 4: "a4"})]
            },
        )
    )
    for i in range(4, 10):
        steps.append(
            ForkchoiceUpdatedStep(
                head=f"b{i}",
                expect=applied(f"b{i}"),
                branches={
                    "applied": [
                        AssertCanonicalStep(
                            blocks={
                                i: f"b{i}",
                                3: "a3",
                                **({i + 1: None} if i < 9 else {}),
                            }
                        )
                    ]
                },
            )
        )
        steps.append(
            ForkchoiceUpdatedStep(
                head="a9",
                expect=applied("a9"),
                branches={
                    "applied": [
                        AssertCanonicalStep(blocks={9: "a9", i: f"a{i}"})
                    ]
                },
            )
        )
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_reorg_to_older_canonical_ancestor_and_forward(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Hive ``ReOrgBackToCanonicalTest`` (depth 1..5) / erigon
    ``TestFcuAllowsReorgBackOnCanonicalChainWhenAfterFinalisedHash`` / reth
    ``test_fcu_with_canonical_ancestor_updates_latest_block``: after every
    new block, FCU back to a5 (a canonical ancestor above finalized) then
    forward to the tip. #786: the rewind is applied or refused (-38006); the
    forward FCU must always be VALID.
    """
    blocks, steps = chain(pre, "a", 5)
    more, _ = chain(pre, "a", 5, parent="a5", start=6)
    blocks += more
    steps.append(
        ForkchoiceUpdatedStep(
            head="a5", safe="a5", finalized="a1", expect=applied("a5")
        )
    )
    for i in range(6, 11):
        tip = f"a{i}"
        steps += [
            NewPayloadStep(block=tip),
            ForkchoiceUpdatedStep(
                head=tip, safe="a5", finalized="a1", expect=applied(tip)
            ),
            ForkchoiceUpdatedStep(
                head="a5",
                safe="a5",
                finalized="a1",
                expect=rewind_outcomes("a5"),
                branches={
                    "applied": [
                        AssertCanonicalStep(blocks={5: "a5", 6: None})
                    ],
                    "noop": [AssertCanonicalStep(blocks={5: "a5", i: tip})],
                    "refused": [AssertCanonicalStep(blocks={5: "a5", i: tip})],
                },
            ),
            ForkchoiceUpdatedStep(
                head=tip, safe="a5", finalized="a1", expect=applied(tip)
            ),
        ]
    steps.append(
        AssertCanonicalStep(blocks={i: f"a{i}" for i in range(1, 11)})
    )
    reorg_test(
        pre=pre,
        blocks=blocks,
        steps=steps,
        meta={"class": "shallow", "reorgDepth": 5},
    )


@pytest.mark.valid_from("Cancun")
def test_fcu_to_unknown_block_is_syncing(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Hive ``ReOrgBackFromSyncingTest`` +
    ``ForkchoiceUpdatedUnknownBlockHashTest``,
    nethermind ``forkChoiceUpdatedV1_to_unknown_block_fails`` /
    ``forkChoiceUpdatedV1_to_unknown_safeBlock_hash_should_fail``, reth
    ``test_engine_tree_fcu_missing_head``.

    A 10-deep side chain exists but only its leaf is ever delivered: the leaf
    is SYNCING/ACCEPTED, FCU to it is SYNCING, FCU with an unknown safe or
    finalized hash is an error, and FCU back to the canonical tip is VALID.
    """
    blocks, steps = chain(pre, "a", 5)
    side, _ = chain(pre, "s", 10, parent="a5", start=6, value=3)
    blocks += side
    steps += [
        NewPayloadStep(
            block="s15",
            expect=[
                Outcome(id="syncing", status="SYNCING"),
                Outcome(
                    id="accepted", status="ACCEPTED", latest_valid_hash="null"
                ),
            ],
        ),
        ForkchoiceUpdatedStep(
            head="s15",
            expect=[
                Outcome(
                    id="syncing", status="SYNCING", latest_valid_hash="null"
                )
            ],
        ),
        AssertHeadStep(latest="a5"),
        ForkchoiceUpdatedStep(
            head="a5",
            safe="s15",
            expect=[
                Outcome(
                    id="inconsistent", error_code=INVALID_FORKCHOICE_STATE
                ),
                Outcome(id="error", any_error=True),
            ],
        ),
        ForkchoiceUpdatedStep(
            head="a5",
            finalized="s15",
            expect=[
                Outcome(
                    id="inconsistent", error_code=INVALID_FORKCHOICE_STATE
                ),
                Outcome(id="error", any_error=True),
            ],
        ),
        ForkchoiceUpdatedStep(head="a5", expect=applied("a5")),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("field", ["head", "safe", "finalized"])
def test_inconsistent_forkchoice_state(
    reorg_test: ReorgTestFiller, pre: Alloc, field: str
) -> None:
    """
    Hive ``InconsistentForkchoiceTest``,
    nethermind ``inconsistent_finalized_hash`` /
    ``inconsistent_safe_hash``, besu invalid-forkchoice-state variants: with
    canonical a1..a3 and a validated sibling chain b1..b3, an FCU whose
    ``field`` points into the other chain is ``-38002``; the canonical FCU
    afterwards is VALID.
    """
    blocks, steps = chain(pre, "a", 3)
    side, _ = chain(pre, "b", 3, value=2)
    blocks += side
    steps += [NewPayloadStep(block=b.label) for b in side]
    state = {"head": "a3", "safe": "a2", "finalized": "a1"}
    state[field] = {"head": "b3", "safe": "b2", "finalized": "b1"}[field]
    steps += [
        ForkchoiceUpdatedStep(
            head=state["head"],
            safe=state["safe"],
            finalized=state["finalized"],
            expect=[
                Outcome(id="inconsistent", error_code=INVALID_FORKCHOICE_STATE)
            ],
        ),
        ForkchoiceUpdatedStep(
            head="a3", safe="a2", finalized="a1", expect=applied("a3")
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_safe_finalized_labels_follow_fcu(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Hive ``BlockStatus`` + ``SafeReOrgToSideChainTest``, nethermind safe/
    finalized/zero-keccak tests, besu
    ``updateForkChoiceShouldPersistFirstFinalizedBlockHash``:
    ``latest``/``safe``/``finalized`` track every FCU, including a reorg of
    head and safe onto a side chain while finalized stays pinned, zero safe
    hash, and all three equal.
    """
    blocks, steps = chain(pre, "a", 3)
    side, _ = chain(pre, "b", 2, parent="a1", start=2, value=2)
    blocks += side
    steps = steps[:-1] + [
        ForkchoiceUpdatedStep(
            head="a3", safe="a2", finalized="a1", expect=applied("a3")
        ),
        NewPayloadStep(block="b2"),
        NewPayloadStep(block="b3"),
        ForkchoiceUpdatedStep(
            head="b3", safe="b2", finalized="a1", expect=applied("b3")
        ),
        ForkchoiceUpdatedStep(
            head="b3",
            safe="zero",
            finalized="a1",
            expect=[
                *applied("b3"),
                Outcome(
                    id="rejected",
                    error_code=INVALID_FORKCHOICE_STATE,
                    disputed=DISPUTED_ZERO_SAFE,
                ),
            ],
        ),
        ForkchoiceUpdatedStep(
            head="b3", safe="b3", finalized="b3", expect=applied("b3")
        ),
        ForkchoiceUpdatedStep(
            head="a3", safe="a3", finalized="a3", expect=applied("a3")
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_newpayload_does_not_move_head(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Hive ``NewPayloadWithMissingFcUTest``, nethermind
    ``block_should_not_be_canonical_before_forkchoiceUpdatedV1``, reth
    ``test_testsuite_create_fork``: payloads alone never change ``latest``
    or the canonical mapping; a single FCU to the tip does.
    """
    blocks, _ = chain(pre, "a", 5)
    steps: List[Step] = [NewPayloadStep(block=f"a{i}") for i in range(1, 6)]
    steps += [
        AssertHeadStep(latest="genesis"),
        AssertCanonicalStep(blocks={1: None, 5: None}),
        ForkchoiceUpdatedStep(
            head="a5", safe="a4", finalized="a3", expect=applied("a5")
        ),
        AssertCanonicalStep(blocks={i: f"a{i}" for i in range(1, 6)}),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_reexecute_payloads(reorg_test: ReorgTestFiller, pre: Alloc) -> None:
    """
    Hive ``ReExecutePayloadTest``, besu
    ``shouldReturnSuccessOnAlreadyPresent``,
    reth ``test_find_invalid_ancestor_detects_block_itself``: re-sending a
    canonical payload stays VALID; re-sending an invalid one stays INVALID.
    """
    blocks, steps = chain(pre, "a", 5)
    sender = pre.fund_eoa()
    blocks.append(
        ReorgBlock(
            label="bad",
            parent="a5",
            txs=[Transaction(sender=sender, nonce=0, to=sender, value=1)],
            rlp_modifier=Header(state_root=Hash(1)),
            exception=[
                BlockException.INVALID_STATE_ROOT,
                BlockException.INVALID_BLOCK_HASH,
            ],
        )
    )
    for i in range(1, 6):
        steps.append(
            NewPayloadStep(
                block=f"a{i}",
                expect=[
                    Outcome(
                        id="valid", status="VALID", latest_valid_hash=f"a{i}"
                    )
                ],
            )
        )
    steps += [
        NewPayloadStep(block="bad"),
        NewPayloadStep(
            block="bad",
            expect=[
                Outcome(id="invalid", status="INVALID", latest_valid_hash="a5")
            ],
        ),
        AssertHeadStep(latest="a5"),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_many_siblings_same_parent(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Hive ``MultiplePayloadsExtendingCanonicalChainTest``: 40 sibling payloads
    (differing prevRandao) on the current head are all VALID/ACCEPTED; the
    canonical block at that height is then applied without error.
    """
    blocks, steps = chain(pre, "a", 3)
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    siblings = []
    for i in range(40):
        siblings.append(
            ReorgBlock(
                label=f"s{i}",
                parent="a3",
                prev_randao=Hash(0x1000 + i),
                txs=[
                    Transaction(sender=sender, nonce=0, to=recipient, value=1)
                ],
            )
        )
    canonical = ReorgBlock(
        label="a4",
        parent="a3",
        txs=[Transaction(sender=sender, nonce=0, to=recipient, value=2)],
    )
    blocks += siblings + [canonical]
    steps += [NewPayloadStep(block=s.label) for s in siblings]
    steps += [
        NewPayloadStep(block="a4"),
        ForkchoiceUpdatedStep(
            head="a4",
            expect=applied("a4"),
            branches={"applied": [AssertCanonicalStep(blocks={4: "a4"})]},
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_out_of_order_payload_delivery(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Hive ``NewPayloadOnSyncingClientTest``, reth
    ``test_engine_tree_buffered_blocks_are_eventually_connected``, nethermind
    ``payloadV1_invalid_parent_hash``: a payload whose parent is unknown is
    SYNCING/ACCEPTED and FCU to it is SYNCING; once the gap is filled the
    payload and the FCU are VALID.
    """
    blocks, steps = chain(pre, "a", 4)
    steps = steps[:4]  # a1, a2 delivered and canonical.
    steps += [
        NewPayloadStep(
            block="a4",
            expect=[
                Outcome(id="syncing", status="SYNCING"),
                Outcome(
                    id="accepted", status="ACCEPTED", latest_valid_hash="null"
                ),
            ],
        ),
        ForkchoiceUpdatedStep(
            head="a4", expect=[Outcome(id="syncing", status="SYNCING")]
        ),
        NewPayloadStep(
            block="a3",
            expect=[
                Outcome(id="valid", status="VALID", latest_valid_hash="a3")
            ],
        ),
        NewPayloadStep(
            block="a4",
            expect=[
                Outcome(id="valid", status="VALID", latest_valid_hash="a4")
            ],
        ),
        ForkchoiceUpdatedStep(head="a4", expect=applied("a4")),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_alternating_canonical_and_depth1_forks(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Geth ``testBlockchainHeaderchainReorgConsistency`` (16 rounds): for each
    new canonical block, also apply a sibling fork of depth 1 and back; the
    head must be consistent after every single FCU.
    """
    n = 16
    blocks, steps = chain(pre, "a", n)
    sender = pre.fund_eoa()
    forks = [
        ReorgBlock(
            label=f"f{i}",
            parent="genesis" if i == 1 else f"a{i - 1}",
            txs=[Transaction(sender=sender, nonce=0, to=sender, value=1)],
            extra_data=b"f",
        )
        for i in range(1, n + 1)
    ]
    blocks += forks
    interleaved: List[Step] = []
    for i in range(1, n + 1):
        interleaved += steps[2 * (i - 1) : 2 * i]
        interleaved += [
            NewPayloadStep(block=f"f{i}"),
            ForkchoiceUpdatedStep(head=f"f{i}", expect=applied(f"f{i}")),
            ForkchoiceUpdatedStep(head=f"a{i}", expect=applied(f"a{i}")),
        ]
    reorg_test(
        pre=pre, blocks=blocks, steps=interleaved, meta={"class": "shallow"}
    )


@pytest.mark.valid_from("Cancun")
def test_valid_and_invalid_forks_with_older_canonical_head(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Reth ``test_engine_tree_valid_forks_with_older_canonical_head`` and its
    ``_and_invalid_`` variant: canonical to a6; head moved back to a1; two
    8-block forks A/B off a6 delivered; FCU(B tip) applied; FCU(A tip) also
    VALID; an invalid block on top of A is INVALID and the head stays.
    """
    blocks, steps = chain(pre, "a", 6)
    fa, _ = chain(pre, "x", 8, parent="a6", start=7, value=2)
    fb, _ = chain(pre, "y", 8, parent="a6", start=7, value=3)
    sender = pre.fund_eoa()
    bad = ReorgBlock(
        label="bad",
        parent="x14",
        txs=[Transaction(sender=sender, nonce=0, to=sender, value=1)],
        rlp_modifier=Header(state_root=Hash(1)),
        exception=[
            BlockException.INVALID_STATE_ROOT,
            BlockException.INVALID_BLOCK_HASH,
        ],
    )
    blocks += fa + fb + [bad]
    steps.append(
        ForkchoiceUpdatedStep(head="a1", expect=rewind_outcomes("a1"))
    )
    steps += [NewPayloadStep(block=b.label) for b in fa + fb]
    steps += [
        ForkchoiceUpdatedStep(
            head="y14",
            expect=applied("y14"),
            branches={
                "applied": [AssertCanonicalStep(blocks={14: "y14", 6: "a6"})]
            },
        ),
        ForkchoiceUpdatedStep(
            head="x14",
            expect=applied("x14"),
            branches={"applied": [AssertCanonicalStep(blocks={14: "x14"})]},
        ),
        NewPayloadStep(
            block="bad",
            expect=[
                Outcome(
                    id="invalid", status="INVALID", latest_valid_hash="x14"
                )
            ],
        ),
        AssertCanonicalStep(blocks={14: "x14", 15: None}),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_reorg_to_fork_behind_finalized(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Reth ``test_reorg_to_fork_behind_finalized``: with finalized = a7 and
    head = a10, FCU to a fork tip branching at a5 (so a7 is not on its chain)
    with finalized still a7. Spec: ``-38002``. reth applies it (trusts the
    CL) — recorded as disputed. After a ``-38002`` the head is unspecified
    (geth and reth move it to f10 before failing the finalized check), so
    the canonical mapping is only asserted on the applied branch.
    """
    blocks, steps = chain(pre, "a", 10)
    fork, _ = chain(pre, "f", 5, parent="a5", start=6, value=2)
    blocks += fork
    steps.append(
        ForkchoiceUpdatedStep(
            head="a10", safe="a10", finalized="a7", expect=applied("a10")
        )
    )
    steps += [NewPayloadStep(block=b.label) for b in fork]
    steps.append(
        ForkchoiceUpdatedStep(
            head="f10",
            safe="f10",
            finalized="a7",
            expect=[
                Outcome(
                    id="inconsistent", error_code=INVALID_FORKCHOICE_STATE
                ),
                Outcome(
                    id="applied",
                    status="VALID",
                    latest_valid_hash="f10",
                    disputed=DISPUTED_FORK_BEHIND_FINALIZED,
                ),
            ],
            branches={
                "applied": [AssertCanonicalStep(blocks={10: "f10"})],
            },
        )
    )
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})
