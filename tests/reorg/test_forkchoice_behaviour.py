"""
Forkchoice behaviour across reorganizations (post-merge: the head follows
``forkchoiceUpdated`` regardless of chain length).

Source mapping and port limitations: ``tests/reorg/README.md``
(test_forkchoice_behaviour.py section).
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    BlockException,
    EngineAPIError,
    Hash,
    Header,
    Transaction,
)
from execution_testing.fixtures.reorg import (
    AssertCanonicalStep,
    AssertHeadStep,
    ForkchoiceUpdatedStep,
    NewPayloadStep,
    Outcome,
    Step,
)
from execution_testing.specs import ReorgBlock, ReorgTestFiller

from .helpers import applied, chain, reorg_outcomes

REFERENCE_SPEC_GIT_PATH = "src/engine/paris.md"
REFERENCE_SPEC_VERSION = "execution-apis#786"

DISPUTED_ZERO_SAFE = (
    "execution-apis#892: whether a zero safeBlockHash is legal once a block "
    "is finalized"
)
DISPUTED_FINALITY_REVERSION = (
    "execution-apis#983: whether a client may refuse a reorg that reverts "
    "the latest known finalized block"
)
DISPUTED_DISCARDED_BRANCH = (
    "paris.md forkchoiceUpdated point 9, related to execution-apis#983: "
    "whether a client may answer SYNCING for a block that was VALID before "
    "it discarded the block's branch at finalization"
)


@pytest.mark.valid_from("Shanghai")
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
    a_tip = f"a{canonical_len}"
    a_canonical = {i: f"a{i}" for i in range(1, canonical_len + 1)}
    steps += [NewPayloadStep(block=b.label) for b in b_blocks]
    # Delivering the fork moves neither the head nor the canonical chain.
    steps += [
        AssertHeadStep(latest=a_tip),
        AssertCanonicalStep(blocks=a_canonical),
    ]
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
    steps.append(
        ForkchoiceUpdatedStep(
            head=a_tip,
            expect=applied(a_tip),
            branches={"applied": [AssertCanonicalStep(blocks=a_canonical)]},
        )
    )
    _ = b_steps
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_forks_going_back_and_forward_in_height(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Three forks from genesis of 2, 1 and 2 blocks, each block delivered and
    then made the head, so the head drops from height 2 to 1 and climbs
    back. Every update is applied and nothing above the head stays
    canonical: a client that keeps canonical hashes above a lower head
    executes the next fork on a stale state and gets its state root wrong.
    """
    blocks: List[ReorgBlock] = []
    steps: List[Step] = []
    for prefix, length in (("a", 2), ("b", 1), ("c", 2)):
        fork, _ = chain(pre, prefix, length)
        blocks += fork
        for height, b in enumerate(fork, start=1):
            canonical = {i: f"{prefix}{i}" for i in range(1, height + 1)}
            steps += [
                NewPayloadStep(block=b.label),
                ForkchoiceUpdatedStep(
                    head=b.label,
                    expect=applied(b.label),
                    branches={
                        "applied": [
                            AssertCanonicalStep(
                                blocks={**canonical, height + 1: None}
                            )
                        ]
                    },
                ),
            ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_reorg_back_and_forth_between_branches(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Two 6-block branches off a 3-block base; the head ping-pongs between
    branch B's blocks and branch A's tip.
    """
    base, steps = chain(pre, "a", 3)
    a_ext, _ = chain(pre, "a", 6, parent="a3", start=4)
    b_ext, _ = chain(pre, "b", 6, parent="a3", start=4, value=2)
    blocks = base + a_ext + b_ext
    steps += [NewPayloadStep(block=b.label) for b in a_ext + b_ext]
    a_canonical = {i: f"a{i}" for i in range(1, 10)}
    steps.append(
        ForkchoiceUpdatedStep(
            head="a9",
            expect=applied("a9"),
            branches={"applied": [AssertCanonicalStep(blocks=a_canonical)]},
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
                                **{h: f"a{h}" for h in range(1, 4)},
                                **{h: f"b{h}" for h in range(4, i + 1)},
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
                    "applied": [AssertCanonicalStep(blocks=a_canonical)]
                },
            )
        )
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_reorg_to_older_canonical_ancestor_and_forward(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    After every new block, FCU back to a5 (a canonical ancestor above
    finalized) then forward to the tip. #786: the rewind, at most 5 deep
    and so within ``MIN_APPLIED_REORG_DEPTH``, must be applied; the forward
    FCU must always be VALID.
    """
    blocks, steps = chain(pre, "a", 5)
    more, _ = chain(pre, "a", 5, parent="a5", start=6)
    blocks += more
    steps.append(
        ForkchoiceUpdatedStep(
            head="a5", safe="a5", finalized="a1", expect=applied("a5")
        )
    )

    def forward_fcu(tip: str) -> ForkchoiceUpdatedStep:
        return ForkchoiceUpdatedStep(
            head=tip, safe="a5", finalized="a1", expect=applied(tip)
        )

    for i in range(6, 11):
        tip = f"a{i}"
        steps += [
            NewPayloadStep(block=tip),
            forward_fcu(tip),
            ForkchoiceUpdatedStep(
                head="a5",
                safe="a5",
                finalized="a1",
                expect=reorg_outcomes("a5", depth=i - 5),
                branches={
                    "applied": [
                        AssertCanonicalStep(blocks={5: "a5", 6: None}),
                        forward_fcu(tip),
                    ],
                },
            ),
        ]
    steps.append(
        AssertCanonicalStep(blocks={i: f"a{i}" for i in range(1, 11)})
    )
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_side_payload_executed_while_rewound(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Rewind ten blocks, execute a side payload there, return to the tip.

    Canonical a1..a15, each of a6..a15 with 50 transfers. FCU back to a5 is
    applied or, ten blocks being deeper than ``MIN_APPLIED_REORG_DEPTH``,
    refused with ``-38006``. Once applied, s6, a5's other child, extends the
    head and must be VALID. Either way a16 then follows a15 and FCU to it is
    applied.
    """
    blocks, steps = chain(pre, "a", 5)
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    for i in range(6, 17):
        blocks.append(
            ReorgBlock(
                label=f"a{i}",
                parent="a5" if i == 6 else None,
                txs=[
                    Transaction(
                        sender=sender,
                        nonce=(i - 6) * 50 + j,
                        to=recipient,
                        value=1,
                    )
                    for j in range(50)
                ],
            )
        )
        if i < 16:
            steps += [
                NewPayloadStep(block=f"a{i}"),
                ForkchoiceUpdatedStep(head=f"a{i}"),
            ]
    blocks.append(ReorgBlock(label="s6", parent="a5", txs=[], extra_data=b"s"))

    def back_to_the_tip() -> List[Step]:
        return [
            NewPayloadStep(block="s6"),
            NewPayloadStep(block="a16"),
            ForkchoiceUpdatedStep(head="a16", expect=applied("a16")),
            AssertCanonicalStep(blocks={5: "a5", 6: "a6", 16: "a16"}),
        ]

    steps.append(
        ForkchoiceUpdatedStep(
            head="a5",
            expect=reorg_outcomes("a5", depth=10),
            branches={
                "applied": [
                    AssertCanonicalStep(blocks={5: "a5", 6: None}),
                    *back_to_the_tip(),
                ],
                "refused": back_to_the_tip(),
            },
        )
    )
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_fcu_to_unknown_block_is_syncing(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    A 10-deep side chain exists but only its leaf is ever delivered. FCU to
    a block never delivered (s14) is SYNCING and leaves the head; the leaf
    is SYNCING (its ancestors are unknown, so ACCEPTED is not legal), and so
    is FCU to it; FCU naming s14 as safe or finalized is ``-38002``; FCU
    back to the canonical tip is VALID and the next canonical block a6 is
    VALID and becomes the head.
    """
    blocks, steps = chain(pre, "a", 6)
    steps, next_canonical = steps[:-2], steps[-2:]
    side, _ = chain(pre, "s", 10, parent="a5", start=6, value=3)
    blocks += side
    syncing = [Outcome(id="syncing", status="SYNCING")]
    unknown = [
        Outcome(
            id="inconsistent", error_code=EngineAPIError.InvalidForkchoiceState
        )
    ]
    steps += [
        ForkchoiceUpdatedStep(
            head="s14",
            expect=syncing,
            branches={"syncing": [AssertHeadStep(latest="a5")]},
        ),
        NewPayloadStep(block="s15", expect=syncing),
        ForkchoiceUpdatedStep(head="s15", expect=syncing),
        AssertHeadStep(latest="a5"),
        ForkchoiceUpdatedStep(head="a5", safe="s14", expect=unknown),
        ForkchoiceUpdatedStep(head="a5", finalized="s14", expect=unknown),
        ForkchoiceUpdatedStep(head="a5", expect=applied("a5")),
        *next_canonical,
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
@pytest.mark.parametrize("field", ["head", "safe", "finalized"])
def test_inconsistent_forkchoice_state(
    reorg_test: ReorgTestFiller, pre: Alloc, field: str
) -> None:
    """
    With canonical a1..a3 (safe a2, finalized a1) and a validated sibling
    chain b2..b4 on a1, an FCU whose ``field`` points into the other chain is
    ``-38002`` and leaves head, safe and finalized as they were; the
    canonical FCU afterwards is VALID. The sibling chain descends from the
    finalized a1, so ``field`` is the only reason for ``-38002``.
    """
    blocks, steps = chain(pre, "a", 3)
    side, _ = chain(pre, "b", 3, parent="a1", start=2, value=2)
    blocks += side
    steps += [NewPayloadStep(block=b.label) for b in side]
    canonical = {"head": "a3", "safe": "a2", "finalized": "a1"}
    state = dict(canonical)
    state[field] = {"head": "b4", "safe": "b3", "finalized": "b2"}[field]
    steps += [
        ForkchoiceUpdatedStep(**canonical, expect=applied("a3")),
        ForkchoiceUpdatedStep(
            **state,
            expect=[
                Outcome(
                    id="inconsistent",
                    error_code=EngineAPIError.InvalidForkchoiceState,
                )
            ],
        ),
        ForkchoiceUpdatedStep(**canonical, expect=applied("a3")),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_safe_finalized_labels_follow_fcu(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    ``latest``/``safe``/``finalized`` track every FCU, including a reorg of
    head and safe onto a side chain while finalized stays pinned, zero safe
    hash, and all three equal.
    """
    blocks, steps = chain(pre, "a", 3)
    side, _ = chain(pre, "b", 2, parent="a1", start=2, value=2)
    blocks += side

    def tail_fcus() -> List[Step]:
        return [
            ForkchoiceUpdatedStep(
                head="b3", safe="b3", finalized="b3", expect=applied("b3")
            ),
            # Reverts the finalized b3.
            ForkchoiceUpdatedStep(
                head="a3",
                safe="a3",
                finalized="a3",
                expect=[
                    *applied("a3"),
                    Outcome(
                        id="refused",
                        error_code=EngineAPIError.TooDeepReorg,
                        disputed=DISPUTED_FINALITY_REVERSION,
                    ),
                    # A client may have discarded a2..a3 when b3 was
                    # finalized.
                    Outcome(
                        id="syncing",
                        status="SYNCING",
                        disputed=DISPUTED_DISCARDED_BRANCH,
                    ),
                ],
                # A client that answers SYNCING must leave its state on b3.
                branches={
                    "syncing": [
                        AssertHeadStep(latest="b3", safe="b3", finalized="b3")
                    ]
                },
            ),
        ]

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
                    error_code=EngineAPIError.InvalidForkchoiceState,
                    disputed=DISPUTED_ZERO_SAFE,
                ),
            ],
            branches={
                "applied": tail_fcus(),
                "rejected": tail_fcus(),
            },
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_newpayload_does_not_move_head(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Payloads alone never change ``latest`` or the canonical mapping; a
    single FCU to the tip does.
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
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_reexecute_payloads(reorg_test: ReorgTestFiller, pre: Alloc) -> None:
    """
    Re-sending a canonical payload stays VALID; re-sending an invalid one
    stays INVALID.
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
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
@pytest.mark.parametrize(
    "canonical_first", [False, True], ids=["siblings_first", "canonical_first"]
)
def test_many_siblings_same_parent(
    reorg_test: ReorgTestFiller, pre: Alloc, canonical_first: bool
) -> None:
    """
    Sibling payloads (differing prevRandao) on the current head are all
    VALID, and FCU to the canonical block at that height is then applied.
    ``canonical_first`` delivers that block before the siblings, so the
    client selects a block it received before many others.
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
    sibling_steps = [NewPayloadStep(block=s.label) for s in siblings]
    canonical_step = NewPayloadStep(block="a4")
    if canonical_first:
        steps += [canonical_step, *sibling_steps]
    else:
        steps += [*sibling_steps, canonical_step]
    steps += [
        ForkchoiceUpdatedStep(
            head="a4",
            expect=applied("a4"),
            branches={"applied": [AssertCanonicalStep(blocks={4: "a4"})]},
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_out_of_order_payload_delivery(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    A payload whose parent is unknown is SYNCING and FCU to it is SYNCING;
    once the gap is filled the payload and the FCU are VALID.
    """
    blocks, steps = chain(pre, "a", 4)
    steps = steps[:4]  # a1, a2 delivered and canonical.
    steps += [
        NewPayloadStep(
            block="a4", expect=[Outcome(id="syncing", status="SYNCING")]
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
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_alternating_canonical_and_depth1_forks(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    For each of 16 new canonical blocks, also apply a sibling fork of depth
    1 and back; the head must be consistent after every single FCU.
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
    reorg_test(pre=pre, blocks=blocks, steps=interleaved)


@pytest.mark.valid_from("Shanghai")
def test_valid_and_invalid_forks_with_older_canonical_head(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Canonical to a6; head moved back to a1; two 8-block forks A/B off a6
    delivered; FCU(B tip) applied; FCU(A tip) also VALID; an invalid block
    on top of A is INVALID and the head stays.
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
        ForkchoiceUpdatedStep(
            head="a1",
            expect=[
                Outcome(
                    id="applied",
                    status="VALID",
                    latest_valid_hash="a1",
                    head_moved=True,
                )
            ],
        )
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
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_reorg_to_fork_behind_finalized(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    With finalized = a7 and head = a10, FCU to a fork tip branching at a5
    (so a7 is not on its chain) with finalized still a7 is ``-38002`` per
    paris.md step 5.
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
                    id="inconsistent",
                    error_code=EngineAPIError.InvalidForkchoiceState,
                ),
            ],
        )
    )
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_forkchoice_state_unchanged_on_invalid_state(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    A forkchoice update that fails the safe/finalized consistency check must
    leave the forkchoice state untouched.

    Canonical a1..a3 (head a3, safe a2, finalized a1) plus a validated
    sibling pair b2, b3 on a1. The call names b3 as head while safe stays
    on the ``a`` chain, so it must be answered with ``-38002``; every
    update resulting from the call is then required to have been applied
    atomically, i.e. not at all.
    """
    blocks, steps = chain(pre, "a", 3)
    side, _ = chain(pre, "b", 2, parent="a1", start=2, value=2)
    blocks += side
    steps += [
        NewPayloadStep(block="b2"),
        NewPayloadStep(block="b3"),
        ForkchoiceUpdatedStep(
            head="a3", safe="a2", finalized="a1", expect=applied("a3")
        ),
    ]
    steps.append(
        ForkchoiceUpdatedStep(
            head="b3",
            safe="a2",
            finalized="a1",
            expect=[
                Outcome(
                    id="inconsistent",
                    error_code=EngineAPIError.InvalidForkchoiceState,
                )
            ],
            branches={
                "inconsistent": [
                    AssertCanonicalStep(blocks={1: "a1", 2: "a2"})
                ]
            },
        )
    )
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_fcu_rewind_with_no_finalized(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Rewind the head to a canonical ancestor while no finalized block is known.

    The no-reorg shortcut is conditional on a known ``finalizedBlockHash`` and
    on the head being an ancestor of it; with a zero finalized hash neither
    holds, so the client must apply the rewind, which is within
    ``MIN_APPLIED_REORG_DEPTH``. A VALID answer that leaves the head where it
    was is not legal here.
    """
    blocks, steps = chain(pre, "a", 8)
    steps.append(
        ForkchoiceUpdatedStep(
            head="a5",
            safe="a5",
            expect=reorg_outcomes("a5", depth=3),
            branches={
                "applied": [AssertCanonicalStep(blocks={5: "a5", 6: None})],
            },
        )
    )
    reorg_test(pre=pre, blocks=blocks, steps=steps)
