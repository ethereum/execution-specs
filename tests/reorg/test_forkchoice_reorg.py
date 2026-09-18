"""
P0 reorg conformance tests.

- Sibling reorg: switch head between two blocks at the same height and verify
  state, head labels and canonical mapping follow the forkchoice.
- Invalid side chain: a side chain with one execution-invalid block; the
  invalid block and everything built on it must never become canonical.
- execution-apis#786 forkchoice semantics: no-reorg shortcut only below
  finalized; rewind to a canonical ancestor above finalized is a real reorg
  (or ``-38006``); finalized regression and inconsistent forkchoice states.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    BlockException,
    Hash,
    Header,
    Transaction,
)
from execution_testing.fixtures.reorg import (
    AccountExpectation,
    AssertCanonicalStep,
    AssertStateStep,
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

DISPUTED_SHORTCUT_VS_38002 = (
    "execution-apis#786: no-reorg shortcut (step 2) vs. inconsistent "
    "forkchoice state (step 5) when head is below finalized but the supplied "
    "safe/finalized are not on head's chain"
)
DISPUTED_SHORTCUT_VS_38006 = (
    "execution-apis#786: step 2 says a client MAY skip the update when head "
    "is an ancestor of finalized; a client that does not skip reaches step 6 "
    "and may refuse the (backwards) reorg with -38006 before step 5 is "
    "evaluated (observed on reth)"
)
DISPUTED_FINALIZED_REGRESSION = (
    "execution-apis: forkchoiceUpdated with finalizedBlockHash older than "
    "the previously finalized block is not addressed by the specification"
)


def linear_chain(
    pre: Alloc, length: int, prefix: str = "a"
) -> tuple[List[ReorgBlock], Account, List[Step]]:
    """
    ``length`` blocks, each with one value transfer, plus the newPayload/FCU
    steps that make the last one the head.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    blocks = [
        ReorgBlock(
            label=f"{prefix}{i}",
            txs=[
                Transaction(sender=sender, nonce=i - 1, to=recipient, value=1)
            ],
        )
        for i in range(1, length + 1)
    ]
    steps: List[Step] = []
    for i in range(1, length + 1):
        steps.append(NewPayloadStep(block=f"{prefix}{i}"))
        steps.append(ForkchoiceUpdatedStep(head=f"{prefix}{i}"))
    return blocks, Account(balance=length), steps


