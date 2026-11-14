"""
Payload building on reorganized heads (client-built payloads bound via
``getPayload``).

Source mapping and port limitations: ``tests/reorg/README.md``
(test_payload_building_reorg.py section).
"""

from typing import List

import pytest
from execution_testing import (
    Alloc,
    EngineAPIError,
    Fork,
    Hash,
    Op,
    Transaction,
)
from execution_testing.fixtures.reorg import (
    AccountExpectation,
    AssertCanonicalStep,
    AssertReceiptStep,
    AssertStateStep,
    ForkchoiceUpdatedStep,
    GetPayloadStep,
    NewPayloadStep,
    Outcome,
    PayloadAttributes,
    SendRawTransactionStep,
    Step,
    TxRef,
)
from execution_testing.specs import ReorgBlock, ReorgTestFiller

from .helpers import applied, build_attrs

REFERENCE_SPEC_GIT_PATH = "src/engine/paris.md"
REFERENCE_SPEC_VERSION = "execution-apis#786"


@pytest.mark.valid_from("Shanghai")
def test_build_on_previously_validated_side_payload(
    reorg_test: ReorgTestFiller, pre: Alloc, fork: Fork
) -> None:
    r"""
    Port of hive ``ReOrgPrevValidatedPayloadOnSideChainTest``.

    genesis <- a1 <- a2 <- a3
            \\- s1 <- s2 <- s3      (side chain, validated via newPayload)

    Reorg to the non-leaf side payload s2 while requesting a build; the built
    payload must have s2 as parent; sending it back is VALID and FCU to it is
    applied. Then the canonical chain must still be re-appliable.

    Then FCU to s2 with build attributes the client must reject: a
    timestamp equal to s2's (``-38003``) and, from ``forkchoiceUpdatedV4``
    on, ``forkchoiceUpdatedV3`` with this fork's attributes (``-38005``).
    Both checks run after the forkchoice update, which must stand
    (paris.md forkchoiceUpdated step 8), so s2 is the head afterwards.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    blocks = []
    for i in range(1, 4):
        blocks.append(
            ReorgBlock(
                label=f"a{i}",
                txs=[
                    Transaction(
                        sender=sender, nonce=i - 1, to=recipient, value=1
                    )
                ],
            )
        )
    for i in range(1, 4):
        blocks.append(
            ReorgBlock(
                label=f"s{i}",
                parent="genesis" if i == 1 else f"s{i - 1}",
                txs=[
                    Transaction(
                        sender=sender, nonce=i - 1, to=recipient, value=2
                    )
                ],
            )
        )
    steps: List[Step] = []
    for i in range(1, 4):
        steps += [
            NewPayloadStep(block=f"a{i}"),
            ForkchoiceUpdatedStep(head=f"a{i}"),
        ]
    for i in range(1, 4):
        steps.append(NewPayloadStep(block=f"s{i}"))
    steps += [
        ForkchoiceUpdatedStep(
            head="s2",
            payload_attributes=build_attrs(0xAA),
            expect=applied("s2", payload_id=True),
            branches={
                "applied": [
                    GetPayloadStep(bind="s3x", parent="s2"),
                    NewPayloadStep(block="s3x"),
                    ForkchoiceUpdatedStep(
                        head="s3x",
                        expect=applied("s3x"),
                        branches={
                            "applied": [
                                AssertCanonicalStep(blocks={2: "s2", 3: "s3x"})
                            ]
                        },
                    ),
                ]
            },
        ),
        ForkchoiceUpdatedStep(
            head="a3",
            expect=applied("a3"),
            branches={"applied": [AssertCanonicalStep(blocks={3: "a3"})]},
        ),
    ]

    def rejected_build(
        attributes: PayloadAttributes,
        error: EngineAPIError,
        version: int | None = None,
    ) -> List[Step]:
        return [
            ForkchoiceUpdatedStep(
                head="s2",
                payload_attributes=attributes,
                version=version,
                expect=[Outcome(id="rejected", error_code=error)],
                branches={"rejected": [AssertCanonicalStep(blocks={2: "s2"})]},
            ),
            ForkchoiceUpdatedStep(head="a3", expect=applied("a3")),
        ]

    # 12 seconds per block from a genesis at 0: s2's own timestamp.
    steps += rejected_build(
        build_attrs(0xBB, timestamp=24),
        EngineAPIError.InvalidPayloadAttributes,
    )
    fcu_version = fork.engine_forkchoice_updated_version()
    assert fcu_version is not None
    if fcu_version > 3:
        steps += rejected_build(
            build_attrs(0xCC), EngineAPIError.UnsupportedFork, version=3
        )
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_two_built_payloads_same_parent(
    reorg_test: ReorgTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    Port of hive ``SidechainReOrgTest``: a pending transaction stores
    PREVRANDAO at its block number; two payloads built on the same parent
    with different ``prevRandao`` both include it, and each switch of the
    head between them must switch ``latest``, the canonical mapping and the
    stored value.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    store = Op.SSTORE(Op.NUMBER, Op.PREVRANDAO)
    randao_store = pre.deploy_contract(store)
    # Raw-sent transactions carry an explicit gas limit and a tip above
    # geth's default ``--miner.gasprice``. The limit is the exact gas of the
    # call: setting a fresh slot costs 107,920 gas from Amsterdam on.
    tx = Transaction(
        sender=pre.fund_eoa(),
        nonce=0,
        to=randao_store,
        gas_limit=fork.transaction_intrinsic_cost_calculator()()
        + fork.transaction_top_frame_gas_calculator()()
        + store.gas_cost(fork),
        gas_price=30 * 10**9,
    )
    blocks = [
        ReorgBlock(
            label="a1",
            txs=[Transaction(sender=sender, nonce=0, to=recipient, value=1)],
        ),
        # Carrier block for the raw tx bytes (never sent as a payload).
        ReorgBlock(
            label="carrier", parent="genesis", txs=[tx], extra_data=b"c"
        ),
    ]
    pool_tx = TxRef(block="carrier", index=0)

    def select(label: str, prev_randao: int) -> ForkchoiceUpdatedStep:
        return ForkchoiceUpdatedStep(
            head=label,
            expect=applied(label),
            branches={
                "applied": [
                    AssertCanonicalStep(blocks={2: label}),
                    AssertStateStep(
                        accounts={
                            randao_store: AccountExpectation(
                                storage={Hash(2): Hash(prev_randao)}
                            )
                        }
                    ),
                ]
            },
        )

    steps: List[Step] = [
        NewPayloadStep(block="a1"),
        ForkchoiceUpdatedStep(head="a1"),
        SendRawTransactionStep(tx=pool_tx),
        ForkchoiceUpdatedStep(
            head="a1",
            payload_attributes=build_attrs(0x01),
            expect=applied("a1", payload_id=True),
            branches={
                "applied": [
                    GetPayloadStep(
                        bind="p", parent="a1", transactions_include=[pool_tx]
                    ),
                    ForkchoiceUpdatedStep(
                        head="a1",
                        payload_attributes=build_attrs(0x02),
                        expect=applied("a1", payload_id=True),
                        branches={
                            "applied": [
                                GetPayloadStep(
                                    bind="q",
                                    parent="a1",
                                    transactions_include=[pool_tx],
                                ),
                                NewPayloadStep(block="p"),
                                NewPayloadStep(block="q"),
                                select("p", 0x01),
                                select("q", 0x02),
                                select("p", 0x01),
                            ]
                        },
                    ),
                ]
            },
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)


@pytest.mark.valid_from("Shanghai")
def test_pool_tx_reorged_out_of_built_payload(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Partial port of hive ``TransactionReOrgTest`` (``ReOrgOut``).

    A pool transaction is included in a payload built on a1 (bound ``p``);
    after FCU to ``p`` its receipt exists. Reorg to sibling b1 (which does
    not contain it): no receipt. Reorg back to ``p``: receipt is back.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    # Tip above geth's default ``--miner.gasprice`` (1 gwei): the pool accepts
    # cheaper txs but the payload builder skips them.
    tx = Transaction(
        sender=sender,
        nonce=0,
        to=recipient,
        value=7,
        gas_limit=21_000,
        gas_price=30 * 10**9,
    )
    blocks = [
        ReorgBlock(label="a1", txs=[]),
        ReorgBlock(label="b1", parent="genesis", txs=[], extra_data=b"b"),
        # Carrier block for the raw tx bytes (never sent as a payload).
        ReorgBlock(
            label="carrier", parent="genesis", txs=[tx], extra_data=b"c"
        ),
    ]
    pool_tx = TxRef(block="carrier", index=0)
    steps: List[Step] = [
        NewPayloadStep(block="a1"),
        NewPayloadStep(block="b1"),
        ForkchoiceUpdatedStep(head="a1"),
        SendRawTransactionStep(tx=pool_tx),
        # Pending: no receipt yet.
        AssertReceiptStep(tx=pool_tx, block=None),
        ForkchoiceUpdatedStep(
            head="a1",
            payload_attributes=build_attrs(0x0A),
            expect=applied("a1", payload_id=True),
            branches={
                "applied": [
                    GetPayloadStep(
                        bind="p", parent="a1", transactions_include=[pool_tx]
                    ),
                    NewPayloadStep(block="p"),
                    # Delivered but not canonical: still no receipt.
                    AssertReceiptStep(tx=pool_tx, block=None),
                    ForkchoiceUpdatedStep(
                        head="p",
                        expect=applied("p"),
                        branches={
                            "applied": [
                                AssertReceiptStep(tx=pool_tx, block="p")
                            ]
                        },
                    ),
                    ForkchoiceUpdatedStep(
                        head="b1",
                        expect=applied("b1"),
                        branches={
                            "applied": [
                                AssertReceiptStep(tx=pool_tx, block=None)
                            ]
                        },
                    ),
                    ForkchoiceUpdatedStep(
                        head="p",
                        expect=applied("p"),
                        branches={
                            "applied": [
                                AssertReceiptStep(tx=pool_tx, block="p")
                            ]
                        },
                    ),
                ]
            },
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps)
