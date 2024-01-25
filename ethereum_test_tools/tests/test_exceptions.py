"""
Test suite for ethereum_test_tools.exceptions
"""

from ..exceptions import BlockException, TransactionException


def test_exceptions_string_conversion():
    """
    Test that the exceptions are unique and have the correct string representation.
    """
    assert (
        str(TransactionException.INSUFFICIENT_ACCOUNT_FUNDS)
        == "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS"
    )
    assert str(BlockException.INCORRECT_BLOB_GAS_USED) == "BlockException.INCORRECT_BLOB_GAS_USED"


def test_exceptions_or():
    """
    Test that the exceptions can be combined using the | operator.
    """
    assert (
        str(
            BlockException.INCORRECT_BLOB_GAS_USED
            | TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
        )
        == "BlockException.INCORRECT_BLOB_GAS_USED|TransactionException.INSUFFICIENT_ACCOUNT_FUNDS"
    )

    assert (
        str(
            BlockException.INCORRECT_BLOB_GAS_USED
            | TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
            | TransactionException.INITCODE_SIZE_EXCEEDED
        )
        == "BlockException.INCORRECT_BLOB_GAS_USED"
        "|TransactionException.INSUFFICIENT_ACCOUNT_FUNDS"
        "|TransactionException.INITCODE_SIZE_EXCEEDED"
    )

    assert (
        str(
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
            | BlockException.INCORRECT_BLOB_GAS_USED
        )
        == "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS|BlockException.INCORRECT_BLOB_GAS_USED"
    )

    assert (
        str(
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS
            | BlockException.INCORRECT_BLOB_GAS_USED
            | BlockException.INCORRECT_BLOB_GAS_USED
        )
        == "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS|BlockException.INCORRECT_BLOB_GAS_USED"
    )
