"""Helper functions."""

from dataclasses import dataclass
from typing import Any, Dict, List

import pytest

from ethereum_clis import Result
from ethereum_test_exceptions import ExceptionBase, ExceptionMapper, UndefinedException
from ethereum_test_types import Transaction, TransactionReceipt


class TransactionUnexpectedSuccessError(Exception):
    """Exception used when the transaction expected to fail succeeded instead."""

    def __init__(self, index: int, nonce: int):
        """Initialize the exception with the transaction index and nonce."""
        message = (
            f"\nTransactionException (pos={index}, nonce={nonce}):"
            f"\n  What: tx expected to fail succeeded!"
        )
        super().__init__(message)


class TransactionUnexpectedFailError(Exception):
    """Exception used when the transaction expected to succeed failed instead."""

    def __init__(self, index: int, nonce: int, message: str, exception: ExceptionBase):
        """Initialize the exception."""
        message = (
            f"\nTransactionException (pos={index}, nonce={nonce}):"
            f"\n   What: tx unexpectedly failed!"
            f'\n  Error: "{message}" ({exception})'
        )
        super().__init__(message)


class TransactionExceptionMismatchError(Exception):
    """Exception used when the actual transaction error string differs from the expected one."""

    def __init__(
        self,
        index: int,
        nonce: int,
        expected_message: str | None,
        expected_exception: ExceptionBase,
        got_message: str,
        got_exception: ExceptionBase,
        mapper_name: str,
    ):
        """Initialize the exception."""
        define_message_hint = (
            f"No message defined for {expected_exception}, please add it to {mapper_name}"
            if expected_message is None
            else ""
        )
        define_exception_hint = (
            f"No exception defined for error message got, please add it to {mapper_name}"
            if got_exception == UndefinedException.UNDEFINED_EXCEPTION
            else ""
        )
        message = (
            f"\nTransactionException (pos={index}, nonce={nonce}):"
            f"\n   What: exception mismatch!"
            f'\n   Want: "{expected_message}" ({expected_exception})'
            f'\n    Got: "{got_message}" ({got_exception})'
            f"\n {define_message_hint}"
            f"\n {define_exception_hint}"
        )
        super().__init__(message)


class TransactionReceiptMismatchError(Exception):
    """Exception used when the actual transaction receipt differs from the expected one."""

    def __init__(
        self,
        index: int,
        field_name: str,
        expected_value: Any,
        actual_value: Any,
    ):
        """Initialize the exception."""
        message = (
            f"\nTransactionReceiptMismatch (pos={index}):"
            f"\n   What: {field_name} mismatch!"
            f"\n   Want: {expected_value}"
            f"\n    Got: {actual_value}"
        )
        super().__init__(message)


@dataclass
class TransactionExceptionInfo:
    """Info to print transaction exception error messages."""

    t8n_error_message: str | None
    transaction_index: int
    tx: Transaction


def verify_transaction_exception(
    exception_mapper: ExceptionMapper, info: TransactionExceptionInfo
):
    """Verify transaction exception."""
    expected_error: bool = info.tx.error is not None or (
        isinstance(info.tx.error, list) and len(info.tx.error) != 0
    )

    # info.tx.error is expected error code defined in .py test
    if expected_error and not info.t8n_error_message:
        raise TransactionUnexpectedSuccessError(index=info.transaction_index, nonce=info.tx.nonce)
    elif not expected_error and info.t8n_error_message:
        raise TransactionUnexpectedFailError(
            index=info.transaction_index,
            nonce=info.tx.nonce,
            message=info.t8n_error_message,
            exception=exception_mapper.message_to_exception(info.t8n_error_message),
        )
    elif expected_error and info.t8n_error_message:
        if isinstance(info.tx.error, List):
            for expected_exception in info.tx.error:
                expected_error_msg = exception_mapper.exception_to_message(expected_exception)
                if expected_error_msg is None:
                    continue
                if expected_error_msg in info.t8n_error_message:
                    # One of expected exceptions is found in tx error string, no error
                    return

        if isinstance(info.tx.error, List):
            expected_exception = info.tx.error[0]
        elif info.tx.error is None:
            return  # will never happen but removes python logic check
        else:
            expected_exception = info.tx.error

        expected_error_msg = exception_mapper.exception_to_message(expected_exception)
        t8n_error_exception = exception_mapper.message_to_exception(info.t8n_error_message)
        exception_mapper_name = exception_mapper.__class__.__name__

        if expected_error_msg is None or expected_error_msg not in info.t8n_error_message:
            raise TransactionExceptionMismatchError(
                index=info.transaction_index,
                nonce=info.tx.nonce,
                expected_exception=expected_exception,
                expected_message=expected_error_msg,
                got_exception=t8n_error_exception,
                got_message=info.t8n_error_message,
                mapper_name=exception_mapper_name,
            )


def verify_transaction_receipt(
    transaction_index: int,
    expected_receipt: TransactionReceipt | None,
    actual_receipt: TransactionReceipt | None,
):
    """
    Verify the actual receipt against the expected one.

    If the expected receipt is None, validation is skipped.

    Only verifies non-None values in the expected receipt if any.
    """
    if expected_receipt is None:
        return
    assert actual_receipt is not None
    if (
        expected_receipt.gas_used is not None
        and actual_receipt.gas_used != expected_receipt.gas_used
    ):
        raise TransactionReceiptMismatchError(
            index=transaction_index,
            field_name="gas_used",
            expected_value=expected_receipt.gas_used,
            actual_value=actual_receipt.gas_used,
        )
    # TODO: Add more fields as needed


def verify_transactions(
    *,
    txs: List[Transaction],
    exception_mapper: ExceptionMapper,
    result: Result,
) -> List[int]:
    """
    Verify accepted and rejected (if any) transactions against the expected outcome.
    Raises exception on unexpected rejections, unexpected successful txs, or successful txs with
    unexpected receipt values.
    """
    rejected_txs: Dict[int, str] = {
        rejected_tx.index: rejected_tx.error for rejected_tx in result.rejected_transactions
    }

    receipt_index = 0
    for i, tx in enumerate(txs):
        error_message = rejected_txs[i] if i in rejected_txs else None
        info = TransactionExceptionInfo(
            t8n_error_message=error_message, transaction_index=i, tx=tx
        )
        verify_transaction_exception(exception_mapper=exception_mapper, info=info)
        if error_message is None:
            verify_transaction_receipt(i, tx.expected_receipt, result.receipts[receipt_index])
            receipt_index += 1

    return list(rejected_txs.keys())


def is_slow_test(request: pytest.FixtureRequest) -> bool:
    """Check if the test is slow."""
    if hasattr(request, "node"):
        return request.node.get_closest_marker("slow") is not None
    return False
