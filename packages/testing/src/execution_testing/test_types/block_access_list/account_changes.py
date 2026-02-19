"""
Account change classes for Block Access List.

This module contains the core data structures representing changes to accounts
in a block access list as defined in EIP-7928.
"""

from typing import ClassVar, List, Self, Union

from pydantic import Field, model_validator

from execution_testing.base_types import (
    Address,
    Bytes,
    CamelModel,
    RLPSerializable,
    ZeroPaddedHexNumber,
)


class BalNonceChange(CamelModel, RLPSerializable):
    """Represents a nonce change in the block access list."""

    block_access_index: ZeroPaddedHexNumber = Field(
        ZeroPaddedHexNumber(1),
        description="Transaction index where the change occurred",
    )
    post_nonce: ZeroPaddedHexNumber = Field(
        ..., description="Nonce value after the transaction"
    )

    rlp_fields: ClassVar[List[str]] = ["block_access_index", "post_nonce"]


class BalBalanceChange(CamelModel, RLPSerializable):
    """Represents a balance change in the block access list."""

    block_access_index: ZeroPaddedHexNumber = Field(
        ZeroPaddedHexNumber(1),
        description="Transaction index where the change occurred",
    )
    post_balance: ZeroPaddedHexNumber = Field(
        ..., description="Balance after the transaction"
    )

    rlp_fields: ClassVar[List[str]] = ["block_access_index", "post_balance"]


class BalCodeChange(CamelModel, RLPSerializable):
    """Represents a code change in the block access list."""

    block_access_index: ZeroPaddedHexNumber = Field(
        ZeroPaddedHexNumber(1),
        description="Transaction index where the change occurred",
    )
    new_code: Bytes = Field(..., description="New code bytes")

    rlp_fields: ClassVar[List[str]] = ["block_access_index", "new_code"]


class BalStorageChange(CamelModel, RLPSerializable):
    """Represents a change to a specific storage slot."""

    block_access_index: ZeroPaddedHexNumber = Field(
        ZeroPaddedHexNumber(1),
        description="Transaction index where the change occurred",
    )
    post_value: ZeroPaddedHexNumber = Field(
        ..., description="Value after the transaction"
    )

    rlp_fields: ClassVar[List[str]] = ["block_access_index", "post_value"]


class BalStorageSlot(CamelModel, RLPSerializable):
    """Represents all changes to a specific storage slot."""

    slot: ZeroPaddedHexNumber = Field(..., description="Storage slot key")
    slot_changes: List[BalStorageChange] = Field(
        default_factory=list, description="List of changes to this slot"
    )
    validate_any_change: bool = Field(
        default=False,
        description=(
            "If True, asserts at least one change exists in this slot "
            "without validating specific values. Mutually exclusive with "
            "non-empty slot_changes."
        ),
        exclude=True,
    )

    rlp_fields: ClassVar[List[str]] = ["slot", "slot_changes"]

    @model_validator(mode="after")
    def _check_mutual_exclusion(self) -> Self:
        if self.validate_any_change and self.slot_changes:
            raise ValueError(
                "Cannot set both validate_any_change=True and slot_changes. "
                "Use validate_any_change=True to assert at least one change "
                "exists, or slot_changes=[...] to validate specific changes."
            )
        return self


class BalAccountChange(CamelModel, RLPSerializable):
    """Represents all changes to a specific account in a block."""

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
    storage_reads: List[ZeroPaddedHexNumber] = Field(
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
