"""Transaction receipt and log types for Ethereum tests."""

from typing import List

from pydantic import Field

from ethereum_test_base_types import (
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

    transaction_hash: Hash | None = None
    gas_used: HexNumber | None = None
    root: Bytes | None = None
    status: HexNumber | None = None
    cumulative_gas_used: HexNumber | None = None
    logs_bloom: Bloom | None = None
    logs: List[TransactionLog] | None = None
    contract_address: Address | None = None
    effective_gas_price: HexNumber | None = None
    block_hash: Hash | None = None
    transaction_index: HexNumber | None = None
    blob_gas_used: HexNumber | None = None
    blob_gas_price: HexNumber | None = None
    delegations: List[ReceiptDelegation] | None = None
