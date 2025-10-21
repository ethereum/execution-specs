"""
Pydantic models for fuzzer output format v2.

This module defines Data Transfer Objects (DTOs) for parsing
fuzzer output. These DTOs are intentionally separate from EEST
domain models (Transaction, Account) to maintain clean separation
between external data format and internal representation.

Design Principle:
- DTOs (this file): Parse external JSON-RPC standard format
- Domain Models (EEST): Internal test generation logic
- Converter (converter.py): Explicit transformation between the two
"""

from typing import Dict, List

from pydantic import BaseModel, Field

from ethereum_test_base_types import (
    AccessList,
    Address,
    Bytes,
    CamelModel,
    Hash,
    HexNumber,
)
from ethereum_test_forks import Fork
from ethereum_test_types import Environment


class FuzzerAccountInput(BaseModel):
    """
    Raw account data from fuzzer output.

    This is a DTO that accepts fuzzer's JSON format without triggering
    EEST's Account validation logic or defaults.
    """

    balance: HexNumber
    nonce: HexNumber = HexNumber(0)
    code: Bytes = Bytes(b"")
    storage: Dict[HexNumber, HexNumber] = Field(default_factory=dict)
    private_key: Hash | None = Field(None, alias="privateKey")

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class FuzzerAuthorizationInput(BaseModel):
    """
    Raw authorization tuple from fuzzer output (EIP-7702).

    Accepts fuzzer's camelCase JSON format.
    """

    chain_id: HexNumber = Field(..., alias="chainId")
    address: Address
    nonce: HexNumber
    v: HexNumber  # yParity
    r: HexNumber
    s: HexNumber

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class FuzzerTransactionInput(BaseModel):
    """
    Raw transaction data from fuzzer output.

    This is a DTO that accepts standard Ethereum JSON-RPC transaction format
    without triggering EEST's Transaction.model_post_init logic.

    Key differences from EEST Transaction:
    - Uses "gas" not "gas_limit" (JSON-RPC standard)
    - Uses "data" not "input" (JSON-RPC standard)
    - Uses "from" not "sender" (JSON-RPC standard)
    - No automatic TestAddress injection
    - No automatic transaction type detection
    - No automatic signature handling
    """

    from_: Address = Field(..., alias="from")
    to: Address | None = None
    gas: HexNumber  # Will be mapped to gas_limit in converter
    gas_price: HexNumber | None = Field(None, alias="gasPrice")
    max_fee_per_gas: HexNumber | None = Field(None, alias="maxFeePerGas")
    max_priority_fee_per_gas: HexNumber | None = Field(
        None, alias="maxPriorityFeePerGas"
    )
    nonce: HexNumber
    data: Bytes = Bytes(b"")  # Will be mapped to data/input in converter
    value: HexNumber = HexNumber(0)
    access_list: List[AccessList] | None = Field(None, alias="accessList")
    blob_versioned_hashes: List[Hash] | None = Field(
        None, alias="blobVersionedHashes"
    )
    max_fee_per_blob_gas: HexNumber | None = Field(
        None, alias="maxFeePerBlobGas"
    )
    authorization_list: List[FuzzerAuthorizationInput] | None = Field(
        None, alias="authorizationList"
    )

    class Config:
        """Pydantic configuration."""

        populate_by_name = True


class FuzzerOutput(CamelModel):
    """
    Main fuzzer output format v2.

    This is the top-level DTO that parses the complete fuzzer
    output JSON. It uses pure DTOs (FuzzerAccountInput,
    FuzzerTransactionInput) to avoid triggering EEST domain
    model logic during parsing.

    After parsing, the converter will transform these DTOs into
    EEST domain models.
    """

    version: str = Field(..., pattern="^2\\.0$")
    fork: Fork
    chain_id: HexNumber = Field(HexNumber(1))
    accounts: Dict[Address, FuzzerAccountInput]
    transactions: List[FuzzerTransactionInput]
    env: Environment
    parent_beacon_block_root: Hash | None = None
