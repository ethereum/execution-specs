"""
Transaction, receipt, log and transaction-pool behaviour across reorgs.

Ports of:
- go-ethereum `core/blockchain_test.go:testChainTxReorgs` (shared /
  dropped / postponed / added transactions) and `testLogReorgs`.
- besu `DefaultBlockchainTest.reorgWithOverlappingTransactions`.
- erigon `engine_api_reorg_test.go`:
  `TestEthGetLogsDoNotGetAffectedAfterNewPayloadOnSideChain`.
- reth `e2e/pool.rs:maintain_txpool_reorg`, besu
  `shouldReAddTransactionsFromThePreviousCanonicalHeadWhenAReorgOccurs`
  / `shouldNotReAddTransactionsThatAreInBothForksWhenReorgHappens`, geth
  `legacypool.reset` (pool re-injection is client policy: recorded, not
  required).
"""

from typing import List

import pytest
from execution_testing import Alloc, Transaction
from execution_testing.fixtures.reorg import (
    AssertCanonicalStep,
    AssertLogsStep,
    AssertReceiptStep,
    AssertTxStatusStep,
    ForkchoiceUpdatedStep,
    NewPayloadStep,
    Outcome,
    SendRawTransactionStep,
    Step,
    TxRef,
)
from execution_testing.specs import ReorgBlock, ReorgTestFiller
from execution_testing.vm import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "src/engine/paris.md"
REFERENCE_SPEC_VERSION = "execution-apis#786"


def applied(head: str) -> List[Outcome]:
    """Single legal outcome: the forkchoice update is applied."""
    return [Outcome(id="applied", status="VALID", latest_valid_hash=head)]


