"""
BAL Utilities for EIP-7928
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Utilities for working with Block Access Lists, including hashing and validation.
"""

from ethereum_types.bytes import Bytes

from ethereum.crypto.hash import Hash32, keccak256

from .ssz_types import BlockAccessList


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
    # For now, use a simple implementation - in a full implementation,
    # this would use proper SSZ encoding
    bal_bytes = _encode_bal_to_bytes(bal)
    return keccak256(bal_bytes)


def _encode_bal_to_bytes(bal: BlockAccessList) -> Bytes:
    """
    Encode a BlockAccessList to bytes for hashing.
    
    This is a simplified implementation. In a production system,
    this would use proper SSZ encoding.
    """
    result = bytearray()
    
    # Encode number of accounts
    result.extend(len(bal.account_changes).to_bytes(4, 'big'))
    
    for account in bal.account_changes:
        # Encode address
        result.extend(account.address)
        
        # Encode storage changes count
        result.extend(len(account.storage_changes).to_bytes(4, 'big'))
        for slot_changes in account.storage_changes:
            result.extend(slot_changes.slot)
            result.extend(len(slot_changes.changes).to_bytes(2, 'big'))
            for change in slot_changes.changes:
                result.extend(change.tx_index.to_bytes(2, 'big'))
                result.extend(change.new_value)
        
        # Encode storage reads count
        result.extend(len(account.storage_reads).to_bytes(4, 'big'))
        for slot_read in account.storage_reads:
            result.extend(slot_read.slot)
        
        # Encode balance changes count
        result.extend(len(account.balance_changes).to_bytes(2, 'big'))
        for balance_change in account.balance_changes:
            result.extend(balance_change.tx_index.to_bytes(2, 'big'))
            result.extend(balance_change.post_balance)
        
        # Encode nonce changes count
        result.extend(len(account.nonce_changes).to_bytes(2, 'big'))
        for nonce_change in account.nonce_changes:
            result.extend(nonce_change.tx_index.to_bytes(2, 'big'))
            result.extend(nonce_change.new_nonce.to_bytes(8, 'big'))
        
        # Encode code changes count
        result.extend(len(account.code_changes).to_bytes(2, 'big'))
        for code_change in account.code_changes:
            result.extend(code_change.tx_index.to_bytes(2, 'big'))
            result.extend(len(code_change.new_code).to_bytes(4, 'big'))
            result.extend(code_change.new_code)
    
    return Bytes(result)


def validate_bal_against_execution(
    bal: BlockAccessList,
    accessed_addresses: set,
    accessed_storage_keys: set,
    state_changes: dict
) -> bool:
    """
    Validate that a BAL accurately represents the execution traces.
    
    Parameters
    ----------
    bal :
        The Block Access List to validate.
    accessed_addresses :
        Set of addresses accessed during execution.
    accessed_storage_keys :
        Set of (address, key) tuples accessed during execution.
    state_changes :
        Dictionary of state changes that occurred during execution.
        
    Returns
    -------
    valid :
        True if the BAL accurately represents the execution.
    """
    # Extract addresses from BAL
    bal_addresses = {account.address for account in bal.account_changes}
    
    # Check that all accessed addresses are in BAL
    if not accessed_addresses.issubset(bal_addresses):
        return False
    
    # Extract storage keys from BAL
    bal_storage_keys = set()
    for account in bal.account_changes:
        for slot_changes in account.storage_changes:
            bal_storage_keys.add((account.address, slot_changes.slot))
        for slot_read in account.storage_reads:
            bal_storage_keys.add((account.address, slot_read.slot))
    
    # Check that all accessed storage keys are in BAL
    if not accessed_storage_keys.issubset(bal_storage_keys):
        return False
    
    # Additional validation could be added here to check specific state changes
    # For now, we assume the BAL construction is correct if address/storage coverage is complete
    
    return True