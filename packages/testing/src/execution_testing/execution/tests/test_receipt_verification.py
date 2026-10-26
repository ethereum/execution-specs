"""Test the receipt verification of the transaction-post execute format."""

from typing import Any, Dict, List, Sequence

import pytest

from execution_testing.base_types import Address, Hash
from execution_testing.test_types import (
    EOA,
    Alloc,
    LogMismatchError,
    Transaction,
    TransactionLog,
    TransactionReceipt,
    TransactionReceiptMismatchError,
)

from ..transaction_post import TransactionPost

SENDER = EOA(key=1)
EMITTER = Address(0xE4177E2)


class FakeEthRPC:
    """Serve one receipt per transaction, counting every request."""

    def __init__(self, receipts: Dict[Hash, Dict[str, Any]]) -> None:
        """Serve the given `receipts`, keyed by transaction hash."""
        self.receipts = receipts
        self.requests: List[Hash] = []

    def get_transaction_receipts(
        self, transaction_hashes: Sequence[Hash]
    ) -> List[Dict[str, Any] | None]:
        """Return the receipts of `transaction_hashes`, in the same order."""
        self.requests.extend(transaction_hashes)
        return [self.receipts.get(tx_hash) for tx_hash in transaction_hashes]


def receipt_data(*, gas_used: int, **kwargs: Any) -> Dict[str, Any]:
    """Return the fields a node returns for a successful transaction."""
    return {
        "status": "0x1",
        "gasUsed": hex(gas_used),
        # The block carries transactions of other tests too, so the node's
        # cumulative value is always ahead of the group's own.
        "cumulativeGasUsed": hex(gas_used + 1_000_000),
        **kwargs,
    }


def transaction_post(
    tx_groups: List[List[Transaction]], receipts: Dict[Hash, Dict[str, Any]]
) -> tuple[TransactionPost, FakeEthRPC]:
    """Return the format of `tx_groups` and a node serving `receipts`."""
    return (
        TransactionPost(blocks=tx_groups, post=Alloc()),
        FakeEthRPC(receipts),
    )


def signed_tx(nonce: int, **kwargs: Any) -> Transaction:
    """Return a signed transaction from `SENDER` at `nonce`."""
    return Transaction(
        sender=SENDER, nonce=nonce, gas_limit=100_000, **kwargs
    ).with_signature_and_sender()


def test_cumulative_gas_used_counts_only_the_test_transactions() -> None:
    """Test that the cumulative gas is re-derived from the test's txs."""
    txs = [
        signed_tx(
            0,
            expected_receipt=TransactionReceipt(cumulative_gas_used=21_000),
        ),
        signed_tx(
            1,
            expected_receipt=TransactionReceipt(cumulative_gas_used=51_000),
        ),
    ]
    test, rpc = transaction_post(
        [txs],
        {
            txs[0].hash: receipt_data(gas_used=21_000),
            txs[1].hash: receipt_data(gas_used=30_000),
        },
    )
    test.verify_receipts(rpc, [txs])  # type: ignore[arg-type]
    assert rpc.requests == [txs[0].hash, txs[1].hash]


def test_cumulative_gas_used_resets_every_group() -> None:
    """Test that each declared group restarts the cumulative gas."""
    tx_groups = [
        [
            signed_tx(
                0,
                expected_receipt=TransactionReceipt(
                    cumulative_gas_used=21_000
                ),
            )
        ],
        [
            signed_tx(
                1,
                expected_receipt=TransactionReceipt(
                    cumulative_gas_used=30_000
                ),
            )
        ],
    ]
    test, rpc = transaction_post(
        tx_groups,
        {
            tx_groups[0][0].hash: receipt_data(gas_used=21_000),
            tx_groups[1][0].hash: receipt_data(gas_used=30_000),
        },
    )
    test.verify_receipts(rpc, tx_groups)  # type: ignore[arg-type]


def test_gas_used_mismatch() -> None:
    """Test that a transaction burning the wrong gas is caught."""
    txs = [signed_tx(0, expected_receipt=TransactionReceipt(gas_used=21_000))]
    test, rpc = transaction_post(
        [txs], {txs[0].hash: receipt_data(gas_used=22_000)}
    )
    with pytest.raises(TransactionReceiptMismatchError):
        test.verify_receipts(rpc, [txs])  # type: ignore[arg-type]


def test_status_mismatch() -> None:
    """Test that a transaction that reverted on the network is caught."""
    txs = [signed_tx(0, expected_receipt=TransactionReceipt(status=1))]
    test, rpc = transaction_post(
        [txs],
        {txs[0].hash: {**receipt_data(gas_used=21_000), "status": "0x0"}},
    )
    with pytest.raises(TransactionReceiptMismatchError):
        test.verify_receipts(rpc, [txs])  # type: ignore[arg-type]


def test_log_mismatch() -> None:
    """Test that a log emitted with the wrong data is caught."""
    txs = [
        signed_tx(
            0,
            expected_receipt=TransactionReceipt(
                logs=[TransactionLog(address=EMITTER, data=b"\x01")]
            ),
        )
    ]
    test, rpc = transaction_post(
        [txs],
        {
            txs[0].hash: receipt_data(
                gas_used=21_000,
                logs=[{"address": str(EMITTER), "topics": [], "data": "0x02"}],
            )
        },
    )
    with pytest.raises(LogMismatchError):
        test.verify_receipts(rpc, [txs])  # type: ignore[arg-type]


def test_receipts_fetched_up_to_the_last_expectation() -> None:
    """Test that trailing transactions without expectations are skipped."""
    txs = [
        signed_tx(0),
        signed_tx(
            1,
            expected_receipt=TransactionReceipt(cumulative_gas_used=51_000),
        ),
        signed_tx(2),
    ]
    test, rpc = transaction_post(
        [txs],
        {
            txs[0].hash: receipt_data(gas_used=21_000),
            txs[1].hash: receipt_data(gas_used=30_000),
        },
    )
    test.verify_receipts(rpc, [txs])  # type: ignore[arg-type]
    assert rpc.requests == [txs[0].hash, txs[1].hash]


def test_no_expectations_requests_nothing() -> None:
    """Test that a group without expectations fetches no receipt."""
    txs = [signed_tx(0), signed_tx(1)]
    test, rpc = transaction_post([txs], {})
    test.verify_receipts(rpc, [txs])  # type: ignore[arg-type]
    assert rpc.requests == []
