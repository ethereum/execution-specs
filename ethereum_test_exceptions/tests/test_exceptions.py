"""
Test suite for ethereum_test_exceptions module.
"""

import pytest
from pydantic import TypeAdapter

from ..exceptions import (
    BlockException,
    BlockExceptionInstanceOrList,
    ExceptionInstanceOrList,
    TransactionException,
    TransactionExceptionInstanceOrList,
)

GenericExceptionListAdapter: TypeAdapter = TypeAdapter(ExceptionInstanceOrList)
TransactionExceptionListAdapter: TypeAdapter = TypeAdapter(TransactionExceptionInstanceOrList)
BlockExceptionListAdapter: TypeAdapter = TypeAdapter(BlockExceptionInstanceOrList)


@pytest.mark.parametrize(
    "exception, expected",
    [
        (
            TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS",
        ),
        (
            TransactionException.INITCODE_SIZE_EXCEEDED,
            "TransactionException.INITCODE_SIZE_EXCEEDED",
        ),
        (BlockException.INCORRECT_BLOB_GAS_USED, "BlockException.INCORRECT_BLOB_GAS_USED"),
        (BlockException.INCORRECT_BLOCK_FORMAT, "BlockException.INCORRECT_BLOCK_FORMAT"),
    ],
)
def test_exceptions_string_conversion(
    exception: BlockException | TransactionException, expected: str
):
    """
    Test that the exceptions are unique and have the correct string representation.
    """
    assert str(exception) == expected


@pytest.mark.parametrize(
    "type_adapter,exception,expected",
    [
        (
            GenericExceptionListAdapter,
            [
                BlockException.INCORRECT_BLOB_GAS_USED,
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
            ],
            "BlockException.INCORRECT_BLOB_GAS_USED|"
            "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS",
        ),
        (
            GenericExceptionListAdapter,
            [
                BlockException.INCORRECT_BLOB_GAS_USED,
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                TransactionException.INITCODE_SIZE_EXCEEDED,
            ],
            "BlockException.INCORRECT_BLOB_GAS_USED"
            "|TransactionException.INSUFFICIENT_ACCOUNT_FUNDS"
            "|TransactionException.INITCODE_SIZE_EXCEEDED",
        ),
        (
            GenericExceptionListAdapter,
            [
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                BlockException.INCORRECT_BLOB_GAS_USED,
            ],
            "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS"
            "|BlockException.INCORRECT_BLOB_GAS_USED",
        ),
        (
            TransactionExceptionListAdapter,
            [
                TransactionException.INSUFFICIENT_ACCOUNT_FUNDS,
                TransactionException.INITCODE_SIZE_EXCEEDED,
            ],
            "TransactionException.INSUFFICIENT_ACCOUNT_FUNDS"
            "|TransactionException.INITCODE_SIZE_EXCEEDED",
        ),
        (
            BlockExceptionListAdapter,
            [
                BlockException.INCORRECT_BLOB_GAS_USED,
                BlockException.INCORRECT_BLOCK_FORMAT,
            ],
            "BlockException.INCORRECT_BLOB_GAS_USED|BlockException.INCORRECT_BLOCK_FORMAT",
        ),
    ],
)
def test_exceptions_or(type_adapter: TypeAdapter, exception, expected: str):
    """
    Test that the exceptions can be combined using the | operator.
    """
    assert type_adapter.dump_python(type_adapter.validate_python(exception)) == expected