@pytest.mark.valid_from("Cancun")
def test_sibling_reorg(reorg_test: ReorgTestFiller, pre: Alloc) -> None:
    r"""
    Genesis <- a1 <- a2.
                 \\- b2.

    Head moves a2 -> b2 -> a2; the recipient balances, ``latest`` and the
    block at height 2 must follow each forkchoice update.
    """
    sender = pre.fund_eoa()
    recipient_a = pre.fund_eoa(amount=0)
    recipient_b = pre.fund_eoa(amount=0)

    blocks = [
        ReorgBlock(
            label="a1",
            txs=[Transaction(sender=sender, nonce=0, to=recipient_a, value=1)],
        ),
        ReorgBlock(
            label="a2",
            txs=[Transaction(sender=sender, nonce=1, to=recipient_a, value=2)],
        ),
        ReorgBlock(
            label="b2",
            parent="a1",
            txs=[Transaction(sender=sender, nonce=1, to=recipient_b, value=3)],
        ),
    ]

    on_a2 = [
        AssertCanonicalStep(blocks={2: "a2"}),
        AssertStateStep(
            accounts={
                recipient_a: AccountExpectation(balance=3),
                recipient_b: AccountExpectation(balance=0),
            }
        ),
    ]
    on_b2 = [
        AssertCanonicalStep(blocks={2: "b2"}),
        AssertStateStep(
            accounts={
                recipient_a: AccountExpectation(balance=1),
                recipient_b: AccountExpectation(balance=3),
            }
        ),
    ]

    steps: List[Step] = [
        NewPayloadStep(block="a1"),
        ForkchoiceUpdatedStep(head="a1"),
        NewPayloadStep(block="a2"),
        ForkchoiceUpdatedStep(head="a2", branches={"applied": list(on_a2)}),
        NewPayloadStep(block="b2"),
        # Same-height sibling: depth-1 reorg, must be applied by every client.
        ForkchoiceUpdatedStep(
            head="b2",
            expect=[
                Outcome(id="applied", status="VALID", latest_valid_hash="b2")
            ],
            branches={"applied": list(on_b2)},
        ),
        ForkchoiceUpdatedStep(
            head="a2",
            expect=[
                Outcome(id="applied", status="VALID", latest_valid_hash="a2")
            ],
            branches={"applied": list(on_a2)},
        ),
    ]

    reorg_test(
        pre=pre,
        blocks=blocks,
        steps=steps,
        meta={"class": "shallow", "reorgDepth": 1},
    )


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("invalid_index", [1, 3, 5])
def test_invalid_side_chain(
    reorg_test: ReorgTestFiller, pre: Alloc, invalid_index: int
) -> None:
    r"""
    Genesis <- a1 .. a5                 (canonical).
           \\- s1 .. s5                 (side chain, s_k invalid).

    ``newPayload(s_k)`` must be INVALID with ``latestValidHash`` = s_{k-1};
    later side blocks are INVALID or SYNCING; ``forkchoiceUpdated(s5)`` must
    not make the side chain canonical; the canonical chain keeps working.
    """
    blocks, _, steps = linear_chain(pre, 5, prefix="a")

    side_sender = pre.fund_eoa()
    side_recipient = pre.fund_eoa(amount=0)
    for i in range(1, 6):
        kwargs: dict = {}
        if i == invalid_index:
            kwargs = dict(
                rlp_modifier=Header(state_root=Hash(1)),
                exception=[
                    BlockException.INVALID_STATE_ROOT,
                    BlockException.INVALID_BLOCK_HASH,
                ],
            )
        blocks.append(
            ReorgBlock(
                label=f"s{i}",
                parent="genesis" if i == 1 else f"s{i - 1}",
                txs=[
                    Transaction(
                        sender=side_sender,
                        nonce=i - 1,
                        to=side_recipient,
                        value=1,
                    )
                ],
                **kwargs,
            )
        )

    last_valid = "genesis" if invalid_index == 1 else f"s{invalid_index - 1}"
    for i in range(1, 6):
        # `expect` derived by the model: VALID/ACCEPTED before the invalid
        # block, INVALID at it, INVALID-or-SYNCING after it.
        steps.append(NewPayloadStep(block=f"s{i}"))
    steps.append(
        ForkchoiceUpdatedStep(
            head="s5",
            expect=[
                Outcome(
                    id="invalid",
                    status="INVALID",
                    latest_valid_hash=last_valid,
                ),
                Outcome(id="syncing", status="SYNCING"),
            ],
        )
    )
    # Canonical chain is unaffected and still progresses.
    steps.append(
        ForkchoiceUpdatedStep(
            head="a5",
            expect=[
                Outcome(id="applied", status="VALID", latest_valid_hash="a5")
            ],
            branches={
                "applied": [
                    AssertCanonicalStep(
                        blocks={i: f"a{i}" for i in range(1, 6)}
                    ),
                    AssertStateStep(
                        accounts={
                            side_recipient: AccountExpectation(balance=0)
                        }
                    ),
                ]
            },
        )
    )

    reorg_test(
        pre=pre,
        blocks=blocks,
        steps=steps,
        meta={
            "class": "shallow",
            "sideLength": 5,
            "invalidIndex": invalid_index,
        },
    )


