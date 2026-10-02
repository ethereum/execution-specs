"""
Invalid payloads on side chains and the ``latestValidHash`` contract.

Ports of:
- hive ``BadHashOnNewPayload`` (canonical / sidechain),
  ``ParentHashOnNewPayload``, ``InvalidPayloadTestCase`` (per field,
  canonical and sidechain, non-syncing variants),
  ``InvalidMissingAncestorReOrgTest`` (payloads via NP, no P2P),
  ``InvalidTransitionPayload`` is out of scope (genesis is post-merge
  here).
- reth ``test_engine_tree_reorg_with_missing_ancestor_expecting_valid``,
  ``test_find_invalid_ancestor_in_buffered_blocks``,
  ``test_engine_tree_fcu_canon_chain_insertion``,
  ``test_handle_invalid_block``.
- besu ``shouldReturnInvalidWithLatestValidHashIsABadBlock``,
  ``shouldReturnInvalidBlockHashOnBadHashParameter``,
  ``shouldReturnInvalidOnBlockExecutionError``,
  ``shouldReturnInvalidWhenBadBlock``,
  ``shouldPropagateBadBlockToDescendants`` (bad-block-manager tests).
- nethermind ``newPayloadV1_should_return_invalid_when_block_hash_wrong``
  and ``executePayloadV1_invalid_block_...`` family,
  ``Invalid_blocks_should_be_...``.
- geth ``TestInvalidBloom``/``TestSideImportPrunedBlocks``-style: an
  invalid side block never becomes canonical.
"""

from typing import Any, Dict, List

