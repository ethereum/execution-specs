"""
Block Access List Builder for EIP-7928
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This module implements the Block Access List builder that tracks all account and storage
accesses during block execution and constructs the final BlockAccessList.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U32, U64, Uint

from ..fork_types import Address
from ..ssz_types import (
    AccountChanges,
    BalanceChange,
    BlockAccessList,
    CodeChange,
    NonceChange,
    SlotChanges,
    StorageChange,
)


@dataclass
class AccountData:
    """
    Account data stored in the builder.
    """
    storage_changes: Dict[Bytes, List[StorageChange]] = field(default_factory=dict)
    storage_reads: Set[Bytes] = field(default_factory=set)
    balance_changes: List[BalanceChange] = field(default_factory=list)
    nonce_changes: List[NonceChange] = field(default_factory=list)
    code_changes: List[CodeChange] = field(default_factory=list)


@dataclass
class BlockAccessListBuilder:
    """
    Builder for constructing `BlockAccessList` efficiently during transaction
    execution.
    
    The builder accumulates all account and storage accesses during block
    execution and constructs a deterministic access list following the pattern:
    address -> field -> tx_index -> change
    """
    accounts: Dict[Address, AccountData] = field(default_factory=dict)


def ensure_account(builder: BlockAccessListBuilder, address: Address) -> None:
    """
    Ensure account exists in builder.
    
    Creates an empty account entry if it doesn't already exist.
    """
    if address not in builder.accounts:
        builder.accounts[address] = AccountData()


def add_storage_write(
    builder: BlockAccessListBuilder,
    address: Address, 
    slot: Bytes, 
    tx_index: int, 
    new_value: Bytes
) -> None:
    """
    Add storage write to the block access list.
    
    Records a storage slot modification for a given address at a specific
    transaction index.
    """
    ensure_account(builder, address)
    
    if slot not in builder.accounts[address].storage_changes:
        builder.accounts[address].storage_changes[slot] = []
        
    change = StorageChange(tx_index=U32(tx_index), new_value=new_value)
    builder.accounts[address].storage_changes[slot].append(change)


def add_storage_read(
    builder: BlockAccessListBuilder,
    address: Address,
    slot: Bytes
) -> None:
    """
    Add storage read to the block access list.
    
    Records a storage slot read for a given address. Only slots that are
    not also written to will be included in the final access list.
    """
    ensure_account(builder, address)
    builder.accounts[address].storage_reads.add(slot)


def add_balance_change(
    builder: BlockAccessListBuilder,
    address: Address, 
    tx_index: int, 
    post_balance: Bytes
) -> None:
    """
    Add balance change to the block access list.
    
    Records a balance change for a given address at a specific transaction
    index.
    """
    ensure_account(builder, address)
    
    change = BalanceChange(tx_index=U32(tx_index), post_balance=post_balance)
    builder.accounts[address].balance_changes.append(change)


def add_nonce_change(
    builder: BlockAccessListBuilder,
    address: Address, 
    tx_index: int, 
    new_nonce: int
) -> None:
    """
    Add nonce change to the block access list.
    
    Records a nonce change for a given address at a specific transaction
    index.
    """
    ensure_account(builder, address)
    
    change = NonceChange(tx_index=U32(tx_index), new_nonce=U64(new_nonce))
    builder.accounts[address].nonce_changes.append(change)


def add_code_change(
    builder: BlockAccessListBuilder,
    address: Address, 
    tx_index: int, 
    new_code: Bytes
) -> None:
    """
    Add code change to the block access list.
    
    Records a code change for a given address at a specific transaction
    index.
    """
    ensure_account(builder, address)
    
    change = CodeChange(tx_index=U32(tx_index), new_code=new_code)
    builder.accounts[address].code_changes.append(change)


def add_touched_account(builder: BlockAccessListBuilder, address: Address) -> None:
    """
    Add an account that was touched but not changed.
    
    Used for operations like EXTCODEHASH or BALANCE checks that access
    an account without modifying it.
    """
    ensure_account(builder, address)


def build(builder: BlockAccessListBuilder) -> BlockAccessList:
    """
    Build the final BlockAccessList.
    
    Constructs a sorted and deterministic block access list from all
    accumulated changes.
    """
    account_changes_list = []
    
    for address, changes in builder.accounts.items():
        storage_changes = []
        for slot, slot_changes in changes.storage_changes.items():
            sorted_changes = tuple(sorted(slot_changes, key=lambda x: x.tx_index))
            storage_changes.append(SlotChanges(slot=slot, changes=sorted_changes))
        
        storage_reads = []
        for slot in changes.storage_reads:
            if slot not in changes.storage_changes:
                storage_reads.append(slot)
        
        balance_changes = tuple(sorted(changes.balance_changes, key=lambda x: x.tx_index))
        nonce_changes = tuple(sorted(changes.nonce_changes, key=lambda x: x.tx_index))
        code_changes = tuple(sorted(changes.code_changes, key=lambda x: x.tx_index))
        
        storage_changes.sort(key=lambda x: x.slot)
        storage_reads.sort()
        
        account_change = AccountChanges(
            address=address,
            storage_changes=tuple(storage_changes),
            storage_reads=tuple(storage_reads),
            balance_changes=balance_changes,
            nonce_changes=nonce_changes,
            code_changes=code_changes
        )
        
        account_changes_list.append(account_change)
    
    account_changes_list.sort(key=lambda x: x.address)
    
    return BlockAccessList(account_changes=tuple(account_changes_list))