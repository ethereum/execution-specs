"""Transaction receipt and log types for Ethereum tests."""

from typing import Any, List

from pydantic import AliasChoices, Field, model_validator

from execution_testing.base_types import (
    Address,
    Bloom,
    Bytes,
    CamelModel,
    Hash,
    HexNumber,
)


class TransactionLog(CamelModel):
    """Transaction log."""

    address: Address | None = None
    topics: List[Hash] | None = None
    data: Bytes | None = None
    block_number: HexNumber | None = None
    transaction_hash: Hash | None = None
    transaction_index: HexNumber | None = None
    block_hash: Hash | None = None
    log_index: HexNumber | None = None
    removed: bool | None = None
    block_timestamp: HexNumber | None = None


class ReceiptDelegation(CamelModel):
    """Transaction receipt set-code delegation."""

    from_address: Address = Field(..., alias="from")
    nonce: HexNumber
    target: Address


class FrameReceipt(CamelModel):
    """
    Per-frame receipt of an
    [EIP-8141](https://eips.ethereum.org/EIPS/eip-8141) frame transaction.

    The consensus receipt reports the frame's gas usage as the pair
    `gas_used = [execution, state]`; here the two dimensions are the
    flat `gas_used` and `state_gas_used` fields.
    """

    status: HexNumber | None = None
    gas_used: HexNumber | None = None
    state_gas_used: HexNumber | None = None
    logs: List[TransactionLog] | None = None


class TransactionReceipt(CamelModel):
    """Transaction receipt."""

    @model_validator(mode="before")
    @classmethod
    def strip_extra_fields(cls, data: Any) -> Any:
        """Strip extra fields from t8n tool / RPC output not part of model."""
        if isinstance(data, dict):
            data = dict(data)
            # geth (1.16+) returns extra fields in receipts
            data.pop("type", None)
            data.pop("blockNumber", None)
            # Fields eth_getTransactionReceipt returns that the fixture
            # schema does not model. Fill-stateful fetches receipts live,
            # so we tolerate these even though the t8n path never emits
            # them.
            data.pop("from", None)
            data.pop("to", None)
            root = data.get("root")
            root_is_empty = root in (None, "", "0x", b"", bytearray())
            if not root_is_empty:
                # geth's t8n JSON uses `root` for pre-Byzantium receipts while
                # also populating `status`. For fixture re-encoding, a
                # non-empty root must take precedence over status.
                data.setdefault("post_state", root)
                data.pop("status", None)
        return data

    transaction_hash: Hash | None = None
    post_state: Hash | None = Field(
        None, validation_alias=AliasChoices("post_state", "postState")
    )
    root: Bytes | None = None
    status: HexNumber | None = Field(
        None, validation_alias=AliasChoices("status", "succeeded")
    )
    cumulative_gas_used: HexNumber | None = None
    bloom: Bloom | None = Field(
        None, validation_alias=AliasChoices("logs_bloom", "logsBloom", "bloom")
    )
    logs: List[TransactionLog] | None = None
    gas_used: HexNumber | None = None
    contract_address: Address | None = None
    effective_gas_price: HexNumber | None = None
    block_hash: Hash | None = None
    transaction_index: HexNumber | None = None
    blob_gas_used: HexNumber | None = None
    blob_gas_price: HexNumber | None = None
    delegations: List[ReceiptDelegation] | None = None
    payer: Address | None = None
    frame_receipts: List[FrameReceipt] | None = None


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


class TransactionReceiptIncompleteError(Exception):
    """
    Exception used when the transition tool returns incomplete information
    required to validate the test.
    """

    def __init__(
        self,
        index: int,
        field_name: str,
        expected_value: Any,
    ):
        """Initialize the exception."""
        message = (
            f"\nTransactionReceiptIncomplete (pos={index}):"
            f"\n   What: {field_name} missing!"
            f"\n   Want: {expected_value}"
            f"\n    Got: MISSING"
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
    *,
    transaction_index: int,
    previous_cumulative_gas_used: int | None,
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
            field_name="cumulative_gas_used",
            expected_value=expected_receipt.cumulative_gas_used,
            actual_value=actual_receipt.cumulative_gas_used,
        )
    if expected_receipt.gas_used is not None:
        actual_gas_used: int
        if actual_receipt.gas_used is not None:
            actual_gas_used = actual_receipt.gas_used
        else:
            if previous_cumulative_gas_used is None:
                raise TransactionReceiptIncompleteError(
                    index=transaction_index - 1,
                    field_name="cumulative_gas_used",
                    expected_value=expected_receipt.gas_used,
                )
            current_cumulative_gas_used = actual_receipt.cumulative_gas_used
            if current_cumulative_gas_used is None:
                raise TransactionReceiptIncompleteError(
                    index=transaction_index,
                    field_name="cumulative_gas_used",
                    expected_value=expected_receipt.gas_used,
                )
            actual_gas_used = HexNumber(
                current_cumulative_gas_used - previous_cumulative_gas_used
            )
        if expected_receipt.gas_used != actual_gas_used:
            raise TransactionReceiptMismatchError(
                index=transaction_index,
                field_name="gas_used",
                expected_value=expected_receipt.gas_used,
                actual_value=actual_gas_used,
            )
    if expected_receipt.logs is not None:
        actual_logs = actual_receipt.logs
        if actual_logs is None:
            raise TransactionReceiptIncompleteError(
                index=transaction_index,
                field_name="logs",
                expected_value=expected_receipt.logs,
            )
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
    if expected_receipt.status is not None:
        if actual_receipt.status is None:
            raise TransactionReceiptIncompleteError(
                index=transaction_index,
                field_name="status/succeeded",
                expected_value=expected_receipt.status,
            )
        if expected_receipt.status != actual_receipt.status:
            raise TransactionReceiptMismatchError(
                index=transaction_index,
                field_name="status/succeeded",
                expected_value=expected_receipt.status,
                actual_value=actual_receipt.status,
            )

    # TODO: Add more fields as needed


