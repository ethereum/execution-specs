"""
Invalid payloads on side chains and the ``latestValidHash`` contract.

Ports of:

- hive ``BadHashOnNewPayload`` (canonical / sidechain):
  https://github.com/ethereum/hive/blob/ae173f1ce15aed785e6c0945c2156a95819d21bf/simulators/ethereum/engine/suites/engine/bad_hash.go#L41
- hive ``ParentHashOnNewPayload``:
  https://github.com/ethereum/hive/blob/ae173f1ce15aed785e6c0945c2156a95819d21bf/simulators/ethereum/engine/suites/engine/bad_hash.go#L139
- hive ``InvalidPayloadTestCase`` (per field, canonical and sidechain,
  non-syncing variants):
  https://github.com/ethereum/hive/blob/ae173f1ce15aed785e6c0945c2156a95819d21bf/simulators/ethereum/engine/suites/engine/invalid_payload.go#L23
- hive ``InvalidMissingAncestorReOrgTest`` (payloads via NP, no P2P):
  https://github.com/ethereum/hive/blob/ae173f1ce15aed785e6c0945c2156a95819d21bf/simulators/ethereum/engine/suites/engine/invalid_ancestor.go#L27
- reth ``test_engine_tree_reorg_with_missing_ancestor_expecting_valid_e2e``:
  https://github.com/paradigmxyz/reth/blob/8458973f25fec5e2bc1a51992da041620c266e62/crates/engine/tree/tests/e2e-testsuite/main.rs#L468
- reth ``test_engine_tree_fcu_canon_chain_insertion_v1_e2e``:
  https://github.com/paradigmxyz/reth/blob/8458973f25fec5e2bc1a51992da041620c266e62/crates/engine/tree/tests/e2e-testsuite/main.rs#L297
- besu ``shouldReturnInvalidWithLatestValidHashIsABadBlock``:
  https://github.com/besu-eth/besu/blob/0930cdcd1b8723e9db608e6ea48edcd644b86b2c/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineNewPayloadV1Test.java#L258
- besu ``shouldReturnInvalidBlockHashOnBadHashParameter``:
  https://github.com/besu-eth/besu/blob/0930cdcd1b8723e9db608e6ea48edcd644b86b2c/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineNewPayloadV1Test.java#L314
- besu ``shouldReturnInvalidOnBlockExecutionError``:
  https://github.com/besu-eth/besu/blob/0930cdcd1b8723e9db608e6ea48edcd644b86b2c/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineNewPayloadV1Test.java#L208
- besu ``shouldReturnInvalidWhenBadBlock``:
  https://github.com/besu-eth/besu/blob/0930cdcd1b8723e9db608e6ea48edcd644b86b2c/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineNewPayloadV1Test.java#L416
- nethermind ``executePayloadV1_rejects_invalid_blockHash``:
  https://github.com/NethermindEth/nethermind/blob/c8bb53e7f807ad476d3073c3e092070037bd451b/src/Nethermind/Nethermind.Merge.Plugin.Test/EngineModuleTests.V1.cs#L434
- nethermind
  ``executePayloadV1_invalid_hash_returns_invalid_and_does_not_store_bad_block``:
  https://github.com/NethermindEth/nethermind/blob/c8bb53e7f807ad476d3073c3e092070037bd451b/src/Nethermind/Nethermind.Merge.Plugin.Test/EngineModuleTests.V1.cs#L446
- geth ``TestInvalidBloom`` (style only):
  https://github.com/ethereum/go-ethereum/blob/93d4038b088fd7a3102d90ad5feda5e50f6aaebf/eth/catalyst/api_test.go#L977
- geth ``TestSideImportPrunedBlocks`` (style only: an invalid side block never
  becomes canonical):
  https://github.com/ethereum/go-ethereum/blob/93d4038b088fd7a3102d90ad5feda5e50f6aaebf/core/blockchain_test.go#L2498
"""

from typing import Any, Dict

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
    GetPayloadStep,
    NewPayloadStep,
    Outcome,
)
from execution_testing.specs import ReorgBlock, ReorgTestFiller

from .helpers import applied, build_attrs, chain

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

SINK = Address(0xC0DE)
"""Recipient of every value transfer in this module's chains."""


