"""
Payload building on reorganized heads (client-built payloads bound via
``getPayload``).

Ports of hive `suites/engine/reorg.go`:
- ``ReOrgPrevValidatedPayloadOnSideChainTest``: reorg to a previously
  validated non-leaf side payload and build a new payload on top of it.
- ``SidechainReOrgTest`` (build two payloads on the same parent with
  different attributes, switch between them).
- ``TransactionReOrgTest`` (``ReOrgOut``): a transaction sent to the pool is
  included when building on one head and absent from a payload built on a
  sibling head.
"""

from typing import List

import pytest
from execution_testing import Alloc, Hash, Transaction
from execution_testing.fixtures.reorg import (
    AssertCanonicalStep,
    AssertReceiptStep,
    FixturePayloadAttributes,
    ForkchoiceUpdatedStep,
    GetPayloadStep,
    NewPayloadStep,
    Outcome,
    SendRawTransactionStep,
    Step,
    TxRef,
)
from execution_testing.specs import ReorgBlock, ReorgTestFiller

REFERENCE_SPEC_GIT_PATH = "src/engine/paris.md"
REFERENCE_SPEC_VERSION = "execution-apis#786"

FEE_RECIPIENT = 0x1234


def build_attrs(prev_randao: int) -> FixturePayloadAttributes:
    """Payload attributes; timestamp/withdrawals/beacon root filled at fill."""
    return FixturePayloadAttributes(
        timestamp=0,
        prev_randao=Hash(prev_randao),
        suggested_fee_recipient=FEE_RECIPIENT,
    )


def applied(head: str, payload_id: bool = False) -> List[Outcome]:
    """Single legal outcome: applied (optionally with a payload id)."""
    return [
        Outcome(
            id="applied",
            status="VALID",
            latest_valid_hash=head,
            payload_id="nonNull" if payload_id else None,
        )
    ]


@pytest.mark.valid_from("Cancun")
def test_build_on_previously_validated_side_payload(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    r"""
    Port of hive ``ReOrgPrevValidatedPayloadOnSideChainTest``.

    genesis <- a1 <- a2 <- a3
            \\- s1 <- s2 <- s3      (side chain, validated via newPayload)

    Reorg to the non-leaf side payload s2 while requesting a build; the built
    payload must have s2 as parent; sending it back is VALID and FCU to it is
    applied. Then the canonical chain must still be re-appliable.
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
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_two_built_payloads_same_parent(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Port of hive ``SidechainReOrgTest``: build two payloads on the same
    parent with different ``prevRandao``, switch head between them, verify
    ``latest`` and the canonical mapping each time.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    blocks = [
        ReorgBlock(
            label="a1",
            txs=[Transaction(sender=sender, nonce=0, to=recipient, value=1)],
        )
    ]
    steps: List[Step] = [
        NewPayloadStep(block="a1"),
        ForkchoiceUpdatedStep(
            head="a1",
            payload_attributes=build_attrs(0x01),
            expect=applied("a1", payload_id=True),
            branches={
                "applied": [
                    GetPayloadStep(bind="p", parent="a1"),
                    ForkchoiceUpdatedStep(
                        head="a1",
                        payload_attributes=build_attrs(0x02),
                        expect=applied("a1", payload_id=True),
                        branches={
                            "applied": [
                                GetPayloadStep(bind="q", parent="a1"),
                                NewPayloadStep(block="p"),
                                NewPayloadStep(block="q"),
                                ForkchoiceUpdatedStep(
                                    head="p",
                                    expect=applied("p"),
                                    branches={
                                        "applied": [
                                            AssertCanonicalStep(
                                                blocks={2: "p"}
                                            )
                                        ]
                                    },
                                ),
                                ForkchoiceUpdatedStep(
                                    head="q",
                                    expect=applied("q"),
                                    branches={
                                        "applied": [
                                            AssertCanonicalStep(
                                                blocks={2: "q"}
                                            )
                                        ]
                                    },
                                ),
                                ForkchoiceUpdatedStep(
                                    head="p",
                                    expect=applied("p"),
                                    branches={
                                        "applied": [
                                            AssertCanonicalStep(
                                                blocks={2: "p"}
                                            )
                                        ]
                                    },
                                ),
                            ]
                        },
                    ),
                ]
            },
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_pool_tx_reorged_out_of_built_payload(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    """
    Port of hive ``TransactionReOrgTest`` (``ReOrgOut`` / ``ReOrgBackIn``).

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
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})
