"""
Abstract interface for state oracle implementations.
"""

from typing import Any, Callable, Optional, Protocol

from ethereum_types.bytes import Bytes20, Bytes32

# Use generic types for compatibility across forks
Account = Any
Address = Bytes20


class MerkleOracle(Protocol):
    """
    Oracle interface for Merkle Patricia Trie based state.
    """

    def get_account(
        self, address: Address  # noqa: U100
    ) -> Account:  # noqa: U100
        """
        Get account information for the given address.

        `address` is the account address to retrieve.

        Returns EMPTY_ACCOUNT if the account doesn't exist.
        """

    def get_account_optional(
        self, address: Address  # noqa: U100
    ) -> Optional[Account]:  # noqa: U100
        """
        Get account information for the given address.

        `address` is the account address to retrieve.

        Returns None if the account doesn't exist.
        Use this when you need to distinguish between non-existent and
        empty accounts.
        """

    def get_storage(
        self, address: Address, key: Bytes32  # noqa: U100
    ) -> Bytes32:  # noqa: U100
        """Get storage value at `key` for the given `address`."""

    def state_root(self) -> Bytes32:  # noqa: U100
        """Compute and return the current state root."""

    def get_storage_original(
        self, address: Address, key: Bytes32  # noqa: U100
    ) -> Bytes32:  # noqa: U100
        """
        Get original storage value before current transaction started.

        `address` is the contract address and `key` is the storage slot.

        This is required for SSTORE gas calculations per EIP-2200.
        The implementation should use state snapshots/checkpoints to
        track pre-transaction values.
        TODO: The oracle does not have a `begin_transaction` method,
        TODO: so it kind of breaks here.

        Parameters
        ----------
        address : Bytes20
            Contract address
        key : Bytes32
            Storage slot key

        Returns
        -------
        Bytes32
            Original storage value as 32-byte value
        """

    def set_storage_value(
        self, address: Address, key: Bytes32, value: Any  # noqa: U100
    ) -> None:
        """
        Set individual storage value.

        `address` is the contract address, `key` is the storage slot,
        and `value` is the new storage value.

        Parameters
        ----------
        address : Bytes20
            Contract address
        key : Bytes32
            Storage slot key
        value : Any
            Storage value (U256 or Bytes32)
        """

    def account_has_code_or_nonce(
        self, address: Address  # noqa: U100
    ) -> bool:  # noqa: U100
        """
        Check if account has non-zero code or nonce.

        Used during contract creation to check if address is available.
        """

    def account_has_storage(self, address: Address) -> bool:  # noqa: U100
        """
        Check if account has any storage slots.

        Used during contract creation to check if address is available.
        """

    def is_account_alive(self, address: Address) -> bool:  # noqa: U100
        """
        Check if account is alive (exists and not marked for deletion).

        Used in CALL instructions and SELFDESTRUCT.
        """

    def account_exists(self, address: Address) -> bool:  # noqa: U100
        """
        Check if account exists in the state.
        """

    def increment_nonce(self, address: Address) -> None:  # noqa: U100
        """
        Increment account nonce.

        Used during contract creation and transaction processing.
        """

    def set_code(self, address: Address, code: Any) -> None:  # noqa: U100
        """
        Set account code.

        Used during contract creation and EOA delegation.
        """

    def set_account_balance(
        self, address: Address, balance: Any  # noqa: U100
    ) -> None:  # noqa: U100
        """
        Set account balance.

        Used in SELFDESTRUCT and other balance transfer operations.
        """

    def move_ether(
        self, sender: Bytes20, recipient: Bytes20, amount: Any  # noqa: U100
    ) -> None:
        """
        Transfer ether between accounts.

        Handles balance updates for both sender and recipient accounts.
        Used in CALL instructions and contract transfers.
        """

    def add_created_account(self, address: Address) -> None:  # noqa: U100
        """
        Mark account as created in current transaction.

        Used for tracking accounts created during transaction execution.
        """

    def is_created_account(self, address: Address) -> bool:  # noqa: U100
        """
        Check if account was created in current transaction.

        Used in SELFDESTRUCT and other operations that need to know
        if account was created in current transaction.
        """

    def account_exists_and_is_empty(
        self, address: Address  # noqa: U100
    ) -> bool:  # noqa: U100
        """
        Check if account exists and is empty.

        Used for account cleanup logic.
        """

    def destroy_account(self, address: Address) -> None:  # noqa: U100
        """
        Mark account for destruction.

        Used in SELFDESTRUCT and account cleanup.
        """

    def modify_state(
        self,
        address: Address,  # noqa: U100
        modifier_function: Callable[[Account], None],  # noqa: U100
    ) -> None:
        """
        Modify an account using a modifier function.

        Parameters
        ----------
        address : Address
            Address of account to modify
        modifier_function : Callable[[Account], None]
            Function that takes an account and modifies it in place
        """
