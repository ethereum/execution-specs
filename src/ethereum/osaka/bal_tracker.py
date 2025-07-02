"""
BAL State Change Tracker for EIP-7928
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This module tracks state changes during transaction execution to build Block Access Lists.
"""

from typing import Dict, Set, Optional

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint

from .fork_types import Address, Account
from .state import State, get_account, get_storage
from .bal_builder import BALBuilder


class StateChangeTracker:
    """
    Tracks state changes during transaction execution for BAL construction.
    """

    def __init__(self, bal_builder: BALBuilder):
        self.bal_builder = bal_builder
        self.pre_storage_cache: Dict[tuple, U256] = {}  # (address, key) -> pre_value
        self.current_tx_index: int = 0

    def set_transaction_index(self, tx_index: int) -> None:
        """Set the current transaction index for tracking changes."""
        self.current_tx_index = tx_index
        # Note: We keep the pre_storage_cache across transactions within the same block
        # as we need it to determine what was the original state before the block
    
    def capture_pre_state(self, address: Address, key: Bytes, state: State) -> U256:
        """Capture and cache the pre-state value for a storage location."""
        cache_key = (address, key)
        if cache_key not in self.pre_storage_cache:
            self.pre_storage_cache[cache_key] = get_storage(state, address, key)
        return self.pre_storage_cache[cache_key]

    def track_address_access(self, address: Address) -> None:
        """Track that an address was accessed (even if not changed)."""
        self.bal_builder.add_touched_account(address)

    def track_storage_read(self, address: Address, key: Bytes, state: State) -> None:
        """Track a storage read operation."""
        self.track_address_access(address)
        
        # Capture pre-state value for potential later comparison
        self.capture_pre_state(address, key, state)
        
        # Add as read (will be filtered out later if this slot is written to)
        self.bal_builder.add_storage_read(address, key)

    def track_storage_write(
        self, 
        address: Address, 
        key: Bytes, 
        new_value: U256, 
        state: State
    ) -> None:
        """Track a storage write operation."""
        self.track_address_access(address)
        
        # Get pre-value to determine if this is actually a change
        pre_value = self.capture_pre_state(address, key, state)
        
        # Convert U256 to 32-byte value
        value_bytes = new_value.to_be_bytes32()
        
        # Only track as write if value actually changed
        if pre_value != new_value:
            self.bal_builder.add_storage_write(address, key, self.current_tx_index, value_bytes)
        else:
            # Unchanged write - track as read instead
            self.bal_builder.add_storage_read(address, key)

    def track_balance_change(
        self, 
        address: Address, 
        new_balance: U256, 
        state: State
    ) -> None:
        """Track a balance change."""
        self.track_address_access(address)
        
        # Convert U256 to 12-byte balance (sufficient for total ETH supply)
        balance_bytes = new_balance.to_be_bytes32()[-12:]  # Take last 12 bytes
        self.bal_builder.add_balance_change(address, self.current_tx_index, balance_bytes)

    def track_nonce_change(
        self, 
        address: Address, 
        new_nonce: Uint, 
        state: State
    ) -> None:
        """Track a nonce change."""
        self.track_address_access(address)
        self.bal_builder.add_nonce_change(address, self.current_tx_index, int(new_nonce))

    def track_code_change(
        self, 
        address: Address, 
        new_code: Bytes, 
        state: State
    ) -> None:
        """Track a code change (contract deployment)."""
        self.track_address_access(address)
        self.bal_builder.add_code_change(address, self.current_tx_index, new_code)

    def finalize_transaction_changes(self, state: State) -> None:
        """
        Finalize changes for the current transaction by comparing with pre-state.
        This method should be called at the end of each transaction.
        """
        # This is where we could perform additional validation or cleanup
        # For now, the tracking is done incrementally during execution
        pass