@pytest.mark.valid_from("Cancun")
def test_fcu_below_finalized_with_inconsistent_state(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    #786 case (a): finalized = a5, then FCU(head=a2, safe=a2, finalized=a5).

    a2 is an ancestor of finalized so the no-reorg shortcut (step 2) applies
    and yields VALID; but a5 is not on a2's chain so step 5 would yield
    ``-38002``, and a client that does not take the optional shortcut may
    treat the request as a backwards reorg and refuse with ``-38006`` (step
    6). The spec orders step 2 first; clients differ (geth: VALID no-op;
    reth 2.5.2: -38006) — recorded as disputed. Either way the head must not
    move.
    """
    blocks, _, steps = linear_chain(pre, 10)
    steps.append(
        ForkchoiceUpdatedStep(
            head="a10",
            safe="a10",
            finalized="a5",
            expect=[
                Outcome(id="applied", status="VALID", latest_valid_hash="a10")
            ],
        )
    )
    steps.append(
        ForkchoiceUpdatedStep(
            head="a2",
            safe="a2",
            finalized="a5",
            expect=[
                Outcome(id="noop", status="VALID", latest_valid_hash="a2"),
                Outcome(
                    id="inconsistent",
                    error_code=INVALID_FORKCHOICE_STATE,
                    disputed=DISPUTED_SHORTCUT_VS_38002,
                ),
                Outcome(
                    id="refused",
                    error_code=TOO_DEEP_REORG,
                    disputed=DISPUTED_SHORTCUT_VS_38006,
                ),
            ],
            branches={
                "noop": [AssertCanonicalStep(blocks={10: "a10", 2: "a2"})],
                "inconsistent": [AssertCanonicalStep(blocks={10: "a10"})],
                "refused": [AssertCanonicalStep(blocks={10: "a10"})],
            },
        )
    )
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_fcu_finalized_regression(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    #786 case (b): finalized = a9, then FCU(head=a10, finalized=a1).

    Moving finalized backwards is not addressed by the specification;
    accepting it (VALID) or rejecting it (``-38002``) are both recorded.
    """
    blocks, _, steps = linear_chain(pre, 10)
    steps.append(
        ForkchoiceUpdatedStep(
            head="a10",
            safe="a10",
            finalized="a9",
            expect=[
                Outcome(id="applied", status="VALID", latest_valid_hash="a10")
            ],
        )
    )
    steps.append(
        ForkchoiceUpdatedStep(
            head="a10",
            safe="a10",
            finalized="a1",
            expect=[
                Outcome(id="applied", status="VALID", latest_valid_hash="a10"),
                Outcome(
                    id="rejected",
                    error_code=INVALID_FORKCHOICE_STATE,
                    disputed=DISPUTED_FINALIZED_REGRESSION,
                ),
            ],
        )
    )
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_fcu_rewind_to_canonical_ancestor_above_finalized(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    #786 case (c): finalized = a5, head = a10, then FCU(head=a7, safe=a7,
    finalized=a5).

    a7 is above finalized: the client MUST rewind to a7 (VALID, latest = a7)
    or refuse with ``-38006``; a pre-#786 VALID no-op that leaves the head at
    a10 fails. Afterwards FCU(a10) must be VALID in either case and the chain
    must continue.
    """
    blocks, expected_recipient, steps = linear_chain(pre, 10)
    steps.append(
        ForkchoiceUpdatedStep(
            head="a10",
            safe="a10",
            finalized="a5",
            expect=[
                Outcome(id="applied", status="VALID", latest_valid_hash="a10")
            ],
        )
    )
    resume = [
        ForkchoiceUpdatedStep(
            head="a10",
            safe="a10",
            finalized="a5",
            expect=[
                Outcome(id="applied", status="VALID", latest_valid_hash="a10")
            ],
            branches={
                "applied": [
                    AssertCanonicalStep(blocks={7: "a7", 8: "a8", 10: "a10"}),
                ]
            },
        )
    ]
    steps.append(
        ForkchoiceUpdatedStep(
            head="a7",
            safe="a7",
            finalized="a5",
            expect=[
                Outcome(id="applied", status="VALID", latest_valid_hash="a7"),
                Outcome(id="refused", error_code=TOO_DEEP_REORG),
            ],
            branches={
                "applied": [
                    AssertCanonicalStep(blocks={7: "a7", 8: None, 10: None}),
                    *resume,
                ],
                "refused": [
                    AssertCanonicalStep(blocks={7: "a7", 10: "a10"}),
                    *resume,
                ],
            },
        )
    )
    reorg_test(
        pre=pre,
        blocks=blocks,
        steps=steps,
        meta={"class": "shallow", "reorgDepth": 3, "rewind": True},
    )
