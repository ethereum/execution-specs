"""Test Erigon exception mappings."""

import pytest

from execution_testing.client_clis.clis.erigon import ErigonExceptionMapper
from execution_testing.exceptions import TransactionException


@pytest.mark.parametrize(
    "message",
    [
        pytest.param(
            "a blob stx must contain at least one blob", id="rlp-decoding"
        ),
        pytest.param(
            "blob txn must contain at least one blob versioned hash",
            id="execution",
        ),
        pytest.param(
            "[5/5 Execution] invalid block: could not apply tx 1:0 [3:0x"
            "8b1dbd9a4727c24f40a9850245c7dc1fe80835c0d0575b4034b54aea266b0179"
            "]: blob txn must contain at least one blob versioned hash",
            id="engine-validation-error",
        ),
    ],
)
def test_erigon_empty_blob_hashes(message: str) -> None:
    """Recognize empty blob hash lists rejected by decoding or execution."""
    assert ErigonExceptionMapper().message_to_exception(message) == [
        TransactionException.TYPE_3_TX_ZERO_BLOBS
    ]
