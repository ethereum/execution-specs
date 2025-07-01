"""
Block Access List Builder for EIP-7928
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This module implements the BAL builder that tracks all account and storage
accesses during block execution and constructs the final BlockAccessList.
"""

from collections import defaultdict
from typing import Dict, Set

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U16, U64, Uint

from .fork_types import Address
from .ssz_types import (
    AccountChanges,
    BalanceChange,
    BlockAccessList,
    CodeChange,
    NonceChange,
    SlotChanges,
    SlotRead,
    StorageChange,
)


class BALBuilder:
    """
    Builder for constructing BlockAccessList efficiently during transaction execution.
    
    Follows the pattern: address -> field -> tx_index -> change
    """

    def __init__(self) -> None:
        # address -> field_type -> changes
        self.accounts: Dict[Address, Dict[str, any]] = {}

    def _ensure_account(self, address: Address) -> None:
        """Ensure account exists in builder."""
        if address not in self.accounts:
            self.accounts[address] = {
                'storage_changes': {},  # slot -> [StorageChange]
                'storage_reads': set(),  # set of slots
                'balance_changes': [],  # [BalanceChange]
                'nonce_changes': [],    # [NonceChange]
                'code_changes': [],     # [CodeChange]
            }

    def add_storage_write(
        self, 
        address: Address, 
        slot: Bytes, 
        tx_index: int, 
        new_value: Bytes
    ) -> None:
        """Add storage write: address -> slot -> tx_index -> new_value"""
        self._ensure_account(address)
        
        if slot not in self.accounts[address]['storage_changes']:
            self.accounts[address]['storage_changes'][slot] = []
            
        change = StorageChange(tx_index=U16(tx_index), new_value=new_value)
        self.accounts[address]['storage_changes'][slot].append(change)

    def add_storage_read(self, address: Address, slot: Bytes) -> None:
        """Add storage read: address -> slot (read-only)"""
        self._ensure_account(address)
        self.accounts[address]['storage_reads'].add(slot)

    def add_balance_change(
        self, 
        address: Address, 
        tx_index: int, 
        post_balance: Bytes
    ) -> None:
        """Add balance change: address -> balance -> tx_index -> post_balance"""
        self._ensure_account(address)
        
        change = BalanceChange(tx_index=U16(tx_index), post_balance=post_balance)
        self.accounts[address]['balance_changes'].append(change)

    def add_nonce_change(
        self, 
        address: Address, 
        tx_index: int, 
        new_nonce: int
    ) -> None:
        """Add nonce change: address -> nonce -> tx_index -> new_nonce"""
        self._ensure_account(address)
        
        change = NonceChange(tx_index=U16(tx_index), new_nonce=U64(new_nonce))
        self.accounts[address]['nonce_changes'].append(change)

    def add_code_change(
        self, 
        address: Address, 
        tx_index: int, 
        new_code: Bytes
    ) -> None:
        """Add code change: address -> code -> tx_index -> new_code"""
        self._ensure_account(address)
        
        change = CodeChange(tx_index=U16(tx_index), new_code=new_code)
        self.accounts[address]['code_changes'].append(change)

    def add_touched_account(self, address: Address) -> None:
        """Add an account that was touched but not changed (e.g., EXTCODEHASH, BALANCE checks)"""
        self._ensure_account(address)

    def build(self) -> BlockAccessList:
        """Build the final BlockAccessList."""
        account_changes_list = []
        
        for address, changes in self.accounts.items():
            # Build storage changes
            storage_changes = []
            for slot, slot_changes in changes['storage_changes'].items():
                # Sort changes by tx_index for deterministic encoding
                sorted_changes = tuple(sorted(slot_changes, key=lambda x: x.tx_index))
                storage_changes.append(SlotChanges(slot=slot, changes=sorted_changes))
            
            # Build storage reads (only slots that weren't written to)
            storage_reads = []
            for slot in changes['storage_reads']:
                if slot not in changes['storage_changes']:
                    storage_reads.append(SlotRead(slot=slot))
            
            # Sort all changes by tx_index for deterministic encoding
            balance_changes = tuple(sorted(changes['balance_changes'], key=lambda x: x.tx_index))
            nonce_changes = tuple(sorted(changes['nonce_changes'], key=lambda x: x.tx_index))
            code_changes = tuple(sorted(changes['code_changes'], key=lambda x: x.tx_index))
            
            # Sort storage changes and reads by slot
            storage_changes.sort(key=lambda x: x.slot)
            storage_reads.sort(key=lambda x: x.slot)
            
            # Create account changes object
            account_change = AccountChanges(
                address=address,
                storage_changes=tuple(storage_changes),
                storage_reads=tuple(storage_reads),
                balance_changes=balance_changes,
                nonce_changes=nonce_changes,
                code_changes=code_changes
            )
            
            account_changes_list.append(account_change)
        
        # Sort accounts by address for deterministic encoding
        account_changes_list.sort(key=lambda x: x.address)
        
        return BlockAccessList(account_changes=tuple(account_changes_list))