"""Test Erigon fee error mappings across frame transaction encodings."""

import pytest

from execution_testing.client_clis.clis.erigon import ErigonExceptionMapper
from execution_testing.exceptions import TransactionException


@pytest.mark.parametrize(
    "message",
    [
        "fee cap less than block base fee",
        "frame fee budget below base fees",
    ],
)
def test_insufficient_fee(message: str) -> None:
    """Map ordinary fee caps and total frame budgets to the same category."""
    assert ErigonExceptionMapper().message_to_exception(message) == [
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS
    ]


@pytest.mark.parametrize("field", ["FeeCap", "MaxFee"])
def test_frame_fee_overflow(field: str) -> None:
    """Recognize both frame fee field names in the RLP decoder path."""
    message = (
        "rlp: input string too long for *uint256.Int, decoding into "
        f"(types.frameTransactionRLP).Fees.{field}"
    )
    assert ErigonExceptionMapper().message_to_exception(message) == [
        TransactionException.GASPRICE_OVERFLOW
    ]
