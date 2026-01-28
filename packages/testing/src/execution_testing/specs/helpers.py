"""Helper functions."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict, List

from execution_testing.client_clis import Result
from execution_testing.exceptions import (
    BlockException,
    ExceptionBase,
    ExceptionWithMessage,
    TransactionException,
    UndefinedException,
)
from execution_testing.test_types import (
    Transaction,
    TransactionLog,
    TransactionReceipt,
)


class ExecutionContext(StrEnum):
    """The execution context in which a test case can fail."""

    BLOCK = "Block"
    TRANSACTION = "Transaction"


class UnexpectedExecutionSuccessError(Exception):
    """
    Exception used when the transaction expected to fail succeeded instead.
    """

    def __init__(
        self, execution_context: ExecutionContext, **kwargs: Any
    ) -> None:
        """Initialize the unexpected success exception."""
        message = (
            f"\nUnexpected success for {execution_context.value} ({kwargs}):"
            f"\n  What: {execution_context.value} unexpectedly succeeded!"
        )
        super().__init__(message)


class UnexpectedExecutionFailError(Exception):
    """
    Exception used when a transaction/block expected to succeed failed instead.
    """

    def __init__(
        self,
        execution_context: ExecutionContext,
        message: str,
        exception: ExceptionWithMessage | UndefinedException,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception."""
        message = (
            f"Unexpected fail for {execution_context.value} ({kwargs}):"
            f"\n   What: {execution_context.value} unexpectedly failed!"
            f'\n  Error: "{message}" ({exception})'
        )
        super().__init__(message)