def verify_frame_transaction_receipt(
    transaction_index: int,
    expected_receipt: TransactionReceipt | None,
    actual_receipt: TransactionReceipt | None,
) -> None:
    """
    Verify the frame-transaction-specific fields of the actual receipt
    against the expected one: the `payer` and the per-frame receipt
    entries defined by [EIP-8141].

    Only called for frame transactions, on top of the generic
    [`verify_transaction_receipt`][vtr] checks. If the expected receipt
    is None, validation is skipped. Only non-None values in the
    expected receipt are verified; within an expected frame receipt
    entry, only its non-None fields are verified.

    [vtr]: ref:execution_testing.test_types.verify_transaction_receipt
    [EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
    """
    if expected_receipt is None:
        return
    assert actual_receipt is not None
    if (
        expected_receipt.payer is not None
        and actual_receipt.payer != expected_receipt.payer
    ):
        raise TransactionReceiptMismatchError(
            index=transaction_index,
            field_name="payer",
            expected_value=expected_receipt.payer,
            actual_value=actual_receipt.payer,
        )

    if expected_receipt.frame_receipts is None:
        return
    actual_frame_receipts = actual_receipt.frame_receipts
    if actual_frame_receipts is None:
        raise TransactionReceiptMismatchError(
            index=transaction_index,
            field_name="frame_receipts",
            expected_value=expected_receipt.frame_receipts,
            actual_value=None,
        )
    if len(expected_receipt.frame_receipts) != len(actual_frame_receipts):
        raise TransactionReceiptMismatchError(
            index=transaction_index,
            field_name="frame_receipt_count",
            expected_value=len(expected_receipt.frame_receipts),
            actual_value=len(actual_frame_receipts),
        )
    for frame_idx, (expected_frame, actual_frame) in enumerate(
        zip(
            expected_receipt.frame_receipts,
            actual_frame_receipts,
            strict=True,
        )
    ):
        if (
            expected_frame.status is not None
            and actual_frame.status != expected_frame.status
        ):
            raise TransactionReceiptMismatchError(
                index=transaction_index,
                field_name=f"frame_receipts[{frame_idx}].status",
                expected_value=expected_frame.status,
                actual_value=actual_frame.status,
            )
        if (
            expected_frame.gas_used is not None
            and actual_frame.gas_used != expected_frame.gas_used
        ):
            raise TransactionReceiptMismatchError(
                index=transaction_index,
                field_name=f"frame_receipts[{frame_idx}].gas_used",
                expected_value=expected_frame.gas_used,
                actual_value=actual_frame.gas_used,
            )
        if (
            expected_frame.state_gas_used is not None
            and actual_frame.state_gas_used != expected_frame.state_gas_used
        ):
            raise TransactionReceiptMismatchError(
                index=transaction_index,
                field_name=f"frame_receipts[{frame_idx}].state_gas_used",
                expected_value=expected_frame.state_gas_used,
                actual_value=actual_frame.state_gas_used,
            )
        if expected_frame.logs is not None:
            actual_frame_logs = actual_frame.logs or []
            if len(expected_frame.logs) != len(actual_frame_logs):
                raise TransactionReceiptMismatchError(
                    index=transaction_index,
                    field_name=f"frame_receipts[{frame_idx}].log_count",
                    expected_value=len(expected_frame.logs),
                    actual_value=len(actual_frame_logs),
                )
            for log_idx, (expected_log, actual_log) in enumerate(
                zip(expected_frame.logs, actual_frame_logs, strict=True)
            ):
                verify_log(
                    transaction_index, log_idx, expected_log, actual_log
                )
