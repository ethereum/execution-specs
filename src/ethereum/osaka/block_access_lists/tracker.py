"""
BAL State Change Tracker for EIP-7928
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This module tracks state changes during transaction execution to build Block Access Lists.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint

from ..fork_types import Address, Account
from ..state import State, get_account, get_storage
from .builder import (
    BlockAccessListBuilder,
    add_balance_change,
    add_code_change,
    add_nonce_change,
    add_storage_read,
    add_storage_write,
    add_touched_account,
)


@dataclass
class StateChangeTracker:
    """
    Tracks state changes during transaction execution for BAL construction.
    """
    block_access_list_builder: BlockAccessListBuilder
    pre_storage_cache: Dict[tuple, U256] = field(default_factory=dict)
    current_tx_index: int = 0


def set_transaction_index(tracker: StateChangeTracker, tx_index: int) -> None:
    """
    Set the current transaction index for tracking changes.
    """
    tracker.current_tx_index = tx_index


def capture_pre_state(
    tracker: StateChangeTracker,
    address: Address,
    key: Bytes,
    state: State
) -> U256:
    """
    Capture and cache the pre-state value for a storage location.
    """
    cache_key = (address, key)
    if cache_key not in tracker.pre_storage_cache:
        tracker.pre_storage_cache[cache_key] = get_storage(state, address, key)
    return tracker.pre_storage_cache[cache_key]


def track_address_access(tracker: StateChangeTracker, address: Address) -> None:
    """
    Track that an address was accessed (even if not changed).
    """
    add_touched_account(tracker.block_access_list_builder, address)


def track_storage_read(
    tracker: StateChangeTracker,
    address: Address,
    key: Bytes,
    state: State
) -> None:
    """
    Track a storage read operation.
    """
    track_address_access(tracker, address)
    
    capture_pre_state(tracker, address, key, state)
    
    add_storage_read(tracker.block_access_list_builder, address, key)


def track_storage_write(
    tracker: StateChangeTracker,
    address: Address, 
    key: Bytes, 
    new_value: U256, 
    state: State
) -> None:
    """
    Track a storage write operation.
    """
    track_address_access(tracker, address)
    
    pre_value = capture_pre_state(tracker, address, key, state)
    
    value_bytes = new_value.to_be_bytes32()
    
    if pre_value != new_value:
        add_storage_write(
            tracker.block_access_list_builder,
            address,
            key,
            tracker.current_tx_index,
            value_bytes
        )
    else:
        add_storage_read(tracker.block_access_list_builder, address, key)


def track_balance_change(
    tracker: StateChangeTracker,
    address: Address, 
    new_balance: U256, 
    state: State
) -> None:
    """
    Track a balance change.
    """
    track_address_access(tracker, address)
    
    balance_bytes = new_balance.to_be_bytes32()[-16:]
    add_balance_change(
        tracker.block_access_list_builder,
        address,
        tracker.current_tx_index,
        balance_bytes
    )


def track_nonce_change(
    tracker: StateChangeTracker,
    address: Address, 
    new_nonce: Uint, 
    state: State
) -> None:
    """
    Track a nonce change.
    """
    track_address_access(tracker, address)
    add_nonce_change(
        tracker.block_access_list_builder,
        address,
        tracker.current_tx_index,
        int(new_nonce)
    )


def track_code_change(
    tracker: StateChangeTracker,
    address: Address, 
    new_code: Bytes, 
    state: State
) -> None:
    """
    Track a code change (contract deployment).
    """
    track_address_access(tracker, address)
    add_code_change(
        tracker.block_access_list_builder,
        address,
        tracker.current_tx_index,
        new_code
    )


def finalize_transaction_changes(
    tracker: StateChangeTracker,
    state: State
) -> None:
    """
    Finalize changes for the current transaction by comparing with pre-state.
    
    This method should be called at the end of each transaction.
    """
    pass