class UndefinedExecutionExceptionError(Exception):
    """
    Exception used when a client's exception message isn't present in its
    `ExceptionMapper`.
    """

    def __init__(
        self,
        execution_context: ExecutionContext,
        want_exception: ExceptionBase | List[ExceptionBase],
        got_exception: UndefinedException,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception."""
        message = (
            f"Exception mismatch on {execution_context.value} ({kwargs}):"
            f"\n   What: {execution_context.value} exception mismatch!"
            f"\n   Want: {want_exception}"
            f'\n    Got: "{got_exception}"'
            "\n No exception defined for error message got, please add it to "
            f"{got_exception.mapper_name}"
        )
        super().__init__(message)


class ExecutionExceptionMismatchError(Exception):
    """
    Exception used when the actual block/transaction error string differs from
    the expected one.
    """

    def __init__(
        self,
        execution_context: ExecutionContext,
        want_exception: ExceptionBase | List[ExceptionBase],
        got_exception: ExceptionWithMessage,
        got_message: str,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception."""
        message = (
            f"Exception mismatch on {execution_context.value} ({kwargs}):"
            f"\n   What: {execution_context.value} exception mismatch!"
            f"\n   Want: {want_exception}"
            f'\n    Got: "{got_exception}" ("{got_message}")'
        )
        super().__init__(message)


class TransactionReceiptMismatchError(Exception):
    """
    Exception used when the actual transaction receipt differs from the
    expected one.
    """

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


class LogMismatchError(Exception):
    """
    Exception used when an actual log field differs from the expected one.
    """

    def __init__(
        self,
        index: int,
        log_index: int,
        field_name: str,
        expected_value: Any,
        actual_value: Any,
    ):
        """Initialize the exception."""
        message = (
            f"\nLogMismatch (pos={index}, log={log_index}):"
            f"\n   What: {field_name} mismatch!"
            f"\n   Want: {expected_value}"
            f"\n    Got: {actual_value}"
        )
        super().__init__(message)


@dataclass
class ExceptionInfo:
    """Info to print transaction exception error messages."""

    execution_context: ExecutionContext
    want_exception: List[ExceptionBase] | ExceptionBase | None
    got_exception: ExceptionWithMessage | UndefinedException | None
    got_message: str | None
    context: Dict[str, Any]

    def __init__(
        self,
        *,
        execution_context: ExecutionContext,
        want_exception: List[ExceptionBase] | ExceptionBase | None,
        got_exception: ExceptionWithMessage | UndefinedException | None,
        context: Dict[str, Any],
    ):
        """Initialize the exception."""
        self.execution_context = execution_context
        self.want_exception = want_exception
        self.got_exception = got_exception
        if self.got_exception is None:
            self.got_message = None
        else:
            self.got_message = (
                got_exception.message
                if isinstance(got_exception, ExceptionWithMessage)
                else str(got_exception)
            )
        self.context = context

    def verify(self: "ExceptionInfo", *, strict_match: bool) -> None:
        """Verify the exception."""
        want_exception, got_exception = (
            self.want_exception,
            self.got_exception,
        )
        if want_exception and not got_exception:
            raise UnexpectedExecutionSuccessError(
                execution_context=self.execution_context, **self.context
            )
        elif not want_exception and got_exception:
            assert self.got_message is not None
            raise UnexpectedExecutionFailError(
                execution_context=self.execution_context,
                message=self.got_message,
                exception=got_exception,
                **self.context,
            )
        elif want_exception and got_exception:
            if isinstance(got_exception, UndefinedException):
                raise UndefinedExecutionExceptionError(
                    execution_context=self.execution_context,
                    want_exception=want_exception,
                    got_exception=got_exception,
                    **self.context,
                )
            if strict_match:
                if want_exception not in got_exception:
                    got_message = self.got_message
                    assert got_message is not None
                    raise ExecutionExceptionMismatchError(
                        execution_context=self.execution_context,
                        want_exception=want_exception,
                        got_exception=got_exception,
                        got_message=got_message,
                        **self.context,
                    )


class TransactionExceptionInfo(ExceptionInfo):
    """Info to print transaction exception error messages."""

    def __init__(
        self,
        tx: Transaction,
        tx_index: int,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception."""
        super().__init__(
            execution_context=ExecutionContext.TRANSACTION,
            want_exception=tx.error,  # type: ignore
            context={"index": tx_index, "nonce": tx.nonce},
            **kwargs,
        )


class BlockExceptionInfo(ExceptionInfo):
    """Info to print block exception error messages."""

    def __init__(
        self,
        block_number: int,
        **kwargs: Any,
    ) -> None:
        """Initialize the exception."""
        super().__init__(
            execution_context=ExecutionContext.BLOCK,
            context={"number": block_number},
            **kwargs,
        )


def verify_log(
    tx_index: int,
    log_index: int,
    expected: TransactionLog,
    actual: TransactionLog,
) -> None:
    """Verify a single log matches expected values (only specified fields)."""
    if expected.address is not None and expected.address != actual.address:
        raise LogMismatchError(
            index=tx_index,
            log_index=log_index,
            field_name="address",
            expected_value=expected.address,
            actual_value=actual.address,
        )
    if expected.topics is not None and expected.topics != actual.topics:
        raise LogMismatchError(
            index=tx_index,
            log_index=log_index,
            field_name="topics",
            expected_value=expected.topics,
            actual_value=actual.topics,
        )
    if expected.data is not None and expected.data != actual.data:
        raise LogMismatchError(
            index=tx_index,
            log_index=log_index,
            field_name="data",
            expected_value=expected.data,
            actual_value=actual.data,
        )


def verify_transaction_receipt(
    transaction_index: int,
    expected_receipt: TransactionReceipt | None,
    actual_receipt: TransactionReceipt | None,
) -> None:
    """
    Verify the actual receipt against the expected one.

    If the expected receipt is None, validation is skipped.

    Only verifies non-None values in the expected receipt if any.
    """
    if expected_receipt is None:
        return
    assert actual_receipt is not None
    if (
        expected_receipt.cumulative_gas_used is not None
        and actual_receipt.cumulative_gas_used
        != expected_receipt.cumulative_gas_used
    ):
        raise TransactionReceiptMismatchError(
            index=transaction_index,
            field_name="gas_used",
            expected_value=expected_receipt.cumulative_gas_used,
            actual_value=actual_receipt.cumulative_gas_used,
        )
    if expected_receipt.logs is not None and actual_receipt.logs is not None:
        actual_logs = actual_receipt.logs
        expected_logs = expected_receipt.logs
        if len(expected_logs) != len(actual_logs):
            raise LogMismatchError(
                index=transaction_index,
                log_index=0,
                field_name="log_count",
                expected_value=len(expected_logs),
                actual_value=len(actual_logs),
            )
        for log_idx, (expected, actual) in enumerate(
            zip(expected_logs, actual_logs, strict=True)
        ):
            verify_log(transaction_index, log_idx, expected, actual)
    # TODO: Add more fields as needed


def verify_transactions(
    *,
    txs: List[Transaction],
    result: Result,
    transition_tool_exceptions_reliable: bool,
) -> List[int]:
    """
    Verify accepted and rejected (if any) transactions against the expected
    outcome. Raises exception on unexpected rejections, unexpected successful
    txs, or successful txs with unexpected receipt values.
    """
    rejected_txs: Dict[int, ExceptionWithMessage | UndefinedException] = {
        rejected_tx.index: rejected_tx.error
        for rejected_tx in result.rejected_transactions
    }

    receipt_index = 0
    for i, tx in enumerate(txs):
        error_message = rejected_txs[i] if i in rejected_txs else None
        info = TransactionExceptionInfo(
            tx=tx,
            tx_index=i,
            got_exception=error_message,
        )
        info.verify(strict_match=transition_tool_exceptions_reliable)
        if error_message is None:
            verify_transaction_receipt(
                i, tx.expected_receipt, result.receipts[receipt_index]
            )
            receipt_index += 1

    return list(rejected_txs.keys())


def verify_block(
    *,
    block_number: int,
    want_exception: List[TransactionException | BlockException]
    | TransactionException
    | BlockException
    | None,
    got_exception: ExceptionWithMessage | UndefinedException | None,
    transition_tool_exceptions_reliable: bool,
) -> None:
    """Verify the block exception against the expected one."""
    info = BlockExceptionInfo(
        block_number=block_number,
        want_exception=want_exception,
        got_exception=got_exception,
    )
    info.verify(strict_match=transition_tool_exceptions_reliable)
