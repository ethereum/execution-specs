"""
Reorgs across a fork boundary (transition at timestamp 15000; filled for every
transition from Paris -> Shanghai onwards).

Ports of:

- hive ``WithdrawalsReorgSpec`` ("Withdrawals Fork on Block N - M Block Re-Org"
  via NewPayload):
  https://github.com/ethereum/hive/blob/ae173f1ce15aed785e6c0945c2156a95819d21bf/simulators/ethereum/engine/suites/withdrawals/tests.go#L1500
- hive ``suites/cancun`` (fork-transition payload-version tests, e.g.):
  https://github.com/ethereum/hive/blob/ae173f1ce15aed785e6c0945c2156a95819d21bf/simulators/ethereum/engine/suites/cancun/tests.go#L774
- geth ``TestSetCanonical`` (style only: fork-crossing reorgs):
  https://github.com/ethereum/go-ethereum/blob/93d4038b088fd7a3102d90ad5feda5e50f6aaebf/core/blockchain_test.go#L3410
- besu ``MergeCoordinatorTest`` (post-fork payload handling):
  https://github.com/besu-eth/besu/blob/def0a84d72bcf54816132c2843852eb38fdbbe59/consensus/merge/src/test/java/org/hyperledger/besu/consensus/merge/blockcreation/MergeCoordinatorTest.java
- nethermind ``ForkChoiceUpdated_should_return_proper_error_code`` (wrong
  version -> -38005):
  https://github.com/NethermindEth/nethermind/blob/c8bb53e7f807ad476d3073c3e092070037bd451b/src/Nethermind/Nethermind.Merge.Plugin.Test/EngineModuleTests.V3.cs#L492

Genesis is the pre-fork; blocks at or after timestamp 15000 are post-fork and
use the post-fork ``engine_newPayload``/``forkchoiceUpdated`` versions (V1 ->
V2 -> V3 -> V4; only post-fork payloads carry the new fork's fields, such as
withdrawals or execution requests). A reorg may move the head from a
post-fork block to a pre-fork block and back.
"""

from typing import Any, Dict, List

import pytest
from execution_testing import EOA, Address, Alloc, Transaction, Withdrawal
from execution_testing.fixtures.reorg import (
    AccountExpectation,
    AssertCanonicalStep,
    AssertHeadStep,
    AssertStateStep,
    ForkchoiceUpdatedStep,
    NewPayloadStep,
    Outcome,
    Step,
)
from execution_testing.specs import ReorgBlock, ReorgTestFiller

from .helpers import applied

REFERENCE_SPEC_GIT_PATH = "src/engine/cancun.md"
REFERENCE_SPEC_VERSION = "execution-apis#786"

FORK_TS = 15_000


def withdrawn(gwei_to: Dict[EOA, int]) -> AssertStateStep:
    """Balances of withdrawal recipients, from the gwei credited to each."""
    return AssertStateStep(
        accounts={
            address: AccountExpectation(balance=gwei * 10**9)
            for address, gwei in gwei_to.items()
        }
    )


