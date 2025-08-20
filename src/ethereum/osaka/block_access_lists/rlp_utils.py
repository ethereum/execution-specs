"""
Block Access List RLP Utilities for EIP-7928
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Utilities for working with Block Access Lists using RLP encoding,
as specified in EIP-7928.

This module provides:

- RLP encoding functions for all Block Access List types
- Hash computation using [`keccak256`]
- Validation logic to ensure structural correctness

The encoding follows the RLP specification used throughout Ethereum.

[`keccak256`]: ref:ethereum.crypto.hash.keccak256
"""

from typing import Optional

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import Uint

from ethereum.crypto.hash import Hash32, keccak256

from ..rlp_types import (
    BlockAccessList,
    AccountChanges,
    SlotChanges,
    StorageChange,
    BalanceChange,
    NonceChange,
    CodeChange,
    MAX_TXS,
    MAX_SLOTS,
    MAX_ACCOUNTS,
    MAX_CODE_SIZE,
)


def compute_bal_hash(bal: BlockAccessList) -> Hash32:
    """
    Compute the hash of a Block Access List.
    
    The Block Access List is RLP-encoded and then hashed with keccak256.
    
    Parameters
    ----------
    bal :
        The Block Access List to hash.
        
    Returns
    -------
    hash :
        The keccak256 hash of the RLP-encoded Block Access List.
    """
    bal_bytes = rlp_encode_block_access_list(bal)
    return keccak256(bal_bytes)


def rlp_encode_storage_change(change: StorageChange) -> bytes:
    """
    Encode a [`StorageChange`] as RLP.
    
    Encoded as: [block_access_index, new_value]
    
    Parameters
    ----------
    change :
        The storage change to encode.
    
    Returns
    -------
    encoded :
        The RLP-encoded storage change.
    
    [`StorageChange`]: ref:ethereum.osaka.rlp_types.StorageChange
    """
    return rlp.encode([
        Uint(change.block_access_index),
        change.new_value
    ])


def rlp_encode_balance_change(change: BalanceChange) -> bytes:
    """
    Encode a [`BalanceChange`] as RLP.
    
    Encoded as: [block_access_index, post_balance]
    
    Parameters
    ----------
    change :
        The balance change to encode.
    
    Returns
    -------
    encoded :
        The RLP-encoded balance change.
    
    [`BalanceChange`]: ref:ethereum.osaka.rlp_types.BalanceChange
    """
    return rlp.encode([
        Uint(change.block_access_index),
        change.post_balance
    ])


def rlp_encode_nonce_change(change: NonceChange) -> bytes:
    """
    Encode a [`NonceChange`] as RLP.
    
    Encoded as: [block_access_index, new_nonce]
    
    Parameters
    ----------
    change :
        The nonce change to encode.
    
    Returns
    -------
    encoded :
        The RLP-encoded nonce change.
    
    [`NonceChange`]: ref:ethereum.osaka.rlp_types.NonceChange
    """
    return rlp.encode([
        Uint(change.block_access_index),
        Uint(change.new_nonce)
    ])


def rlp_encode_code_change(change: CodeChange) -> bytes:
    """
    Encode a [`CodeChange`] as RLP.
    
    Encoded as: [block_access_index, new_code]
    
    Parameters
    ----------
    change :
        The code change to encode.
    
    Returns
    -------
    encoded :
        The RLP-encoded code change.
    
    [`CodeChange`]: ref:ethereum.osaka.rlp_types.CodeChange
    """
    return rlp.encode([
        Uint(change.block_access_index),
        change.new_code
    ])


def rlp_encode_slot_changes(slot_changes: SlotChanges) -> bytes:
    """
    Encode [`SlotChanges`] as RLP.
    
    Encoded as: [slot, [changes]]
    
    Parameters
    ----------
    slot_changes :
        The slot changes to encode.
    
    Returns
    -------
    encoded :
        The RLP-encoded slot changes.
    
    [`SlotChanges`]: ref:ethereum.osaka.rlp_types.SlotChanges
    """
    # Encode each change as [block_access_index, new_value]
    changes_list = [
        [Uint(change.block_access_index), change.new_value]
        for change in slot_changes.changes
    ]
    
    return rlp.encode([
        slot_changes.slot,
        changes_list
    ])


