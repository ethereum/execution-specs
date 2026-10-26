"""Tests for the common fixture types."""

from typing import Any, Dict, List

import pytest

from execution_testing.base_types import Bloom
from execution_testing.test_types.receipt_types import TransactionReceipt
from execution_testing.test_types.transaction_types import Transaction

from ..common import FixtureTransactionReceipt

LOG = {
    "address": "0x" + "11" * 20,
    "topics": ["0x" + "22" * 32],
    "data": "0x3344",
}


@pytest.mark.parametrize(
    "logs,expected_log_count",
    [
        pytest.param(None, 0, id="null_logs"),
        pytest.param([], 0, id="empty_logs"),
        pytest.param([LOG], 1, id="one_log"),
    ],
)
def test_receipt_from_t8n_logs(
    logs: List[Dict[str, Any]] | None, expected_log_count: int
) -> None:
    """Build a fixture receipt from t8n output with null, empty or set logs."""
    receipt = TransactionReceipt.model_validate(
        {
            "status": "0x1",
            "cumulativeGasUsed": "0x5208",
            "logsBloom": Bloom(0),
            "logs": logs,
        }
    )
    fixture_receipt = FixtureTransactionReceipt.from_transaction_receipt(
        receipt, Transaction(gas_limit=21_000).with_signature_and_sender()
    )
    assert len(fixture_receipt.logs) == expected_log_count
