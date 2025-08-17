"""
Memory-based state oracle implementation.

This impl wraps the existing execution-specs `State` object
to provide the oracle interface. 
This is mainly done as a first pass to make the diff small. 
"""

from typing import Any, Optional

from ethereum_types.bytes import Bytes20, Bytes32

# TODO: This file is current Osaka specific -- we could move state.py into here to mitigate this.

# Use generic types for compatibility across forks
Account = Any
Address = Bytes20

from .interface import MerkleOracle


class MemoryMerkleOracle:
    """
    Merkle oracle implementation that wraps existing execution-specs state.
    """

    def __init__(self, state):
        """
        Initialize oracle with existing state.

        Parameters
        ----------
        state : State
            The existing execution-specs state object.
        """
        self._state = state

    def get_account(self, address: Address) -> Account:
        """Get account information for the given address. Returns EMPTY_ACCOUNT if not exists."""
        from ethereum.osaka.state import get_account

        return get_account(self._state, address)

    def get_account_optional(self, address: Address) -> Optional[Account]:
        """Get account information for the given address. Returns None if not exists."""
        from ethereum.osaka.state import get_account_optional

        return get_account_optional(self._state, address)

    def get_storage(self, address: Address, key: Bytes32) -> Bytes32:
        """Get storage value at key for the given address."""
        from ethereum_types.numeric import U256

        from ethereum.osaka.state import get_storage

        # Get storage as U256 and convert to Bytes32
        storage_value = get_storage(self._state, address, key)
        return storage_value.to_be_bytes32()


    def state_root(self) -> Bytes32:
        """Compute and return the current state root."""
        from ethereum.osaka.state import state_root

        return state_root(self._state)

    def get_storage_original(self, address, key):
        """Get original storage value (before transaction started)."""
        from ethereum_types.numeric import U256

        from ethereum.osaka.state import get_storage_original

        storage_value = get_storage_original(self._state, address, key)
        return storage_value.to_be_bytes32()

    def set_storage_value(self, address, key, value):
        """Set a single storage value."""
        from ethereum_types.numeric import U256

        from ethereum.osaka.state import set_storage

        if isinstance(value, bytes):
            storage_value = U256.from_be_bytes(value)
        else:
            storage_value = value
        set_storage(self._state, address, key, storage_value)

    def account_has_code_or_nonce(self, address):
        """Check if account has non-zero code or nonce."""
        from ethereum.osaka.state import account_has_code_or_nonce

        return account_has_code_or_nonce(self._state, address)

    def account_has_storage(self, address):
        """Check if account has any storage slots."""
        from ethereum.osaka.state import account_has_storage

        return account_has_storage(self._state, address)

    def is_account_alive(self, address):
        """Check if account is alive (exists and not marked for deletion)."""
        from ethereum.osaka.state import is_account_alive

        return is_account_alive(self._state, address)

    def account_exists(self, address):
        """Check if account exists in the state."""
        from ethereum.osaka.state import account_exists

        return account_exists(self._state, address)

    def increment_nonce(self, address):
        """Increment account nonce."""
        from ethereum.osaka.state import increment_nonce

        increment_nonce(self._state, address)

    def set_code(self, address, code):
        """Set account code."""
        from ethereum.osaka.state import set_code

        set_code(self._state, address, code)

    def set_account_balance(self, address, balance):
        """Set account balance."""
        from ethereum.osaka.state import set_account_balance

        set_account_balance(self._state, address, balance)

    def move_ether(self, sender, recipient, amount):
        """Transfer ether between accounts."""
        from ethereum.osaka.state import move_ether

        move_ether(self._state, sender, recipient, amount)

    def add_created_account(self, address):
        """Mark account as created in current transaction."""
        # Add to the created_accounts set in state
        self._state.created_accounts.add(address)

    def is_created_account(self, address):
        """Check if account was created in current transaction."""
        return address in self._state.created_accounts

    def account_exists_and_is_empty(self, address):
        """Check if account exists and is empty."""
        from ethereum.osaka.state import account_exists_and_is_empty

        return account_exists_and_is_empty(self._state, address)

    def destroy_account(self, address):
        """Mark account for destruction."""
        from ethereum.osaka.state import destroy_account

        destroy_account(self._state, address)

    def modify_state(self, address, modifier_func):
        """Modify an account using a modifier function."""
        from ethereum.osaka.state import modify_state

        modify_state(self._state, address, modifier_func)

    @property
    def state(self):
        """Access to underlying state for compatibility."""
        return self._state
