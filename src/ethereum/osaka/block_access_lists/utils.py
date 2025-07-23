"""
Block Access List Utilities for EIP-7928
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Utilities for working with Block Access Lists, including SSZ encoding,
hashing, and validation functions.

This module provides:

- SSZ encoding functions for all Block Access List types
- Hash computation using [`keccak256`]
- Validation logic to ensure structural correctness

The encoding follows the [SSZ specification] used in Ethereum consensus layer.

[`keccak256`]: ref:ethereum.crypto.hash.keccak256
[SSZ specification]: https://github.com/ethereum/consensus-specs/blob/dev/ssz/simple-serialize.md
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
    MAX_TRANSACTIONS,
    MAX_SLOTS,
    MAX_ACCOUNTS,
    MAX_CODE_SIZE,
)


def compute_bal_hash(bal: BlockAccessList) -> Hash32:
    """
    Compute the hash of a Block Access List.
    
    The Block Access List is SSZ-encoded and then hashed with keccak256.
    
    Parameters
    ----------
    bal :
        The Block Access List to hash.
        
    Returns
    -------
    hash :
        The keccak256 hash of the SSZ-encoded Block Access List.
    """
    bal_bytes = ssz_encode_block_access_list(bal)
    return keccak256(bal_bytes)


def ssz_encode_uint(value: Union[int, Uint], size: int) -> bytes:
    """
    Encode an unsigned integer as SSZ (little-endian).
    
    Parameters
    ----------
    value :
        The integer value to encode.
    size :
        The size in bytes for the encoded output.
    
    Returns
    -------
    encoded :
        The little-endian encoded bytes.
    """
    if isinstance(value, Uint):
        value = int(value)
    return value.to_bytes(size, 'little')


def ssz_encode_bytes(data: bytes) -> bytes:
    """
    Encode fixed-size bytes as SSZ.
    
    For fixed-size byte arrays, SSZ encoding is simply the bytes themselves.
    
    Parameters
    ----------
    data :
        The bytes to encode.
    
    Returns
    -------
    encoded :
        The encoded bytes (unchanged).
    """
    return data


def ssz_encode_list(items: tuple, encode_item_fn, max_length: int = None) -> bytes:
    """
    Encode a list or tuple as SSZ.
    
    Handles both fixed-length and variable-length lists according to the
    [SSZ specification]. Variable-length lists use offset encoding when
    elements have variable size.
    
    Parameters
    ----------
    items :
        The tuple of items to encode.
    encode_item_fn :
        Function to encode individual items.
    max_length :
        Maximum list length (if specified, indicates variable-length list).
    
    Returns
    -------
    encoded :
        The SSZ-encoded list.
    
    [SSZ specification]: https://github.com/ethereum/consensus-specs/blob/dev/ssz/simple-serialize.md
    """
    result = bytearray()
    
    if max_length is None:
        # Fixed-length list/tuple: just concatenate
        for item in items:
            result.extend(encode_item_fn(item))
    else:
        # Variable-length lists use offset encoding
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
    
    return bytes(result)


def ssz_encode_storage_change(change: StorageChange) -> bytes:
    """
    Encode a [`StorageChange`] as SSZ.
    
    Parameters
    ----------
    change :
        The storage change to encode.
    
    Returns
    -------
    encoded :
        The SSZ-encoded storage change.
    
    [`StorageChange`]: ref:ethereum.osaka.ssz_types.StorageChange
    """
    return (
        ssz_encode_uint(change.tx_index, 2)  # TxIndex as uint16
        + ssz_encode_bytes(change.new_value)   # StorageValue as Bytes32
    )


def ssz_encode_balance_change(change: BalanceChange) -> bytes:
    """
    Encode a [`BalanceChange`] as SSZ.
    
    Parameters
    ----------
    change :
        The balance change to encode.
    
    Returns
    -------
    encoded :
        The SSZ-encoded balance change.
    
    [`BalanceChange`]: ref:ethereum.osaka.ssz_types.BalanceChange
    """
    return (
        ssz_encode_uint(change.tx_index, 2)      # TxIndex as uint16
        + ssz_encode_uint(change.post_balance, 32) # Balance as uint256
    )


def ssz_encode_nonce_change(change: NonceChange) -> bytes:
    """
    Encode a [`NonceChange`] as SSZ.
    
    Parameters
    ----------
    change :
        The nonce change to encode.
    
    Returns
    -------
    encoded :
        The SSZ-encoded nonce change.
    
    [`NonceChange`]: ref:ethereum.osaka.ssz_types.NonceChange
    """
    return (
        ssz_encode_uint(change.tx_index, 2)   # TxIndex as uint16
        + ssz_encode_uint(change.new_nonce, 8)  # Nonce as uint64
    )


def ssz_encode_code_change(change: CodeChange) -> bytes:
    """
    Encode a [`CodeChange`] as SSZ.
    
    Code changes use variable-length encoding since contract bytecode
    can vary in size up to [`MAX_CODE_SIZE`].
    
    Parameters
    ----------
    change :
        The code change to encode.
    
    Returns
    -------
    encoded :
        The SSZ-encoded code change.
    
    [`CodeChange`]: ref:ethereum.osaka.ssz_types.CodeChange
    [`MAX_CODE_SIZE`]: ref:ethereum.osaka.ssz_types.MAX_CODE_SIZE
    """
    result = bytearray()
    result.extend(ssz_encode_uint(change.tx_index, 2))  # TxIndex as uint16
    # Code is variable length, so we encode length first for variable-size containers
    code_len = len(change.new_code)
    # In SSZ, variable-length byte arrays are prefixed with their length
    result.extend(ssz_encode_uint(code_len, 4))
    result.extend(change.new_code)
    return bytes(result)


def ssz_encode_slot_changes(slot_changes: SlotChanges) -> bytes:
    """
    Encode [`SlotChanges`] as SSZ.
    
    Encodes a storage slot and all changes made to it during block execution.
    
    Parameters
    ----------
    slot_changes :
        The slot changes to encode.
    
    Returns
    -------
    encoded :
        The SSZ-encoded slot changes.
    
    [`SlotChanges`]: ref:ethereum.osaka.ssz_types.SlotChanges
    """
    result = bytearray()
    result.extend(ssz_encode_bytes(slot_changes.slot))  # StorageKey as Bytes32
    # Encode the list of changes
    changes_encoded = ssz_encode_list(
        slot_changes.changes,
        ssz_encode_storage_change,
        MAX_TRANSACTIONS  # max length for changes
    )
    result.extend(changes_encoded)
    return bytes(result)


def ssz_encode_slot_read(slot_read: SlotRead) -> bytes:
    """
    Encode a [`SlotRead`] as SSZ.
    
    For read-only slots, only the slot key is encoded.
    
    Parameters
    ----------
    slot_read :
        The slot read to encode.
    
    Returns
    -------
    encoded :
        The SSZ-encoded slot read.
    
    [`SlotRead`]: ref:ethereum.osaka.ssz_types.SlotRead
    """
    return ssz_encode_bytes(slot_read.slot)  # StorageKey as Bytes32


def ssz_encode_account_changes(account: AccountChanges) -> bytes:
    """
    Encode [`AccountChanges`] as SSZ.
    
    Encodes all changes for a single account using variable-size struct
    encoding with offsets for the variable-length fields.
    
    Parameters
    ----------
    account :
        The account changes to encode.
    
    Returns
    -------
    encoded :
        The SSZ-encoded account changes.
    
    [`AccountChanges`]: ref:ethereum.osaka.ssz_types.AccountChanges
    """
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
        MAX_TRANSACTIONS
    )
    offsets.append(base_offset + len(data_section))
    data_section.extend(balance_changes_data)
    
    # Encode nonce_changes
    nonce_changes_data = ssz_encode_list(
        account.nonce_changes,
        ssz_encode_nonce_change,
        MAX_TRANSACTIONS
    )
    offsets.append(base_offset + len(data_section))
    data_section.extend(nonce_changes_data)
    
    # Encode code_changes
    code_changes_data = ssz_encode_list(
        account.code_changes,
        ssz_encode_code_change,
        MAX_TRANSACTIONS
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
    Encode a [`BlockAccessList`] to SSZ bytes.
    
    This is the top-level encoding function that produces the final SSZ
    representation of a block's access list, following the [SSZ specification]
    for Ethereum.
    
    Parameters
    ----------
    bal :
        The block access list to encode.
    
    Returns
    -------
    encoded :
        The complete SSZ-encoded block access list.
    
    [`BlockAccessList`]: ref:ethereum.osaka.ssz_types.BlockAccessList
    [SSZ specification]: https://github.com/ethereum/consensus-specs/blob/dev/ssz/simple-serialize.md
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
        read_slots = {sr.slot for sr in account.storage_reads}
        
        # A slot should not be in both changes and reads (per EIP-7928)
        if changed_slots & read_slots:
            return False
    
    # 2. Validate ordering (addresses should be sorted lexicographically)
    addresses = [account.address for account in bal.account_changes]
    if addresses != sorted(addresses):
        return False
    
    # 3. Validate all data is within bounds
    max_tx_index = MAX_TRANSACTIONS - 1
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
    
    # 4. If Block Access List builder provided, validate against it by comparing hashes
    if block_access_list_builder is not None:
        from .builder import build
        # Build a Block Access List from the builder
        expected_bal = build(block_access_list_builder)
        
        # Compare hashes - much simpler!
        if compute_bal_hash(bal) != compute_bal_hash(expected_bal):
            return False
    
    return True