@pytest.mark.valid_from("Cancun")
def test_tx_reorg_shared_dropped_postponed_added(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    r"""
    Port of geth ``testChainTxReorgs``.

    genesis <- a1 <- a2 <- a3        (canonical first)
            \\- b1 <- b2 <- b3 <- b4  (reorg target)

    - shared: in a1 and b1 (same tx) — stays included after the reorg.
    - dropped: only in a-chain — no receipt after the reorg.
    - postponed: in a2, re-included later in b4.
    - added: only in b-chain — receipt appears after the reorg.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    other = pre.fund_eoa()

    shared = Transaction(sender=sender, nonce=0, to=recipient, value=1)
    dropped = Transaction(sender=sender, nonce=1, to=recipient, value=2)
    postponed = Transaction(sender=other, nonce=0, to=recipient, value=3)
    added = Transaction(sender=sender, nonce=1, to=recipient, value=4)
    filler_b2 = Transaction(sender=other, nonce=1, to=recipient, value=5)

    blocks = [
        ReorgBlock(label="a1", txs=[shared]),
        ReorgBlock(label="a2", txs=[dropped, postponed]),
        ReorgBlock(label="a3", txs=[]),
        ReorgBlock(
            label="b1", parent="genesis", txs=[shared], extra_data=b"b"
        ),
        ReorgBlock(label="b2", txs=[added]),
        ReorgBlock(label="b3", txs=[]),
        ReorgBlock(label="b4", txs=[postponed, filler_b2]),
    ]

    after_a = [
        AssertReceiptStep(tx=TxRef(block="a1", index=0), block="a1"),
        AssertReceiptStep(tx=TxRef(block="a2", index=0), block="a2"),
        AssertReceiptStep(tx=TxRef(block="a2", index=1), block="a2"),
        AssertReceiptStep(tx=TxRef(block="b2", index=0), block=None),
        AssertTxStatusStep(
            tx=TxRef(block="a2", index=0),
            expect=["included"],
            included_in="a2",
        ),
    ]
    after_b = [
        # shared: same hash, now in b1.
        AssertReceiptStep(tx=TxRef(block="a1", index=0), block="b1"),
        # dropped: gone from the canonical chain; pool re-injection is policy.
        AssertReceiptStep(tx=TxRef(block="a2", index=0), block=None),
        AssertTxStatusStep(
            tx=TxRef(block="a2", index=0), expect=["pending", "dropped"]
        ),
        # postponed: now in b4.
        AssertReceiptStep(tx=TxRef(block="a2", index=1), block="b4"),
        # added: now included.
        AssertReceiptStep(tx=TxRef(block="b2", index=0), block="b2"),
        AssertCanonicalStep(blocks={1: "b1", 2: "b2", 3: "b3", 4: "b4"}),
    ]

    steps: List[Step] = []
    for label in ("a1", "a2", "a3"):
        steps += [
            NewPayloadStep(block=label),
            ForkchoiceUpdatedStep(head=label),
        ]
    steps[-1] = ForkchoiceUpdatedStep(head="a3", branches={"applied": after_a})
    for label in ("b1", "b2", "b3", "b4"):
        steps.append(NewPayloadStep(block=label))
    steps.append(
        ForkchoiceUpdatedStep(
            head="b4", expect=applied("b4"), branches={"applied": after_b}
        )
    )
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_logs_follow_reorg(reorg_test: ReorgTestFiller, pre: Alloc) -> None:
    r"""
    Port of geth ``testLogReorgs`` and erigon
    ``TestEthGetLogsDoNotGetAffectedAfterNewPayloadOnSideChain``.

    genesis <- a1(log) <- a2(log)
            \\- b1(log) <- b2

    ``eth_getLogs`` over the whole range must return the canonical chain's
    logs only: a non-canonical ``newPayload`` must not leak logs; after the
    reorg the a-chain logs disappear and the b-chain logs appear.
    """
    sender = pre.fund_eoa()
    emitter = pre.deploy_contract(code=Op.LOG1(0, 0, 0x1234) + Op.STOP)

    def emit(nonce: int, value: int) -> Transaction:
        return Transaction(
            sender=sender,
            nonce=nonce,
            to=emitter,
            value=value,
            gas_limit=100_000,
        )

    blocks = [
        ReorgBlock(label="a1", txs=[emit(0, 1)]),
        ReorgBlock(label="a2", txs=[emit(1, 2)]),
        ReorgBlock(label="b1", parent="genesis", txs=[emit(0, 3)]),
        ReorgBlock(label="b2", txs=[]),
    ]
    steps: List[Step] = [
        NewPayloadStep(block="a1"),
        ForkchoiceUpdatedStep(head="a1"),
        NewPayloadStep(block="a2"),
        ForkchoiceUpdatedStep(
            head="a2",
            branches={
                "applied": [
                    AssertLogsStep(address=emitter, blocks=["a1", "a2"])
                ]
            },
        ),
        # Side chain known but not canonical: logs unaffected.
        NewPayloadStep(block="b1"),
        NewPayloadStep(block="b2"),
        AssertLogsStep(address=emitter, blocks=["a1", "a2"]),
        ForkchoiceUpdatedStep(
            head="b2",
            expect=applied("b2"),
            branches={
                "applied": [
                    AssertLogsStep(address=emitter, blocks=["b1"]),
                    AssertReceiptStep(
                        tx=TxRef(block="a2", index=0), block=None
                    ),
                ]
            },
        ),
        # And back.
        ForkchoiceUpdatedStep(
            head="a2",
            expect=applied("a2"),
            branches={
                "applied": [
                    AssertLogsStep(address=emitter, blocks=["a1", "a2"])
                ]
            },
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})


@pytest.mark.valid_from("Cancun")
def test_txpool_reinjection_after_reorg(
    reorg_test: ReorgTestFiller, pre: Alloc
) -> None:
    r"""
    Port of reth ``maintain_txpool_reorg`` / besu txpool re-add tests / geth
    ``legacypool.reset``.

    genesis <- a1(tx1)
            \\- b1(tx2, same sender+nonce, conflicting)

    tx1 is sent through the pool, then included in a1. After the reorg to b1
    (which contains the conflicting tx2), tx1 is no longer canonical; whether
    the client re-injects it into the pool (``pending``) or drops it is
    client policy and is recorded. tx2 must be ``included`` in b1. Reorging
    back to a1 must restore tx1's receipt.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    # Explicit gas limit: raw-sent txs must not inherit the block-filling
    # default the filler assigns to payload txs.
    tx1 = Transaction(
        sender=sender, nonce=0, to=recipient, value=1, gas_limit=21_000
    )
    tx2 = Transaction(
        sender=sender, nonce=0, to=recipient, value=2, gas_limit=21_000
    )
    blocks = [
        ReorgBlock(label="a1", txs=[tx1]),
        ReorgBlock(label="b1", parent="genesis", txs=[tx2]),
    ]
    steps: List[Step] = [
        SendRawTransactionStep(tx=TxRef(block="a1", index=0)),
        AssertTxStatusStep(tx=TxRef(block="a1", index=0), expect=["pending"]),
        NewPayloadStep(block="a1"),
        ForkchoiceUpdatedStep(
            head="a1",
            branches={
                "applied": [
                    AssertTxStatusStep(
                        tx=TxRef(block="a1", index=0),
                        expect=["included"],
                        included_in="a1",
                    )
                ]
            },
        ),
        NewPayloadStep(block="b1"),
        ForkchoiceUpdatedStep(
            head="b1",
            expect=applied("b1"),
            branches={
                "applied": [
                    AssertReceiptStep(
                        tx=TxRef(block="b1", index=0), block="b1"
                    ),
                    AssertReceiptStep(
                        tx=TxRef(block="a1", index=0), block=None
                    ),
                    AssertTxStatusStep(
                        tx=TxRef(block="a1", index=0),
                        expect=["pending", "dropped"],
                    ),
                ]
            },
        ),
        ForkchoiceUpdatedStep(
            head="a1",
            expect=applied("a1"),
            branches={
                "applied": [
                    AssertReceiptStep(
                        tx=TxRef(block="a1", index=0), block="a1"
                    ),
                    AssertReceiptStep(
                        tx=TxRef(block="b1", index=0), block=None
                    ),
                ]
            },
        ),
    ]
    reorg_test(pre=pre, blocks=blocks, steps=steps, meta={"class": "shallow"})
