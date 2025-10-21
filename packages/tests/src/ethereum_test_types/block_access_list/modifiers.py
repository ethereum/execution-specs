"""
BAL modifier functions for invalid test cases.

This module provides modifier functions that can be used to modify Block Access
Lists in various ways for testing invalid block scenarios. They are composable
and can be combined to create complex modifications.
"""

from typing import Any, Callable, List, Optional

from ethereum_test_base_types import Address, HexNumber

from .. import BalCodeChange
from . import (
    BalAccountChange,
    BalBalanceChange,
    BalNonceChange,
    BalStorageChange,
    BlockAccessList,
)


def _remove_field_from_accounts(
    addresses: tuple[Address, ...], field_name: str
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Abstracted helper to remove a field from specified accounts."""
    len_addresses = len(addresses)
    found_addresses = set()

    def transform(bal: BlockAccessList) -> BlockAccessList:
        nonlocal found_addresses
        new_root = []
        for account_change in bal.root:
            if account_change.address in addresses:
                found_addresses.add(account_change.address)
                new_account = account_change.model_copy(deep=True)
                # clear the specified field
                setattr(new_account, field_name, [])
                new_root.append(new_account)
            else:
                new_root.append(account_change)

        if len(found_addresses) != len_addresses:
            # sanity check that we found all addresses specified
            missing = set(addresses) - found_addresses
            raise ValueError(
                f"Some specified addresses were not found in the BAL: {missing}"
            )

        return BlockAccessList(root=new_root)

    return transform


def _modify_field_value(
    address: Address,
    tx_index: int,
    field_name: str,
    change_class: type,
    new_value: Any,
    value_field: str = "post_value",
    nested: bool = False,
    slot: Optional[int] = None,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """
    Abstracted helper to modify a field value for a specific account and
    transaction.
    """
    found_address = False

    def transform(bal: BlockAccessList) -> BlockAccessList:
        nonlocal found_address
        new_root = []
        for account_change in bal.root:
            if account_change.address == address:
                found_address = True
                new_account = account_change.model_copy(deep=True)
                changes = getattr(new_account, field_name)

                if changes:
                    if nested and slot is not None:
                        # nested structure (storage)
                        for storage_slot in changes:
                            if storage_slot.slot == slot:
                                for j, change in enumerate(
                                    storage_slot.slot_changes
                                ):
                                    if change.tx_index == tx_index:
                                        kwargs = {
                                            "tx_index": tx_index,
                                            value_field: new_value,
                                        }
                                        storage_slot.slot_changes[j] = (
                                            change_class(**kwargs)
                                        )
                                        break
                                break
                    else:
                        # flat structure (nonce, balance, code)
                        for i, change in enumerate(changes):
                            if change.tx_index == tx_index:
                                kwargs = {
                                    "tx_index": tx_index,
                                    value_field: new_value,
                                }
                                changes[i] = change_class(**kwargs)
                                break

                new_root.append(new_account)
            else:
                new_root.append(account_change)

        if not found_address:
            # sanity check that we actually found the address
            raise ValueError(
                f"Address {address} not found in BAL to modify {field_name}"
            )

        return BlockAccessList(root=new_root)

    return transform


def remove_accounts(
    *addresses: Address,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Remove entire account entries from the BAL."""

    def transform(bal: BlockAccessList) -> BlockAccessList:
        new_root = []
        for account_change in bal.root:
            if account_change.address not in addresses:
                new_root.append(account_change)
        return BlockAccessList(root=new_root)

    return transform


def remove_nonces(
    *addresses: Address,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Remove nonce changes from specified accounts."""
    return _remove_field_from_accounts(addresses, "nonce_changes")


def remove_balances(
    *addresses: Address,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Remove balance changes from specified accounts."""
    return _remove_field_from_accounts(addresses, "balance_changes")


def remove_storage(
    *addresses: Address,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Remove storage changes from specified accounts."""
    return _remove_field_from_accounts(addresses, "storage_changes")


def remove_storage_reads(
    *addresses: Address,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Remove storage reads from specified accounts."""
    return _remove_field_from_accounts(addresses, "storage_reads")


def remove_code(
    *addresses: Address,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Remove code changes from specified accounts."""
    return _remove_field_from_accounts(addresses, "code_changes")


def modify_nonce(
    address: Address, tx_index: int, nonce: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Set an incorrect nonce value for a specific account and transaction."""
    return _modify_field_value(
        address, tx_index, "nonce_changes", BalNonceChange, nonce, "post_nonce"
    )


def modify_balance(
    address: Address, tx_index: int, balance: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """
    Set an incorrect balance value for a specific account and transaction.
    """
    return _modify_field_value(
        address,
        tx_index,
        "balance_changes",
        BalBalanceChange,
        balance,
        "post_balance",
    )


def modify_storage(
    address: Address, tx_index: int, slot: int, value: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """
    Set an incorrect storage value for a specific account, transaction, and
    slot.
    """
    return _modify_field_value(
        address,
        tx_index,
        "storage_changes",
        BalStorageChange,
        value,
        "post_value",
        nested=True,
        slot=slot,
    )


def modify_code(
    address: Address, tx_index: int, code: bytes
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Set an incorrect code value for a specific account and transaction."""
    return _modify_field_value(
        address, tx_index, "code_changes", BalCodeChange, code, "post_code"
    )


def swap_tx_indices(
    tx1: int, tx2: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Swap transaction indices throughout the BAL, modifying tx ordering."""
    nonce_indices = {tx1: False, tx2: False}
    balance_indices = nonce_indices.copy()
    storage_indices = nonce_indices.copy()
    code_indices = nonce_indices.copy()

    def transform(bal: BlockAccessList) -> BlockAccessList:
        nonlocal nonce_indices, balance_indices, storage_indices, code_indices
        new_root = []
        for account_change in bal.root:
            new_account = account_change.model_copy(deep=True)

            # Swap in nonce changes
            if new_account.nonce_changes:
                for nonce_change in new_account.nonce_changes:
                    if nonce_change.tx_index == tx1:
                        nonce_indices[tx1] = True
                        nonce_change.tx_index = HexNumber(tx2)
                    elif nonce_change.tx_index == tx2:
                        nonce_indices[tx2] = True
                        nonce_change.tx_index = HexNumber(tx1)

            # Swap in balance changes
            if new_account.balance_changes:
                for balance_change in new_account.balance_changes:
                    if balance_change.tx_index == tx1:
                        balance_indices[tx1] = True
                        balance_change.tx_index = HexNumber(tx2)
                    elif balance_change.tx_index == tx2:
                        balance_indices[tx2] = True
                        balance_change.tx_index = HexNumber(tx1)

            # Swap in storage changes (nested structure)
            if new_account.storage_changes:
                for storage_slot in new_account.storage_changes:
                    for storage_change in storage_slot.slot_changes:
                        if storage_change.tx_index == tx1:
                            balance_indices[tx1] = True
                            storage_change.tx_index = HexNumber(tx2)
                        elif storage_change.tx_index == tx2:
                            balance_indices[tx2] = True
                            storage_change.tx_index = HexNumber(tx1)

            # Note: storage_reads is just a list of StorageKey, no tx_index to
            # swap

            # Swap in code changes
            if new_account.code_changes:
                for code_change in new_account.code_changes:
                    if code_change.tx_index == tx1:
                        code_indices[tx1] = True
                        code_change.tx_index = HexNumber(tx2)
                    elif code_change.tx_index == tx2:
                        code_indices[tx2] = True
                        code_change.tx_index = HexNumber(tx1)

            new_root.append(new_account)

        return BlockAccessList(root=new_root)

    return transform


def append_account(
    account_change: BalAccountChange,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Append an account to account changes."""

    def transform(bal: BlockAccessList) -> BlockAccessList:
        new_root = list(bal.root)
        new_root.append(account_change)
        return BlockAccessList(root=new_root)

    return transform


def duplicate_account(
    address: Address,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Duplicate an account entry in the BAL."""
    address_present = False

    def transform(bal: BlockAccessList) -> BlockAccessList:
        nonlocal address_present
        new_root = []
        for account_change in bal.root:
            new_root.append(account_change)
            if account_change.address == address:
                # Add duplicate immediately after
                new_root.append(account_change.model_copy(deep=True))
                address_present = True

        if not address_present:
            # sanity check that we actually duplicate
            raise ValueError(
                f"Address {address} not found in BAL to duplicate"
            )

        return BlockAccessList(root=new_root)

    return transform


def reverse_accounts() -> Callable[[BlockAccessList], BlockAccessList]:
    """Reverse the order of accounts in the BAL."""

    def transform(bal: BlockAccessList) -> BlockAccessList:
        return BlockAccessList(root=list(reversed(bal.root)))

    return transform


def sort_accounts_by_address() -> Callable[[BlockAccessList], BlockAccessList]:
    """Sort accounts by address (may modify expected ordering)."""

    def transform(bal: BlockAccessList) -> BlockAccessList:
        sorted_root = sorted(bal.root, key=lambda x: x.address)
        return BlockAccessList(root=sorted_root)

    return transform


def reorder_accounts(
    indices: List[int],
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Reorder accounts according to the provided index list."""

    def transform(bal: BlockAccessList) -> BlockAccessList:
        if len(indices) != len(bal.root):
            raise ValueError("Index list length must match number of accounts")
        new_root = [bal.root[i] for i in indices]
        return BlockAccessList(root=new_root)

    return transform


def clear_all() -> Callable[[BlockAccessList], BlockAccessList]:
    """Return an empty BAL."""

    def transform(bal: BlockAccessList) -> BlockAccessList:
        del bal
        return BlockAccessList(root=[])

    return transform


def keep_only(
    *addresses: Address,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Keep only the specified accounts, removing all others."""
    len_addresses = len(addresses)

    def transform(bal: BlockAccessList) -> BlockAccessList:
        new_root = []
        for account_change in bal.root:
            if account_change.address in addresses:
                new_root.append(account_change)

        if len(new_root) != len_addresses:
            # sanity check that we found all specified addresses
            raise ValueError(
                "Some specified addresses were not found in the BAL"
            )

        return BlockAccessList(root=new_root)

    return transform


__all__ = [
    # Core functions
    # Account-level modifiers
    "remove_accounts",
    "append_account",
    "duplicate_account",
    "reverse_accounts",
    "keep_only",
    # Field-level modifiers
    "remove_nonces",
    "remove_balances",
    "remove_storage",
    "remove_storage_reads",
    "remove_code",
    # Value modifiers
    "modify_nonce",
    "modify_balance",
    "modify_storage",
    "modify_code",
    # Transaction index modifiers
    "swap_tx_indices",
]