@pytest.mark.valid_from("Shanghai")
@pytest.mark.parametrize(
    "on_side_chain", [False, True], ids=["canonical", "sidechain"]
)
def test_bad_block_hash_on_new_payload(
    reorg_test: ReorgTestFiller, pre: Alloc, on_side_chain: bool
) -> None:
    """
    Hive ``BadHashOnNewPayload``: a payload whose ``blockHash`` does not match
    its contents is ``INVALID`` with a null latestValidHash (shanghai.md
    supplants V1's ``INVALID_BLOCK_HASH``); the head does not move. The same
    payload with its correct hash is then deliverable and becomes the head,
    so the client recorded neither the claimed hash nor the contents as bad.
    """
    blocks, steps = chain(pre, "a", 3, recipient=SINK)
    parent = "a3"
    if on_side_chain:
        side, _ = chain(pre, "s", 1, parent="a2", start=3, recipient=SINK)
        blocks += side
        steps.append(NewPayloadStep(block="s3"))
        parent = "s3"
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, nonce=0, to=sender, value=1)
    blocks += [
        ReorgBlock(
            label="badhash",
            parent=parent,
            txs=[tx],
            engine_new_payload_block_hash=Hash(0xBAD),
        ),
        ReorgBlock(label="real", parent=parent, txs=[tx]),
    ]
    steps += [
        NewPayloadStep(
            block="badhash",
            expect=[
                Outcome(
                    id="invalid", status="INVALID", latest_valid_hash="null"
                ),
            ],
        ),
        AssertHeadStep(latest="a3"),
        ForkchoiceUpdatedStep(
            head="badhash",
            expect=[
                Outcome(id="syncing", status="SYNCING"),
                Outcome(id="invalid", status="INVALID"),
            ],
        ),
        AssertHeadStep(latest="a3"),
        NewPayloadStep(block="real"),
        ForkchoiceUpdatedStep(head="real", expect=applied("real")),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_parent_hash_equals_block_hash(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Hive ``ParentHashOnNewPayload``: ``parentHash == blockHash`` (self
    parent) cannot be a valid block hash: ``INVALID`` with a null
    latestValidHash.
    """
    blocks, steps = chain(pre, "a", 2, recipient=SINK)
    sender = pre.fund_eoa()
    blocks.append(
        ReorgBlock(
            label="selfparent",
            parent="a2",
            txs=[Transaction(sender=sender, nonce=0, to=sender, value=1)],
            engine_new_payload_parent_hash=Hash(0x5E1F),
            engine_new_payload_block_hash=Hash(0x5E1F),
        )
    )
    steps += [
        NewPayloadStep(
            block="selfparent",
            expect=[
                Outcome(
                    id="invalid", status="INVALID", latest_valid_hash="null"
                ),
            ],
        ),
        AssertHeadStep(latest="a2"),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
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
    INVALID with ``latestValidHash`` = its parent; on a side chain, where
    the client may skip validation, ACCEPTED as well. In the canonical
    ``state_root`` variant the client then builds, imports and selects a
    payload on the same head. A valid sibling afterwards is fine.
    """
    blocks, steps = chain(pre, "a", 3, recipient=SINK)
    parent = "a3"
    if on_side_chain:
        side, _ = chain(pre, "s", 1, parent="a2", start=3, recipient=SINK)
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
                *(
                    [
                        Outcome(
                            id="syncing",
                            status="SYNCING",
                            disputed=(
                                "go-ethereum looks the parent up by "
                                "(parentHash, number - 1), so a wrong number "
                                "reads as an unknown parent"
                            ),
                        )
                    ]
                    if field == "number"
                    else []
                ),
                *(
                    [
                        Outcome(
                            id="accepted",
                            status="ACCEPTED",
                            latest_valid_hash="null",
                        )
                    ]
                    if on_side_chain
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
            ],
        ),
        AssertHeadStep(latest="a3"),
    ]
    if not on_side_chain and field == "state_root":
        # The payload builder still works after a rejected payload.
        steps.append(
            ForkchoiceUpdatedStep(
                head="a3",
                payload_attributes=build_attrs(0x01),
                expect=applied("a3", payload_id=True),
                branches={
                    "applied": [
                        GetPayloadStep(bind="built", parent="a3"),
                        NewPayloadStep(block="built"),
                        ForkchoiceUpdatedStep(
                            head="built", expect=applied("built")
                        ),
                    ]
                },
            )
        )
    steps += [
        NewPayloadStep(block="good"),
        ForkchoiceUpdatedStep(
            head="good",
            expect=[
                Outcome(id="applied", status="VALID", latest_valid_hash="good")
            ],
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
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
    delivered in order and, as in hive, each valid one is made the head. The
    invalid one then extends the head and is INVALID (lvh = its parent),
    or, as the first side block, also ACCEPTED; all descendants are INVALID
    (lvh = last valid) or SYNCING/ACCEPTED if the client dropped the invalid
    block; the head stays on the last valid block and the reorg back to a5
    is applied. ``reorg_from_canonical`` branches the side chain off a4
    rather than genesis.
    """
    blocks, steps = chain(pre, "a", 5, recipient=SINK)
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
                txs=[Transaction(sender=sender, nonce=i, to=SINK, value=3)],
                **kwargs,
            )
        )
    blocks += side
    last_valid = (
        parent if invalid_index == 1 else f"s{start + invalid_index - 2}"
    )
    for i, b in enumerate(side):
        if i + 1 < invalid_index:
            steps += [
                NewPayloadStep(block=b.label),
                ForkchoiceUpdatedStep(head=b.label, expect=applied(b.label)),
            ]
        elif i + 1 == invalid_index:
            steps.append(NewPayloadStep(block=b.label))
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
        AssertHeadStep(latest="a5" if invalid_index == 1 else last_valid),
        ForkchoiceUpdatedStep(head="a5", expect=applied("a5")),
        AssertCanonicalStep(blocks={5: "a5"}),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_invalid_ancestor_descendants_delivered_first(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Reth ``test_engine_tree_reorg_with_missing_ancestor_expecting_valid_e2e``:
    the *descendants* of an invalid block are delivered before the invalid
    block itself (SYNCING: an ancestor is unknown); once the invalid
    ancestor arrives it is INVALID and the buffered descendants, re-sent,
    are INVALID with lvh = the invalid block's parent.
    """
    blocks, steps = chain(pre, "a", 3, recipient=SINK)
    sender = pre.fund_eoa()
    bad = ReorgBlock(
        label="bad",
        parent="a3",
        txs=[Transaction(sender=sender, nonce=0, to=sender, value=1)],
        rlp_modifier=Header(state_root=Hash(1)),
        exception=STATEROOT_OR_HASH,
    )
    kids, _ = chain(pre, "k", 3, parent="bad", start=5, recipient=SINK)
    blocks += [bad] + kids
    steps += [
        NewPayloadStep(
            block=k.label, expect=[Outcome(id="syncing", status="SYNCING")]
        )
        for k in kids
    ]
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
    reorg_test(pre=pre, blocks=blocks, steps=steps)