@pytest.mark.valid_at_transition_to("Shanghai", subsequent_forks=True)
@pytest.mark.parametrize("side_activates", ["later", "earlier"])
def test_reorg_across_fork_boundary(
    reorg_test: ReorgTestFiller, pre: Alloc, side_activates: str
) -> None:
    """
    Canonical a1..a5 and a side chain s4, s5 off a3 cross the fork at
    different heights. ``later``: a4 is the first post-fork block (ts
    15000) and s4 is still pre-fork (ts 14988). ``earlier``, hive's
    "canonical block 8, side block 7" mirror: a4 is pre-fork and s4
    post-fork, so a post-fork side block is imported at a height where the
    canonical chain is still pre-fork. Every post-fork block credits a
    withdrawal to its branch's recipient. Head moves a5 -> s4 -> s5 -> a5;
    every FCU is VALID, and the canonical mapping and both recipients'
    balances follow, so withdrawals of the losing branch are reverted.
    """
    later = side_activates == "later"
    ca = pre.fund_eoa()
    cs = pre.fund_eoa()
    sink = Address(0xC0DE)
    payee_a = pre.fund_eoa(amount=0)
    payee_s = pre.fund_eoa(amount=0)

    def block(
        label: str,
        sender: EOA,
        nonce: int,
        withdrawal_to: Address | None = None,
        **kwargs: Any,
    ) -> ReorgBlock:
        return ReorgBlock(
            label=label,
            txs=[Transaction(sender=sender, nonce=nonce, to=sink, value=1)],
            withdrawals=(
                [
                    Withdrawal(
                        index=nonce,
                        validator_index=0,
                        address=withdrawal_to,
                        amount=1,
                    )
                ]
                if withdrawal_to is not None
                else None
            ),
            **kwargs,
        )

    blocks = [
        block("a1", ca, 0, parent="genesis"),
        block("a2", ca, 1),
        block("a3", ca, 2),
        block(
            "a4",
            ca,
            3,
            payee_a if later else None,
            timestamp=FORK_TS if later else FORK_TS - 12,
        ),
        block("a5", ca, 4, payee_a),
        block(
            "s4",
            cs,
            0,
            None if later else payee_s,
            parent="a3",
            timestamp=FORK_TS - 12 if later else FORK_TS,
        ),
        block("s5", cs, 1, payee_s),
    ]
    # Gwei withdrawn to each recipient with each head.
    credited = (
        {
            "a5": {payee_a: 2, payee_s: 0},
            "s4": {payee_a: 0, payee_s: 0},
            "s5": {payee_a: 0, payee_s: 1},
        }
        if later
        else {
            "a5": {payee_a: 1, payee_s: 0},
            "s4": {payee_a: 0, payee_s: 1},
            "s5": {payee_a: 0, payee_s: 2},
        }
    )

    def balances(head: str) -> AssertStateStep:
        return withdrawn(credited[head])

    steps: List[Step] = []
    for label in ("a1", "a2", "a3", "a4", "a5"):
        steps += [
            NewPayloadStep(block=label),
            ForkchoiceUpdatedStep(head=label),
        ]
    steps += [
        balances("a5"),
        NewPayloadStep(block="s4"),
        NewPayloadStep(block="s5"),
        ForkchoiceUpdatedStep(
            head="s4",
            expect=applied("s4"),
            branches={
                "applied": [
                    AssertCanonicalStep(blocks={4: "s4", 5: None}),
                    balances("s4"),
                ]
            },
        ),
        ForkchoiceUpdatedStep(
            head="s5",
            expect=applied("s5"),
            branches={
                "applied": [
                    AssertCanonicalStep(blocks={4: "s4", 5: "s5"}),
                    balances("s5"),
                ]
            },
        ),
        ForkchoiceUpdatedStep(
            head="a5",
            expect=applied("a5"),
            branches={
                "applied": [
                    AssertCanonicalStep(blocks={3: "a3", 4: "a4", 5: "a5"}),
                    balances("a5"),
                ]
            },
        ),
        AssertHeadStep(latest="a5"),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_at_transition_to("Shanghai", subsequent_forks=True)
def test_sibling_first_fork_blocks(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Two competing *first* post-fork blocks on the last pre-fork block (hive
    ``WithdrawalsReorgSpec`` "Fork on Block 8 - 10 Block Re-Org" reduced):
    both VALID, head switches between them, then a child of the loser
    extends and takes the head. Each first post-fork block credits a
    withdrawal to its own recipient, checked after every head move.
    """
    ca = pre.fund_eoa()
    cs = pre.fund_eoa()
    sink = Address(0xC0DE)
    payee_a = pre.fund_eoa(amount=0)
    payee_b = pre.fund_eoa(amount=0)

    def withdrawal(to: Address) -> List[Withdrawal]:
        return [Withdrawal(index=0, validator_index=0, address=to, amount=1)]

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
            withdrawals=withdrawal(payee_a),
        ),
        ReorgBlock(
            label="b2",
            parent="a1",
            timestamp=FORK_TS + 12,
            txs=[Transaction(sender=cs, nonce=0, to=sink, value=2)],
            withdrawals=withdrawal(payee_b),
        ),
        ReorgBlock(
            label="b3", txs=[Transaction(sender=cs, nonce=1, to=sink, value=2)]
        ),
    ]

    def select(
        head: str, gwei_to: Dict[EOA, int], *checks: Step
    ) -> ForkchoiceUpdatedStep:
        return ForkchoiceUpdatedStep(
            head=head,
            expect=applied(head),
            branches={"applied": [*checks, withdrawn(gwei_to)]},
        )

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
        select("a2", {payee_a: 1, payee_b: 0}),
        select(
            "b2",
            {payee_a: 0, payee_b: 1},
            AssertCanonicalStep(blocks={2: "b2"}),
        ),
        select("a2", {payee_a: 1, payee_b: 0}),
        NewPayloadStep(block="b3"),
        select(
            "b3",
            {payee_a: 0, payee_b: 1},
            AssertCanonicalStep(blocks={2: "b2", 3: "b3"}),
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)
