"""
Block Access List Utilities for EIP-7928
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Utilities for working with Block Access Lists, including hashing and validation.
"""

from typing import Union, Optional
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import Uint

from ethereum.crypto.hash import Hash32, keccak256

from ..ssz_types import (
    BlockAccessList,
    AccountChanges,
    SlotChanges,
    SlotRead,
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
    
    The BAL is SSZ-encoded and then hashed with keccak256.
    
    Parameters
    ----------
    bal :
        The Block Access List to hash.
        
    Returns
    -------
    hash :
        The keccak256 hash of the SSZ-encoded BAL.
    """
    bal_bytes = ssz_encode_block_access_list(bal)
    return keccak256(bal_bytes)


def ssz_encode_uint(value: Union[int, Uint], size: int) -> bytes:
    """Encode an unsigned integer as SSZ (little-endian)."""
    if isinstance(value, Uint):
        value = int(value)
    return value.to_bytes(size, 'little')


def ssz_encode_bytes(data: bytes) -> bytes:
    """Encode fixed-size bytes as SSZ."""
    return data


def ssz_encode_list(items: tuple, encode_item_fn, max_length: int = None) -> bytes:
    """Encode a list/tuple as SSZ with optional max length."""
    # For variable-length lists, we need offset encoding
    # First, encode the list length
    result = bytearray()
    
    # If max_length is specified, this is a variable-length list
    if max_length is not None:
        # Variable-length lists use offset encoding
        # First 4 bytes: offset to start of data
        item_count = len(items)
        if item_count == 0:
            # Empty list is encoded as just the 4-byte offset pointing to itself
            return ssz_encode_uint(4, 4)
        
        # Calculate if items are fixed or variable size
        first_item_encoded = encode_item_fn(items[0]) if items else b''
        is_fixed_size = all(len(encode_item_fn(item)) == len(first_item_encoded) for item in items)
        
        if is_fixed_size:
            # Fixed-size elements: concatenate directly
            for item in items:
                result.extend(encode_item_fn(item))
        else:
            # Variable-size elements: use offset encoding
            # Reserve space for offsets
            offset_start = 4 * item_count
            data_section = bytearray()
            
            for item in items:
                # Write offset
                result.extend(ssz_encode_uint(offset_start + len(data_section), 4))
                # Encode item data
                item_data = encode_item_fn(item)
                data_section.extend(item_data)
            
            result.extend(data_section)
    else:
        # Fixed-length list/tuple: just concatenate
        for item in items:
            result.extend(encode_item_fn(item))
    
    return bytes(result)


def ssz_encode_storage_change(change: StorageChange) -> bytes:
    """Encode a StorageChange as SSZ."""
    result = bytearray()
    result.extend(ssz_encode_uint(change.tx_index, 2))  # TxIndex as uint16
    result.extend(ssz_encode_bytes(change.new_value))   # StorageValue as Bytes32
    return bytes(result)


def ssz_encode_balance_change(change: BalanceChange) -> bytes:
    """Encode a BalanceChange as SSZ."""
    result = bytearray()
    result.extend(ssz_encode_uint(change.tx_index, 2))      # TxIndex as uint16
    result.extend(ssz_encode_uint(change.post_balance, 32)) # Balance as uint256
    return bytes(result)


def ssz_encode_nonce_change(change: NonceChange) -> bytes:
    """Encode a NonceChange as SSZ."""
    result = bytearray()
    result.extend(ssz_encode_uint(change.tx_index, 2))   # TxIndex as uint16
    result.extend(ssz_encode_uint(change.new_nonce, 8))  # Nonce as uint64
    return bytes(result)


def ssz_encode_code_change(change: CodeChange) -> bytes:
    """Encode a CodeChange as SSZ."""
    result = bytearray()
    result.extend(ssz_encode_uint(change.tx_index, 2))  # TxIndex as uint16
    # Code is variable length, so we encode length first for variable-size containers
    code_len = len(change.new_code)
    # In SSZ, variable-length byte arrays are prefixed with their length
    result.extend(ssz_encode_uint(code_len, 4))
    result.extend(change.new_code)
    return bytes(result)


def ssz_encode_slot_changes(slot_changes: SlotChanges) -> bytes:
    """Encode SlotChanges as SSZ."""
    result = bytearray()
    result.extend(ssz_encode_bytes(slot_changes.slot))  # StorageKey as Bytes32
    # Encode the list of changes
    changes_encoded = ssz_encode_list(
        slot_changes.changes,
        ssz_encode_storage_change,
        MAX_TXS  # max length for changes
    )
    result.extend(changes_encoded)
    return bytes(result)


def ssz_encode_slot_read(slot_read: SlotRead) -> bytes:
    """Encode SlotRead as SSZ."""
    return ssz_encode_bytes(slot_read.slot)  # StorageKey as Bytes32


def ssz_encode_account_changes(account: AccountChanges) -> bytes:
    """Encode AccountChanges as SSZ."""
    # For variable-size struct, we use offset encoding
    result = bytearray()
    offsets = []
    data_section = bytearray()
    
    # Fixed-size fields first
    result.extend(ssz_encode_bytes(account.address))  # Address as Bytes20
    
    # Variable-size fields use offsets
    # Calculate base offset (after all fixed fields and offset values)
    base_offset = 20 + (5 * 4)  # address + 5 offset fields
    
    # Encode storage_changes
    storage_changes_data = ssz_encode_list(
        account.storage_changes,
        ssz_encode_slot_changes,
        MAX_SLOTS
    )
    offsets.append(base_offset + len(data_section))
    data_section.extend(storage_changes_data)
    
    # Encode storage_reads
    storage_reads_data = ssz_encode_list(
        account.storage_reads,
        ssz_encode_slot_read,
        MAX_SLOTS
    )
    offsets.append(base_offset + len(data_section))
    data_section.extend(storage_reads_data)
    
    # Encode balance_changes
    balance_changes_data = ssz_encode_list(
        account.balance_changes,
        ssz_encode_balance_change,
        MAX_TXS
    )
    offsets.append(base_offset + len(data_section))
    data_section.extend(balance_changes_data)
    
    # Encode nonce_changes
    nonce_changes_data = ssz_encode_list(
        account.nonce_changes,
        ssz_encode_nonce_change,
        MAX_TXS
    )
    offsets.append(base_offset + len(data_section))
    data_section.extend(nonce_changes_data)
    
    # Encode code_changes
    code_changes_data = ssz_encode_list(
        account.code_changes,
        ssz_encode_code_change,
        MAX_TXS
    )
    offsets.append(base_offset + len(data_section))
    data_section.extend(code_changes_data)
    
    # Write offsets
    for offset in offsets:
        result.extend(ssz_encode_uint(offset, 4))
    
    # Write data section
    result.extend(data_section)
    
    return bytes(result)


def ssz_encode_block_access_list(bal: BlockAccessList) -> Bytes:
    """
    Encode a BlockAccessList to SSZ bytes.
    
    This implements proper SSZ encoding following the Ethereum SSZ specification.
    """
    encoded = ssz_encode_list(
        bal.account_changes,
        ssz_encode_account_changes,
        MAX_ACCOUNTS
    )
    return Bytes(encoded)


def validate_bal_against_execution(
    bal: BlockAccessList,
    block_access_list_builder: Optional['BlockAccessListBuilder'] = None
) -> bool:
    """
    Validate that a BAL is structurally correct and optionally matches a builder's state.
    
    Parameters
    ----------
    bal :
        The Block Access List to validate.
    block_access_list_builder :
        Optional BAL builder to validate against. If provided, checks that the BAL
        hash matches what would be built from the builder's current state.
        
    Returns
    -------
    valid :
        True if the BAL is structurally valid and matches the builder (if provided).
    """
    # 1. Validate structural constraints
    
    # Check that storage changes and reads don't overlap for the same slot
    for account in bal.account_changes:
        changed_slots = {sc.slot for sc in account.storage_changes}
        read_slots = {sr.slot for sr in account.storage_reads}
        
        # A slot should not be in both changes and reads (per EIP-7928)
        if changed_slots & read_slots:
            return False
    
    # 2. Validate ordering (addresses should be sorted lexicographically)
    addresses = [account.address for account in bal.account_changes]
    if addresses != sorted(addresses):
        return False
    
    # 3. Validate all data is within bounds
    max_tx_index = MAX_TXS - 1
    for account in bal.account_changes:
        # Validate storage slots are sorted within each account
        storage_slots = [sc.slot for sc in account.storage_changes]
        if storage_slots != sorted(storage_slots):
            return False
            
        # Check storage changes
        for slot_changes in account.storage_changes:
            # Check changes are sorted by tx_index
            tx_indices = [c.tx_index for c in slot_changes.changes]
            if tx_indices != sorted(tx_indices):
                return False
                
            for change in slot_changes.changes:
                if change.tx_index > max_tx_index:
                    return False
        
        # Check balance changes are sorted by tx_index
        balance_tx_indices = [bc.tx_index for bc in account.balance_changes]
        if balance_tx_indices != sorted(balance_tx_indices):
            return False
            
        for balance_change in account.balance_changes:
            if balance_change.tx_index > max_tx_index:
                return False
        
        # Check nonce changes are sorted by tx_index
        nonce_tx_indices = [nc.tx_index for nc in account.nonce_changes]
        if nonce_tx_indices != sorted(nonce_tx_indices):
            return False
            
        for nonce_change in account.nonce_changes:
            if nonce_change.tx_index > max_tx_index:
                return False
        
        # Check code changes are sorted by tx_index
        code_tx_indices = [cc.tx_index for cc in account.code_changes]
        if code_tx_indices != sorted(code_tx_indices):
            return False
            
        for code_change in account.code_changes:
            if code_change.tx_index > max_tx_index:
                return False
            if len(code_change.new_code) > MAX_CODE_SIZE:
                return False
    
    # 4. If BAL builder provided, validate against it by comparing hashes
    if block_access_list_builder is not None:
        from .builder import build
        # Build a BAL from the builder
        expected_bal = build(block_access_list_builder)
        
        # Compare hashes - much simpler!
        if compute_bal_hash(bal) != compute_bal_hash(expected_bal):
            return False
    
    return True