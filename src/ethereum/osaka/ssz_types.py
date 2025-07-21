"""
SSZ Types for EIP-7928 Block-Level Access Lists
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This module defines the SSZ data structures for Block-Level Access Lists (BALs)
as specified in EIP-7928. These structures enable efficient encoding and
decoding of all accounts and storage locations accessed during block execution.
"""

from dataclasses import dataclass
from typing import List, Tuple

from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U256, Uint

# Type aliases for clarity
Address = Bytes20
StorageKey = Bytes32
StorageValue = Bytes32
TxIndex = Uint
Balance = Bytes  # uint128 - Post-transaction balance in wei (16 bytes, sufficient for total ETH supply)
Nonce = Uint

# Constants chosen to support a 630m block gas limit
MAX_TXS = 30_000
MAX_SLOTS = 300_000
MAX_ACCOUNTS = 300_000
MAX_CODE_SIZE = 24_576
MAX_CODE_CHANGES = 1


@slotted_freezable
@dataclass
class StorageChange:
    """Single storage write: tx_index -> new_value"""
    tx_index: TxIndex
    new_value: StorageValue


@slotted_freezable
@dataclass
class BalanceChange:
    """Single balance change: tx_index -> post_balance"""
    tx_index: TxIndex
    post_balance: Balance


@slotted_freezable
@dataclass
class NonceChange:
    """Single nonce change: tx_index -> new_nonce"""
    tx_index: TxIndex
    new_nonce: Nonce


@slotted_freezable
@dataclass
class CodeChange:
    """Single code change: tx_index -> new_code"""
    tx_index: TxIndex
    new_code: Bytes


@slotted_freezable
@dataclass
class SlotChanges:
    """All changes to a single storage slot"""
    slot: StorageKey
    changes: Tuple[StorageChange, ...]




@slotted_freezable
@dataclass
class AccountChanges:
    """
    All changes for a single account, grouped by field type.
    This eliminates address redundancy across different change types.
    """
    address: Address
    storage_changes: Tuple[SlotChanges, ...]
    storage_reads: Tuple[StorageKey, ...]
    balance_changes: Tuple[BalanceChange, ...]
    nonce_changes: Tuple[NonceChange, ...]
    code_changes: Tuple[CodeChange, ...]


@slotted_freezable
@dataclass
class BlockAccessList:
    """
    Block-Level Access List for EIP-7928.
    Contains all addresses accessed during block execution.
    """
    account_changes: Tuple[AccountChanges, ...]