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
    """

    status: HexNumber | None = None
    gas_used: HexNumber | None = None
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
