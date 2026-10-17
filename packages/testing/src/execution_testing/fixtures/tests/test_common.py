"""Tests for the common fixture types."""

from typing import Any, Dict, List

import pytest
from ethereum_rlp import rlp
from ethereum_types.numeric import Uint
from pydantic import ValidationError

from execution_testing.base_types import Bloom
from execution_testing.forks import Amsterdam, Bogota, Fork
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


@pytest.mark.parametrize("fork", [Amsterdam, Bogota])
@pytest.mark.parametrize("tx_type", range(5))
def test_receipt_gas_encoding(fork: Fork, tx_type: int) -> None:
    """Select the on-chain gas field without encoding both RPC fields."""
    tx = Transaction(
        ty=tx_type,
        gas_limit=100_000,
        blob_versioned_hashes=[] if tx_type == 3 else None,
    ).with_signature_and_sender()
    receipt = TransactionReceipt(
        status=1,
        cumulative_gas_used=50_000,
        gas_used=20_000,
        bloom=Bloom(0),
        logs=[],
    )
    fixture_receipt = FixtureTransactionReceipt.from_transaction_receipt(
        receipt, tx, fork=fork
    )
    gas = 20_000 if fork.is_eip_enabled(8116) else 50_000
    prefix = bytes([tx_type]) if tx_type else b""
    assert fixture_receipt.rlp() == prefix + rlp.encode(
        [Uint(1), Uint(gas), bytes(Bloom(0)), []]
    )
    restored = FixtureTransactionReceipt.model_validate_json(
        fixture_receipt.model_dump_json(by_alias=True, exclude_none=True)
    )
    assert restored.rlp() == fixture_receipt.rlp()


@pytest.mark.parametrize(
    "gas_fields", [{}, {"gas_used": 0, "cumulative_gas_used": 0}]
)
def test_receipt_requires_one_gas_field(gas_fields: Dict[str, int]) -> None:
    """Reject ambiguous or missing on-chain gas fields."""
    with pytest.raises(ValidationError, match="exactly one gas field"):
        FixtureTransactionReceipt(
            transaction_hash=0,
            ty=0,
            status=True,
            bloom=Bloom(0),
            logs=[],
            **gas_fields,
        )
