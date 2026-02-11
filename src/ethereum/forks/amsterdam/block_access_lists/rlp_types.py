"""
Defines the RLP data structures for Block-Level Access Lists
as specified in EIP-7928. These structures enable efficient encoding and
decoding of all accounts and storage locations accessed during block execution.

The encoding follows the pattern:
address -> field -> block_access_index -> change.
"""

from dataclasses import dataclass
from typing import List, Tuple, TypeAlias

from ethereum_types.bytes import Bytes
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U16, U64, U256

from ethereum.state import Address

# Type aliases for clarity (matching EIP-7928 specification)
StorageKey: TypeAlias = U256
StorageValue: TypeAlias = U256
CodeData: TypeAlias = Bytes
BlockAccessIndex: TypeAlias = U16
Balance: TypeAlias = U256  # Post-transaction balance in wei
Nonce: TypeAlias = U64


@slotted_freezable
@dataclass
class StorageChange:
    """
    In a [`SlotChanges`][slot], represents a single change in an [`Account`]'s
    storage slot.

    [slot]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.SlotChanges
    [`Account`]: ref:ethereum.state.Account
    """  # noqa: E501

    block_access_index: BlockAccessIndex
    new_value: StorageValue


@slotted_freezable
@dataclass
class BalanceChange:
    """
    In a [`BlockAccessList`][bal], represents a change in an [`Account`]'s
    balance.

    [bal]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.BlockAccessList
    [`Account`]: ref:ethereum.state.Account
    """  # noqa: E501

    block_access_index: BlockAccessIndex
    post_balance: Balance


@slotted_freezable
@dataclass
class NonceChange:
    """
    In a [`BlockAccessList`][bal], represents a change in an [`Account`]'s
    nonce.

    [bal]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.BlockAccessList
    [`Account`]: ref:ethereum.state.Account
    """  # noqa: E501

    block_access_index: BlockAccessIndex
    new_nonce: Nonce


@slotted_freezable
@dataclass
class CodeChange:
    """
    In a [`BlockAccessList`][bal], represents a change in an [`Account`]'s
    code.

    [bal]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.BlockAccessList
    [`Account`]: ref:ethereum.state.Account
    """  # noqa: E501

    block_access_index: BlockAccessIndex
    new_code: CodeData


@slotted_freezable
@dataclass
class SlotChanges:
    """
    In a [`BlockAccessList`][bal], represents a change in an [`Account`]'s
    storage.

    [bal]: ref:ethereum.forks.amsterdam.block_access_lists.rlp_types.BlockAccessList
    [`Account`]: ref:ethereum.state.Account
    """  # noqa: E501

    slot: StorageKey
    changes: Tuple[StorageChange, ...]


@slotted_freezable
@dataclass
class AccountChanges:
    """
    All changes for a single [`Account`], grouped by field type.

    [`Account`]: ref:ethereum.state.Account
    """

    address: Address

    # slot -> [block_access_index -> new_value]
    storage_changes: Tuple[SlotChanges, ...]

    # read-only storage keys
    storage_reads: Tuple[StorageKey, ...]

    # [block_access_index -> post_balance]
    balance_changes: Tuple[BalanceChange, ...]

    # [block_access_index -> new_nonce]
    nonce_changes: Tuple[NonceChange, ...]

    # [block_access_index -> new_code]
    code_changes: Tuple[CodeChange, ...]


BlockAccessList: TypeAlias = List[AccountChanges]
"""
List of state changes recorded across a [`Block`].

[`Block`]: ref:ethereum.forks.amsterdam.blocks.Block
"""
