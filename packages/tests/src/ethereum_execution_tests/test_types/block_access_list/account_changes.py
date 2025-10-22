"""
Account change classes for Block Access List.

This module contains the core data structures representing changes to accounts
in a block access list as defined in EIP-7928.
"""

from typing import ClassVar, List, Union

from pydantic import Field

from ethereum_test_base_types import (
    Address,
    Bytes,
    CamelModel,
    HexNumber,
    RLPSerializable,
    StorageKey,
)


class BalNonceChange(CamelModel, RLPSerializable):
    """Represents a nonce change in the block access list."""

    model_config = CamelModel.model_config | {"extra": "forbid"}

    tx_index: HexNumber = Field(
        HexNumber(1),
        description="Transaction index where the change occurred",
    )
    post_nonce: HexNumber = Field(
        ..., description="Nonce value after the transaction"
    )

    rlp_fields: ClassVar[List[str]] = ["tx_index", "post_nonce"]


class BalBalanceChange(CamelModel, RLPSerializable):
    """Represents a balance change in the block access list."""

    model_config = CamelModel.model_config | {"extra": "forbid"}

    tx_index: HexNumber = Field(
        HexNumber(1),
        description="Transaction index where the change occurred",
    )
    post_balance: HexNumber = Field(
        ..., description="Balance after the transaction"
    )

    rlp_fields: ClassVar[List[str]] = ["tx_index", "post_balance"]


class BalCodeChange(CamelModel, RLPSerializable):
    """Represents a code change in the block access list."""

    model_config = CamelModel.model_config | {"extra": "forbid"}

    tx_index: HexNumber = Field(
        HexNumber(1),
        description="Transaction index where the change occurred",
    )
    new_code: Bytes = Field(..., description="New code bytes")

    rlp_fields: ClassVar[List[str]] = ["tx_index", "new_code"]


class BalStorageChange(CamelModel, RLPSerializable):
    """Represents a change to a specific storage slot."""

    model_config = CamelModel.model_config | {"extra": "forbid"}

    tx_index: HexNumber = Field(
        HexNumber(1),
        description="Transaction index where the change occurred",
    )
    post_value: StorageKey = Field(
        ..., description="Value after the transaction"
    )

    rlp_fields: ClassVar[List[str]] = ["tx_index", "post_value"]


class BalStorageSlot(CamelModel, RLPSerializable):
    """Represents all changes to a specific storage slot."""

    model_config = CamelModel.model_config | {"extra": "forbid"}

    slot: StorageKey = Field(..., description="Storage slot key")
    slot_changes: List[BalStorageChange] = Field(
        default_factory=list, description="List of changes to this slot"
    )

    rlp_fields: ClassVar[List[str]] = ["slot", "slot_changes"]


class BalAccountChange(CamelModel, RLPSerializable):
    """Represents all changes to a specific account in a block."""

    model_config = CamelModel.model_config | {"extra": "forbid"}

    address: Address = Field(..., description="Account address")
    nonce_changes: List[BalNonceChange] = Field(
        default_factory=list, description="List of nonce changes"
    )
    balance_changes: List[BalBalanceChange] = Field(
        default_factory=list, description="List of balance changes"
    )
    code_changes: List[BalCodeChange] = Field(
        default_factory=list, description="List of code changes"
    )
    storage_changes: List[BalStorageSlot] = Field(
        default_factory=list, description="List of storage changes"
    )
    storage_reads: List[StorageKey] = Field(
        default_factory=list,
        description="List of storage slots that were read",
    )

    rlp_fields: ClassVar[List[str]] = [
        "address",
        "storage_changes",
        "storage_reads",
        "balance_changes",
        "nonce_changes",
        "code_changes",
    ]


BlockAccessListChangeLists = Union[
    List[BalNonceChange],
    List[BalBalanceChange],
    List[BalCodeChange],
]


__all__ = [
    "BalNonceChange",
    "BalBalanceChange",
    "BalCodeChange",
    "BalStorageChange",
    "BalStorageSlot",
    "BalAccountChange",
    "BlockAccessListChangeLists",
]
