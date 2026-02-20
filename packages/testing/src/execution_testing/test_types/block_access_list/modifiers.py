"""
BAL modifier functions for invalid test cases.

This module provides modifier functions that can be used to modify Block Access
Lists in various ways for testing invalid block scenarios. They are composable
and can be combined to create complex modifications.
"""

from typing import Any, Callable, List, Optional

from execution_testing.base_types import (
    Address,
    ZeroPaddedHexNumber,
)

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
                f"Some specified addresses were not found in the BAL: "
                f"{missing}"
            )

        return BlockAccessList(root=new_root)

    return transform


def _modify_field_value(
    address: Address,
    block_access_index: int,
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
                                    if (
                                        change.block_access_index
                                        == block_access_index
                                    ):
                                        kwargs = {
                                            "block_access_index": (
                                                block_access_index
                                            ),
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
                            if change.block_access_index == block_access_index:
                                kwargs = {
                                    "block_access_index": block_access_index,
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
    address: Address, block_access_index: int, nonce: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Set an incorrect nonce value for a specific account and transaction."""
    return _modify_field_value(
        address,
        block_access_index,
        "nonce_changes",
        BalNonceChange,
        nonce,
        "post_nonce",
    )


def modify_balance(
    address: Address, block_access_index: int, balance: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """
    Set an incorrect balance value for a specific account and transaction.
    """
    return _modify_field_value(
        address,
        block_access_index,
        "balance_changes",
        BalBalanceChange,
        balance,
        "post_balance",
    )


def modify_storage(
    address: Address, block_access_index: int, slot: int, value: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """
    Set an incorrect storage value for a specific account, transaction, and
    slot.
    """
    return _modify_field_value(
        address,
        block_access_index,
        "storage_changes",
        BalStorageChange,
        value,
        "post_value",
        nested=True,
        slot=slot,
    )


def modify_code(
    address: Address, block_access_index: int, code: bytes
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Set an incorrect code value for a specific account and transaction."""
    return _modify_field_value(
        address,
        block_access_index,
        "code_changes",
        BalCodeChange,
        code,
        "new_code",
    )


def swap_bal_indices(
    idx1: int, idx2: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Swap block access indices throughout the BAL, modifying ordering."""
    nonce_indices = {idx1: False, idx2: False}
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
                    if nonce_change.block_access_index == idx1:
                        nonce_indices[idx1] = True
                        nonce_change.block_access_index = ZeroPaddedHexNumber(
                            idx2
                        )
                    elif nonce_change.block_access_index == idx2:
                        nonce_indices[idx2] = True
                        nonce_change.block_access_index = ZeroPaddedHexNumber(
                            idx1
                        )

            # Swap in balance changes
            if new_account.balance_changes:
                for balance_change in new_account.balance_changes:
                    if balance_change.block_access_index == idx1:
                        balance_indices[idx1] = True
                        balance_change.block_access_index = (
                            ZeroPaddedHexNumber(idx2)
                        )
                    elif balance_change.block_access_index == idx2:
                        balance_indices[idx2] = True
                        balance_change.block_access_index = (
                            ZeroPaddedHexNumber(idx1)
                        )

            # Swap in storage changes (nested structure)
            if new_account.storage_changes:
                for storage_slot in new_account.storage_changes:
                    for storage_change in storage_slot.slot_changes:
                        if storage_change.block_access_index == idx1:
                            storage_indices[idx1] = True
                            storage_change.block_access_index = (
                                ZeroPaddedHexNumber(idx2)
                            )
                        elif storage_change.block_access_index == idx2:
                            storage_indices[idx2] = True
                            storage_change.block_access_index = (
                                ZeroPaddedHexNumber(idx1)
                            )

            # Note: storage_reads is just a list of StorageKey, no
            # block_access_index to swap

            # Swap in code changes
            if new_account.code_changes:
                for code_change in new_account.code_changes:
                    if code_change.block_access_index == idx1:
                        code_indices[idx1] = True
                        code_change.block_access_index = ZeroPaddedHexNumber(
                            idx2
                        )
                    elif code_change.block_access_index == idx2:
                        code_indices[idx2] = True
                        code_change.block_access_index = ZeroPaddedHexNumber(
                            idx1
                        )

            new_root.append(new_account)

        # Validate at least one swap occurred for each index across all
        # change types
        idx1_found = (
            nonce_indices[idx1]
            or balance_indices[idx1]
            or storage_indices[idx1]
            or code_indices[idx1]
        )
        idx2_found = (
            nonce_indices[idx2]
            or balance_indices[idx2]
            or storage_indices[idx2]
            or code_indices[idx2]
        )

        if not idx1_found:
            raise ValueError(
                f"Block access index {idx1} not found in any BAL changes "
                "to swap"
            )
        if not idx2_found:
            raise ValueError(
                f"Block access index {idx2} not found in any BAL changes "
                "to swap"
            )

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


def append_change(
    account: Address,
    change: BalNonceChange | BalBalanceChange | BalCodeChange,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """
    Append a change to an account's field list.

    Generic function to add extraneous entries to nonce_changes,
    balance_changes, or code_changes fields. The field is inferred from the
    change type.
    """
    # Infer field name from change type
    if isinstance(change, BalNonceChange):
        field = "nonce_changes"
    elif isinstance(change, BalBalanceChange):
        field = "balance_changes"
    elif isinstance(change, BalCodeChange):
        field = "code_changes"
    else:
        raise TypeError(f"Unsupported change type: {type(change)}")

    found_address = False

    def transform(bal: BlockAccessList) -> BlockAccessList:
        nonlocal found_address
        new_root = []
        for account_change in bal.root:
            if account_change.address == account:
                found_address = True
                new_account = account_change.model_copy(deep=True)
                # Get the field list and append the change
                field_list = getattr(new_account, field)
                field_list.append(change)
                new_root.append(new_account)
            else:
                new_root.append(account_change)

        if not found_address:
            raise ValueError(
                f"Address {account} not found in BAL to append change to "
                f"{field}"
            )

        return BlockAccessList(root=new_root)

    return transform


def append_storage(
    address: Address,
    slot: int,
    change: Optional[BalStorageChange] = None,
    read: bool = False,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """
    Append storage-related entries to an account.

    Generic function for all storage operations:
    - If read=True: appends to storage_reads
    - If change provided and slot exists: appends to existing slot's
      slot_changes
    - If change provided and slot new: creates new BalStorageSlot
    """
    found_address = False

    def transform(bal: BlockAccessList) -> BlockAccessList:
        nonlocal found_address
        new_root = []
        for account_change in bal.root:
            if account_change.address == address:
                found_address = True
                new_account = account_change.model_copy(deep=True)

                if read:
                    # Append to storage_reads
                    new_account.storage_reads.append(ZeroPaddedHexNumber(slot))
                elif change is not None:
                    # Find if slot already exists
                    slot_found = False
                    for storage_slot in new_account.storage_changes:
                        if storage_slot.slot == slot:
                            # Append to existing slot's slot_changes
                            storage_slot.slot_changes.append(change)
                            slot_found = True
                            break

                    if not slot_found:
                        # Create new BalStorageSlot
                        from . import BalStorageSlot

                        new_storage_slot = BalStorageSlot(
                            slot=slot, slot_changes=[change]
                        )
                        new_account.storage_changes.append(new_storage_slot)

                new_root.append(new_account)
            else:
                new_root.append(account_change)

        if not found_address:
            raise ValueError(
                f"Address {address} not found in BAL to append storage entry"
            )

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


def _duplicate_in_field(
    address: Address,
    field_name: str,
    match_fn: Callable[[Any], bool],
    error_msg: str,
    sub_field: Optional[str] = None,
    sub_match_fn: Optional[Callable[[Any], bool]] = None,
) -> Callable[[BlockAccessList], BlockAccessList]:
    """
    Duplicate the first matching entry in an account's field list.

    When sub_field and sub_match_fn are provided, find the parent entry
    via match_fn then duplicate within sub_field using sub_match_fn.
    """
    found = False

    def _copy(entry: Any) -> Any:
        if hasattr(entry, "model_copy"):
            return entry.model_copy(deep=True)
        return ZeroPaddedHexNumber(entry)

    def transform(bal: BlockAccessList) -> BlockAccessList:
        nonlocal found
        new_root = []
        for account_change in bal.root:
            if account_change.address == address:
                new_account = account_change.model_copy(deep=True)
                entries = getattr(new_account, field_name)

                if sub_field is not None and sub_match_fn is not None:
                    for parent in entries:
                        if match_fn(parent):
                            children = getattr(parent, sub_field)
                            new_children = []
                            for child in children:
                                new_children.append(child)
                                if not found and sub_match_fn(child):
                                    found = True
                                    new_children.append(_copy(child))
                            setattr(parent, sub_field, new_children)
                            break
                else:
                    new_entries = []
                    for entry in entries:
                        new_entries.append(entry)
                        if not found and match_fn(entry):
                            found = True
                            new_entries.append(_copy(entry))
                    setattr(new_account, field_name, new_entries)

                new_root.append(new_account)
            else:
                new_root.append(account_change)

        if not found:
            raise ValueError(error_msg)

        return BlockAccessList(root=new_root)

    return transform


def duplicate_nonce_change(
    address: Address, block_access_index: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Duplicate a nonce change entry for a given block access index."""
    return _duplicate_in_field(
        address,
        "nonce_changes",
        match_fn=lambda c: c.block_access_index == block_access_index,
        error_msg=(
            f"Block access index {block_access_index} not found in "
            f"nonce_changes of account {address}"
        ),
    )


def duplicate_balance_change(
    address: Address, block_access_index: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Duplicate a balance change entry for a given block access index."""
    return _duplicate_in_field(
        address,
        "balance_changes",
        match_fn=lambda c: c.block_access_index == block_access_index,
        error_msg=(
            f"Block access index {block_access_index} not found in "
            f"balance_changes of account {address}"
        ),
    )


def duplicate_code_change(
    address: Address, block_access_index: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Duplicate a code change entry for a given block access index."""
    return _duplicate_in_field(
        address,
        "code_changes",
        match_fn=lambda c: c.block_access_index == block_access_index,
        error_msg=(
            f"Block access index {block_access_index} not found in "
            f"code_changes of account {address}"
        ),
    )


def duplicate_storage_slot(
    address: Address, slot: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Duplicate a storage slot entry in storage_changes."""
    return _duplicate_in_field(
        address,
        "storage_changes",
        match_fn=lambda s: s.slot == slot,
        error_msg=(
            f"Storage slot {slot} not found in storage_changes "
            f"of account {address}"
        ),
    )


def duplicate_storage_read(
    address: Address, slot: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Duplicate a storage read entry."""
    return _duplicate_in_field(
        address,
        "storage_reads",
        match_fn=lambda r: r == slot,
        error_msg=(
            f"Storage slot {slot} not found in storage_reads "
            f"of account {address}"
        ),
    )


def duplicate_slot_change(
    address: Address, slot: int, block_access_index: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """Duplicate a slot change within a specific storage slot."""
    return _duplicate_in_field(
        address,
        "storage_changes",
        match_fn=lambda s: s.slot == slot,
        error_msg=(
            f"Block access index {block_access_index} not found "
            f"in storage slot {slot} of account {address}"
        ),
        sub_field="slot_changes",
        sub_match_fn=lambda c: c.block_access_index == block_access_index,
    )


def insert_storage_read(
    address: Address, slot: int
) -> Callable[[BlockAccessList], BlockAccessList]:
    """
    Insert a storage read at the correct sorted position.

    Useful for testing that a key must not appear in both
    storage_changes and storage_reads.
    """
    found_address = False

    def transform(bal: BlockAccessList) -> BlockAccessList:
        nonlocal found_address
        new_root = []
        for account_change in bal.root:
            if account_change.address == address:
                found_address = True
                new_account = account_change.model_copy(deep=True)
                reads = list(new_account.storage_reads)
                new_slot = ZeroPaddedHexNumber(slot)
                # Find insertion point to maintain sorted order
                insert_idx = len(reads)
                for i, existing in enumerate(reads):
                    if existing >= new_slot:
                        insert_idx = i
                        break
                reads.insert(insert_idx, new_slot)
                new_account.storage_reads = reads
                new_root.append(new_account)
            else:
                new_root.append(account_change)

        if not found_address:
            raise ValueError(
                f"Address {address} not found in BAL to insert storage read"
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
    # Account-level modifiers
    "remove_accounts",
    "append_account",
    "append_change",
    "append_storage",
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
    # Block access index modifiers
    "swap_bal_indices",
    # Duplicate entry modifiers (uniqueness constraint testing)
    "duplicate_nonce_change",
    "duplicate_balance_change",
    "duplicate_code_change",
    "duplicate_storage_slot",
    "duplicate_storage_read",
    "duplicate_slot_change",
    "insert_storage_read",
]
