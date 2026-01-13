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

    address: Address
    topics: List[Hash]
    data: Bytes
    block_number: HexNumber
    transaction_hash: Hash
    transaction_index: HexNumber
    block_hash: Hash
    log_index: HexNumber
    removed: bool


class ReceiptDelegation(CamelModel):
    """Transaction receipt set-code delegation."""

    from_address: Address = Field(..., alias="from")
    nonce: HexNumber
    target: Address


class TransactionReceipt(CamelModel):
    """Transaction receipt."""

    @model_validator(mode="before")
    @classmethod
    def strip_extra_fields(cls, data: Any) -> Any:
        """Strip extra fields from t8n tool output that are not part of the model."""
        if isinstance(data, dict):
            # t8n tool returns 'succeeded' which is redundant with 'status'
            data.pop("succeeded", None)
            # t8n tool may return 'post_state' which is not part of this model
            data.pop("post_state", None)
            data.pop("postState", None)
            # geth (1.16+) returns extra fields in receipts
            data.pop("type", None)
            data.pop("blockNumber", None)
        return data

    transaction_hash: Hash | None = None
    gas_used: HexNumber | None = None
    root: Bytes | None = None
    status: HexNumber | None = None
    cumulative_gas_used: HexNumber | None = None
    logs_bloom: Bloom | None = Field(
        None, validation_alias=AliasChoices("logs_bloom", "logsBloom", "bloom")
    )
    logs: List[TransactionLog] | None = None
    contract_address: Address | None = None
    effective_gas_price: HexNumber | None = None
    block_hash: Hash | None = None
    transaction_index: HexNumber | None = None
    blob_gas_used: HexNumber | None = None
    blob_gas_price: HexNumber | None = None
    delegations: List[ReceiptDelegation] | None = None