import pytest
from execution_testing import (
    Address,
    Alloc,
    BlockException,
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

REFERENCE_SPEC_GIT_PATH = "src/engine/paris.md"
REFERENCE_SPEC_VERSION = "execution-apis#786"

INVALID_FIELDS: Dict[str, Dict[str, Any]] = {
    "state_root": {"state_root": Hash(1)},
    "receipts_root": {"receipts_root": Hash(1)},
    "number": {"number": 99},
    "gas_limit": {"gas_limit": 1},
    "gas_used": {"gas_used": 1},
    "timestamp": {"timestamp": 1},
    "base_fee": {"base_fee_per_gas": 1},
    "logs_bloom": {"logs_bloom": b"\x01" * 256},
}
"""Header fields corrupted per hive ``InvalidPayloadTestCase``."""

STATEROOT_OR_HASH = [
    BlockException.INVALID_STATE_ROOT,
    BlockException.INVALID_BLOCK_HASH,
]


def linear(
    pre: Alloc,
    n: int,
    prefix: str = "a",
    parent: str = "genesis",
    start: int = 1,
) -> tuple[List[ReorgBlock], List[Step]]:
    """Linear chain with one value transfer per block."""
    sender = pre.fund_eoa()
    blocks = [
        ReorgBlock(
            label=f"{prefix}{start + i}",
            parent=parent if i == 0 else None,
            txs=[
                Transaction(
                    sender=sender, nonce=i, to=Address(0xC0DE), value=1
                )
            ],
        )
        for i in range(n)
    ]
    steps: List[Step] = []
    for b in blocks:
        steps += [
            NewPayloadStep(block=b.label),
            ForkchoiceUpdatedStep(head=b.label),
        ]
    return blocks, steps


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "on_side_chain", [False, True], ids=["canonical", "sidechain"]
)
def test_bad_block_hash_on_new_payload(
    reorg_test: ReorgTestFiller, pre: Alloc, on_side_chain: bool
) -> None:
    """
    Hive ``BadHashOnNewPayload``: a payload whose ``blockHash`` does not match
    its contents is ``INVALID_BLOCK_HASH`` (Paris) / ``INVALID`` with null
    latestValidHash (Shanghai+); the head does not move; a valid child of
    the *real* block remains deliverable.
    """
    blocks, steps = linear(pre, 3)
    parent = "a3"
    if on_side_chain:
        side, _ = linear(pre, 1, prefix="s", parent="a2", start=3)
        blocks += side
        steps.append(NewPayloadStep(block="s3"))
        parent = "s3"
    sender = pre.fund_eoa()
    blocks.append(
        ReorgBlock(
            label="badhash",
            parent=parent,
            txs=[Transaction(sender=sender, nonce=0, to=sender, value=1)],
            payload_block_hash=Hash(0xBAD),
        )
    )
    steps += [
        NewPayloadStep(
            block="badhash",
            expect=[
                Outcome(
                    id="invalid", status="INVALID", latest_valid_hash="null"
                ),
                Outcome(id="invalid_block_hash", status="INVALID_BLOCK_HASH"),
            ],
        ),
        AssertHeadStep(latest="a3"),
        ForkchoiceUpdatedStep(
            head="badhash",
            expect=[
                Outcome(id="syncing", status="SYNCING"),
                Outcome(id="invalid", status="INVALID"),
                Outcome(id="error", any_error=True),
            ],
        ),
        AssertHeadStep(latest="a3"),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_parent_hash_equals_block_hash(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Hive ``ParentHashOnNewPayload``: ``parentHash == blockHash`` (self
    parent) cannot be a valid block hash: INVALID / INVALID_BLOCK_HASH.
    """
    blocks, steps = linear(pre, 2)
    sender = pre.fund_eoa()
    blocks.append(
        ReorgBlock(
            label="selfparent",
            parent="a2",
            txs=[Transaction(sender=sender, nonce=0, to=sender, value=1)],
            payload_parent_hash=Hash(0x5E1F),
            payload_block_hash=Hash(0x5E1F),
        )
    )
    steps += [
        NewPayloadStep(
            block="selfparent",
            expect=[
                Outcome(
                    id="invalid", status="INVALID", latest_valid_hash="null"
                ),
                Outcome(id="invalid_block_hash", status="INVALID_BLOCK_HASH"),
            ],
        ),
        AssertHeadStep(latest="a2"),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("field", sorted(INVALID_FIELDS))
@pytest.mark.parametrize(
    "on_side_chain", [False, True], ids=["canonical", "sidechain"]
)
def test_invalid_payload_field(
    reorg_test: ReorgTestFiller, pre: Alloc, field: str, on_side_chain: bool
) -> None:
    """
    Hive ``InvalidPayloadTestCase``: a payload with one corrupted header
    field (hash recomputed, so it is a *well-formed* invalid block) is
    INVALID with ``latestValidHash`` = its parent, on the canonical chain
    and on a side chain. A valid sibling afterwards is fine.
    """
    blocks, steps = linear(pre, 3)
    parent = "a3"
    if on_side_chain:
        side, _ = linear(pre, 1, prefix="s", parent="a2", start=3)
        blocks += side
        steps.append(NewPayloadStep(block="s3"))
        parent = "s3"
    sender = pre.fund_eoa()
    blocks.append(
        ReorgBlock(
            label="bad",
            parent=parent,
            txs=[Transaction(sender=sender, nonce=0, to=sender, value=1)],
            rlp_modifier=Header(**INVALID_FIELDS[field]),
            exception=[
                BlockException.INVALID_STATE_ROOT,
                BlockException.INVALID_BLOCK_HASH,
                BlockException.INVALID_RECEIPTS_ROOT,
                BlockException.INVALID_GASLIMIT,
                BlockException.INVALID_GAS_USED,
                BlockException.INVALID_BLOCK_NUMBER,
                BlockException.INVALID_BLOCK_TIMESTAMP_OLDER_THAN_PARENT,
                BlockException.INVALID_BASEFEE_PER_GAS,
                BlockException.INVALID_LOG_BLOOM,
                BlockException.INCORRECT_BLOCK_FORMAT,
            ],
        )
    )
    good = ReorgBlock(
        label="good",
        parent=parent,
        txs=[Transaction(sender=sender, nonce=0, to=sender, value=2)],
    )
    blocks.append(good)
    steps += [
        NewPayloadStep(
            block="bad",
            expect=[
                Outcome(
                    id="invalid", status="INVALID", latest_valid_hash=parent
                ),
                # Some clients reject malformed number/timestamp before
                # linking the parent and answer with a null lvh.
                Outcome(
                    id="invalid_unlinked",
                    status="INVALID",
                    latest_valid_hash="null",
                ),
                # A wrong number breaks (parentHash, number-1) linking: the
                # client may treat the parent as unknown (hive allows SYNCING
                # for InvalidNumber).
                *(
                    [Outcome(id="syncing", status="SYNCING")]
                    if field == "number"
                    else []
                ),
            ],
        ),
        ForkchoiceUpdatedStep(
            head="bad",
            expect=[
                Outcome(
                    id="invalid", status="INVALID", latest_valid_hash=parent
                ),
                Outcome(id="syncing", status="SYNCING"),
                Outcome(id="error", any_error=True),
            ],
        ),
        AssertHeadStep(latest="a3"),
        NewPayloadStep(block="good"),
        ForkchoiceUpdatedStep(
            head="good",
            expect=[
                Outcome(id="applied", status="VALID", latest_valid_hash="good")
            ],
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("invalid_index", [1, 3, 5])
@pytest.mark.parametrize(
    "reorg_from_canonical",
    [False, True],
    ids=["from_genesis", "from_canonical"],
)
def test_invalid_missing_ancestor_reorg(
    reorg_test: ReorgTestFiller,
    pre: Alloc,
    invalid_index: int,
    reorg_from_canonical: bool,
) -> None:
    """
    Hive ``InvalidMissingAncestorReOrgTest`` (NewPayload delivery): a side
    chain of 10 blocks with block ``invalid_index`` invalid; payloads are
    delivered in order. The invalid one is INVALID (lvh = its parent), all
    descendants INVALID (lvh = last valid) or SYNCING/ACCEPTED if the client
    dropped the invalid block; the head never moves to the side chain.
    ``reorg_from_canonical`` branches the side chain off a4 rather than
    genesis.
    """
    blocks, steps = linear(pre, 5)
    parent = "a4" if reorg_from_canonical else "genesis"
    start = 5 if reorg_from_canonical else 1
    sender = pre.fund_eoa()
    side = []
    for i in range(10):
        label = f"s{start + i}"
        kwargs: Dict[str, Any] = {}
        if i + 1 == invalid_index:
            kwargs = {
                "rlp_modifier": Header(state_root=Hash(1)),
                "exception": STATEROOT_OR_HASH,
            }
        side.append(
            ReorgBlock(
                label=label,
                parent=parent if i == 0 else None,
                txs=[
                    Transaction(
                        sender=sender, nonce=i, to=Address(0xC0DE), value=3
                    )
                ],
                **kwargs,
            )
        )
    blocks += side
    last_valid = (
        parent if invalid_index == 1 else f"s{start + invalid_index - 2}"
    )
    for i, b in enumerate(side):
        if i + 1 < invalid_index:
            steps.append(
                NewPayloadStep(
                    block=b.label,
                    expect=[
                        Outcome(
                            id="valid",
                            status="VALID",
                            latest_valid_hash=b.label,
                        )
                    ],
                )
            )
        elif i + 1 == invalid_index:
            steps.append(
                NewPayloadStep(
                    block=b.label,
                    expect=[
                        Outcome(
                            id="invalid",
                            status="INVALID",
                            latest_valid_hash=last_valid,
                        )
                    ],
                )
            )
        else:
            steps.append(
                NewPayloadStep(
                    block=b.label,
                    expect=[
                        Outcome(
                            id="invalid",
                            status="INVALID",
                            latest_valid_hash=last_valid,
                        ),
                        Outcome(id="syncing", status="SYNCING"),
                        Outcome(
                            id="accepted",
                            status="ACCEPTED",
                            latest_valid_hash="null",
                        ),
                    ],
                )
            )
    steps += [
        ForkchoiceUpdatedStep(
            head=side[-1].label,
            expect=[
                Outcome(
                    id="invalid",
                    status="INVALID",
                    latest_valid_hash=last_valid,
                ),
                Outcome(id="syncing", status="SYNCING"),
            ],
        ),
        AssertHeadStep(latest="a5"),
        AssertCanonicalStep(blocks={5: "a5"}),
        ForkchoiceUpdatedStep(
            head="a5",
            expect=[
                Outcome(id="applied", status="VALID", latest_valid_hash="a5")
            ],
        ),
    ]
    reorg_test(
        pre=pre,
        blocks=blocks,
        steps=steps,
        meta={"class": "shallow", "reorgDepth": 5},
    )


@pytest.mark.valid_from("Cancun")
def test_invalid_ancestor_descendants_delivered_first(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Reth ``test_find_invalid_ancestor_in_buffered_blocks`` /
    ``test_engine_tree_reorg_with_missing_ancestor_expecting_valid``: the
    *descendants* of an invalid block are delivered before the invalid
    block itself (buffered as SYNCING/ACCEPTED); once the invalid ancestor
    arrives it is INVALID and the buffered descendants, re-sent, are INVALID
    with lvh = the invalid block's parent.
    """
    blocks, steps = linear(pre, 3)
    sender = pre.fund_eoa()
    bad = ReorgBlock(
        label="bad",
        parent="a3",
        txs=[Transaction(sender=sender, nonce=0, to=sender, value=1)],
        rlp_modifier=Header(state_root=Hash(1)),
        exception=STATEROOT_OR_HASH,
    )
    kids, _ = linear(pre, 3, prefix="k", parent="bad", start=5)
    blocks += [bad] + kids
    buffered = [
        Outcome(id="syncing", status="SYNCING"),
        Outcome(id="accepted", status="ACCEPTED", latest_valid_hash="null"),
    ]
    steps += [NewPayloadStep(block=k.label, expect=buffered) for k in kids]
    steps += [
        ForkchoiceUpdatedStep(
            head="k7", expect=[Outcome(id="syncing", status="SYNCING")]
        ),
        NewPayloadStep(
            block="bad",
            expect=[
                Outcome(id="invalid", status="INVALID", latest_valid_hash="a3")
            ],
        ),
    ]
    steps += [
        NewPayloadStep(
            block=k.label,
            expect=[
                Outcome(
                    id="invalid", status="INVALID", latest_valid_hash="a3"
                ),
                Outcome(id="syncing", status="SYNCING"),
                Outcome(
                    id="accepted", status="ACCEPTED", latest_valid_hash="null"
                ),
            ],
        )
        for k in kids
    ]
    steps += [
        ForkchoiceUpdatedStep(
            head="k7",
            expect=[
                Outcome(
                    id="invalid", status="INVALID", latest_valid_hash="a3"
                ),
                Outcome(id="syncing", status="SYNCING"),
            ],
        ),
        AssertHeadStep(latest="a3"),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})
