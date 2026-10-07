"""Test the on-demand post-state context used by execute."""

from typing import Any, Dict, List

import pytest

from execution_testing.base_types import Address, Hash
from execution_testing.test_types import (
    EOA,
    GasFee,
    PostStateContext,
    Tip,
    Transaction,
)

from ..transaction_post import RPCPostStateContext

SENDER = EOA(key=1)
MINER = Address(0xC0FFEE)
BLOCK_HASH = Hash(0xB1)


class FakeEthRPC:
    """Serve one block and its receipts, counting every request."""

    def __init__(self, txs: List[Transaction]) -> None:
        """Land all `txs` in `BLOCK_HASH` at an effective price of 12."""
        self.receipt_requests: List[Hash] = []
        self.block_requests: List[Hash] = []
        self.receipts = {
            tx.hash: {
                "blockHash": str(BLOCK_HASH),
                "effectiveGasPrice": hex(12),
            }
            for tx in txs
        }

    def get_transaction_receipt(self, tx_hash: Hash) -> Dict[str, Any]:
        """Return the receipt of `tx_hash`."""
        self.receipt_requests.append(tx_hash)
        return self.receipts[tx_hash]

    def get_block_by_hash(
        self, block_hash: Hash, full_txs: bool = True
    ) -> Dict[str, Any]:
        """Return the block header fields used by the context."""
        del full_txs
        self.block_requests.append(block_hash)
        return {"baseFeePerGas": hex(7), "miner": str(MINER)}


def signed_txs(count: int) -> List[Transaction]:
    """Return `count` signed transactions from `SENDER`."""
    return [
        Transaction(
            sender=SENDER, nonce=nonce, gas_limit=21_000
        ).with_signature_and_sender()
        for nonce in range(count)
    ]


def test_gas_cost_fetches_only_the_receipt() -> None:
    """Test that a sender's fee needs the receipt but not the block."""
    txs = signed_txs(1)
    rpc = FakeEthRPC(txs)
    context = RPCPostStateContext(
        eth_rpc=rpc,  # type: ignore[arg-type]
        txs=txs,
    )
    assert rpc.receipt_requests == []

    assert GasFee(txs[0], gas=2).resolve(context) == 2 * 12
    assert rpc.receipt_requests == [txs[0].hash]
    assert rpc.block_requests == []


def test_fetches_on_demand_and_caches() -> None:
    """Test that receipts are fetched once and blocks once per block."""
    txs = signed_txs(3)
    rpc = FakeEthRPC(txs)
    context = RPCPostStateContext(
        eth_rpc=rpc,  # type: ignore[arg-type]
        txs=txs,
    )

    expression = Tip(txs[0], gas=10) + Tip(txs[1], gas=10)
    assert expression.resolve(context) == 2 * 10 * (12 - 7)
    assert rpc.receipt_requests == [txs[0].hash, txs[1].hash]
    assert rpc.block_requests == [BLOCK_HASH]

    assert GasFee(txs[0], gas=1).resolve(context) == 12
    assert len(rpc.receipt_requests) == 2, "receipt should be cached"

    assert context.landing((Address(SENDER), 2)).fee_recipient() == MINER
    assert len(rpc.receipt_requests) == 3
    assert rpc.block_requests == [BLOCK_HASH], "block should be cached"


def test_unknown_transaction() -> None:
    """Test that a transaction that was never sent did not land."""
    context = RPCPostStateContext(
        eth_rpc=FakeEthRPC([]),  # type: ignore[arg-type]
        txs=[],
    )
    with pytest.raises(PostStateContext.TransactionNotLandedError):
        GasFee(signed_txs(1)[0], gas=1).resolve(context)