def rlp_encode_account_changes(account: AccountChanges) -> bytes:
    """
    Encode [`AccountChanges`] as RLP.
    
    Encoded as: [address, storage_changes, storage_reads, balance_changes, nonce_changes, code_changes]
    
    Parameters
    ----------
    account :
        The account changes to encode.
    
    Returns
    -------
    encoded :
        The RLP-encoded account changes.
    
    [`AccountChanges`]: ref:ethereum.osaka.rlp_types.AccountChanges
    """
    # Encode storage_changes: [[slot, [[block_access_index, new_value], ...]], ...]
    storage_changes_list = [
        [slot_changes.slot, [[Uint(c.block_access_index), c.new_value] for c in slot_changes.changes]]
        for slot_changes in account.storage_changes
    ]
    
    # Encode storage_reads: [slot1, slot2, ...]
    storage_reads_list = list(account.storage_reads)
    
    # Encode balance_changes: [[block_access_index, post_balance], ...]
    balance_changes_list = [
        [Uint(bc.block_access_index), bc.post_balance]
        for bc in account.balance_changes
    ]
    
    # Encode nonce_changes: [[block_access_index, new_nonce], ...]
    nonce_changes_list = [
        [Uint(nc.block_access_index), Uint(nc.new_nonce)]
        for nc in account.nonce_changes
    ]
    
    # Encode code_changes: [[block_access_index, new_code], ...]
    code_changes_list = [
        [Uint(cc.block_access_index), cc.new_code]
        for cc in account.code_changes
    ]
    
    return rlp.encode([
        account.address,
        storage_changes_list,
        storage_reads_list,
        balance_changes_list,
        nonce_changes_list,
        code_changes_list
    ])


def rlp_encode_block_access_list(bal: BlockAccessList) -> Bytes:
    """
    Encode a [`BlockAccessList`] to RLP bytes.
    
    This function produces the final RLP representation of a block's access list,
    following the EIP-7928 specification.
    
    Parameters
    ----------
    bal :
        The block access list to encode.
    
    Returns
    -------
    encoded :
        The complete RLP-encoded block access list.
    
    [`BlockAccessList`]: ref:ethereum.osaka.rlp_types.BlockAccessList
    """
    # Direct RLP encoding of the dataclass
    encoded = rlp.encode(bal)
    return Bytes(encoded)


def validate_bal_against_execution(
    bal: BlockAccessList,
    block_access_list_builder: Optional['BlockAccessListBuilder'] = None
) -> bool:
    """
    Validate that a Block Access List is structurally correct and optionally matches a builder's state.
    
    Parameters
    ----------
    bal :
        The Block Access List to validate.
    block_access_list_builder :
        Optional Block Access List builder to validate against. If provided, checks that the
        Block Access List hash matches what would be built from the builder's current state.
        
    Returns
    -------
    valid :
        True if the Block Access List is structurally valid and matches the builder (if provided).
    """
    # 1. Validate structural constraints
    
    # Check that storage changes and reads don't overlap for the same slot
    for account in bal.account_changes:
        changed_slots = {sc.slot for sc in account.storage_changes}
        read_slots = set(account.storage_reads)
        
        # A slot should not be in both changes and reads (per EIP-7928)
        if changed_slots & read_slots:
            return False
    
    # 2. Validate ordering (addresses should be sorted lexicographically)
    addresses = [account.address for account in bal.account_changes]
    if addresses != sorted(addresses):
        return False
    
    # 3. Validate all data is within bounds
    max_block_access_index = MAX_TXS + 1  # 0 for pre-exec, 1..MAX_TXS for txs, MAX_TXS+1 for post-exec
    for account in bal.account_changes:
        # Validate storage slots are sorted within each account
        storage_slots = [sc.slot for sc in account.storage_changes]
        if storage_slots != sorted(storage_slots):
            return False
            
        # Check storage changes
        for slot_changes in account.storage_changes:
            # Check changes are sorted by block_access_index
            indices = [c.block_access_index for c in slot_changes.changes]
            if indices != sorted(indices):
                return False
                
            for change in slot_changes.changes:
                if change.block_access_index > max_block_access_index:
                    return False
        
        # Check balance changes are sorted by block_access_index
        balance_indices = [bc.block_access_index for bc in account.balance_changes]
        if balance_indices != sorted(balance_indices):
            return False
            
        for balance_change in account.balance_changes:
            if balance_change.block_access_index > max_block_access_index:
                return False
        
        # Check nonce changes are sorted by block_access_index
        nonce_indices = [nc.block_access_index for nc in account.nonce_changes]
        if nonce_indices != sorted(nonce_indices):
            return False
            
        for nonce_change in account.nonce_changes:
            if nonce_change.block_access_index > max_block_access_index:
                return False
        
        # Check code changes are sorted by block_access_index
        code_indices = [cc.block_access_index for cc in account.code_changes]
        if code_indices != sorted(code_indices):
            return False
            
        for code_change in account.code_changes:
            if code_change.block_access_index > max_block_access_index:
                return False
            if len(code_change.new_code) > MAX_CODE_SIZE:
                return False
    
    # 4. If Block Access List builder provided, validate against it by comparing hashes
    if block_access_list_builder is not None:
        from .builder import build
        # Build a Block Access List from the builder
        expected_bal = build(block_access_list_builder)
        
        # Compare hashes
        if compute_bal_hash(bal) != compute_bal_hash(expected_bal):
            return False
    
    return True