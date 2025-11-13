"""
Tests for BlockAccessList.validate_structure() method.

These tests verify that the BAL structural validation correctly enforces
EIP-7928 requirements for ordering and uniqueness.
"""

from typing import List, Union

import pytest

from execution_testing.base_types import Address, HexNumber, StorageKey
from execution_testing.test_types.block_access_list import (
    BalAccountChange,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessList,
    BlockAccessListValidationError,
)


def test_bal_address_ordering_validation() -> None:
    """Test that BAL addresses must be in lexicographic order."""
    alice = Address(0xAA)
    bob = Address(0xBB)

    # Correct order: alice < bob
    bal_valid = BlockAccessList(
        [
            BalAccountChange(address=alice),
            BalAccountChange(address=bob),
        ]
    )
    bal_valid.validate_structure()  # Should not raise

    # Incorrect order: bob before alice
    bal_invalid = BlockAccessList(
        [
            BalAccountChange(address=bob),
            BalAccountChange(address=alice),
        ]
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match="addresses are not in lexicographic order",
    ):
        bal_invalid.validate_structure()


def test_bal_storage_slot_ordering() -> None:
    """Test that storage slots must be in ascending order."""
    addr = Address(0xA)

    # Correct order
    bal_valid = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                storage_changes=[
                    BalStorageSlot(slot=StorageKey(0), slot_changes=[]),
                    BalStorageSlot(slot=StorageKey(1), slot_changes=[]),
                    BalStorageSlot(slot=StorageKey(2), slot_changes=[]),
                ],
            )
        ]
    )
    bal_valid.validate_structure()  # Should not raise

    # Incorrect order: slot 2 before slot 1
    bal_invalid = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                storage_changes=[
                    BalStorageSlot(slot=StorageKey(0), slot_changes=[]),
                    BalStorageSlot(slot=StorageKey(2), slot_changes=[]),
                    BalStorageSlot(slot=StorageKey(1), slot_changes=[]),
                ],
            )
        ]
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match="Storage slots not in ascending order",
    ):
        bal_invalid.validate_structure()


def test_bal_storage_reads_ordering() -> None:
    """Test that storage reads must be in ascending order."""
    addr = Address(0xA)

    # Correct order
    bal_valid = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                storage_reads=[StorageKey(0), StorageKey(1), StorageKey(2)],
            )
        ]
    )
    bal_valid.validate_structure()  # Should not raise

    # Incorrect order
    bal_invalid = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                storage_reads=[StorageKey(0), StorageKey(2), StorageKey(1)],
            )
        ]
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match="Storage reads not in ascending order",
    ):
        bal_invalid.validate_structure()


@pytest.mark.parametrize(
    "field_name",
    ["nonce_changes", "balance_changes", "code_changes"],
)
def test_bal_tx_indices_ordering(field_name: str) -> None:
    """
    Test that transaction indices must be in ascending order within change lists.
    """
    addr = Address(0xA)

    changes_valid: List[Union[BalNonceChange, BalBalanceChange, BalCodeChange]]
    changes_invalid: List[
        Union[BalNonceChange, BalBalanceChange, BalCodeChange]
    ]

    # Correct order: tx_index 1, 2, 3
    if field_name == "nonce_changes":
        changes_valid = [
            BalNonceChange(tx_index=HexNumber(1), post_nonce=HexNumber(1)),
            BalNonceChange(tx_index=HexNumber(2), post_nonce=HexNumber(2)),
            BalNonceChange(tx_index=HexNumber(3), post_nonce=HexNumber(3)),
        ]
        changes_invalid = [
            BalNonceChange(tx_index=HexNumber(1), post_nonce=HexNumber(1)),
            BalNonceChange(tx_index=HexNumber(3), post_nonce=HexNumber(3)),
            BalNonceChange(tx_index=HexNumber(2), post_nonce=HexNumber(2)),
        ]
    elif field_name == "balance_changes":
        changes_valid = [
            BalBalanceChange(
                tx_index=HexNumber(1), post_balance=HexNumber(100)
            ),
            BalBalanceChange(
                tx_index=HexNumber(2), post_balance=HexNumber(200)
            ),
            BalBalanceChange(
                tx_index=HexNumber(3), post_balance=HexNumber(300)
            ),
        ]
        changes_invalid = [
            BalBalanceChange(
                tx_index=HexNumber(1), post_balance=HexNumber(100)
            ),
            BalBalanceChange(
                tx_index=HexNumber(3), post_balance=HexNumber(300)
            ),
            BalBalanceChange(
                tx_index=HexNumber(2), post_balance=HexNumber(200)
            ),
        ]
    elif field_name == "code_changes":
        changes_valid = [
            BalCodeChange(tx_index=HexNumber(1), new_code=b"code1"),
            BalCodeChange(tx_index=HexNumber(2), new_code=b"code2"),
            BalCodeChange(tx_index=HexNumber(3), new_code=b"code3"),
        ]
        changes_invalid = [
            BalCodeChange(tx_index=HexNumber(1), new_code=b"code1"),
            BalCodeChange(tx_index=HexNumber(3), new_code=b"code3"),
            BalCodeChange(tx_index=HexNumber(2), new_code=b"code2"),
        ]

    bal_valid = BlockAccessList(
        [BalAccountChange(address=addr, **{field_name: changes_valid})]
    )
    bal_valid.validate_structure()  # Should not raise

    bal_invalid = BlockAccessList(
        [BalAccountChange(address=addr, **{field_name: changes_invalid})]
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match=f"Transaction indices not in ascending order in {field_name}",
    ):
        bal_invalid.validate_structure()


@pytest.mark.parametrize(
    "field_name",
    ["nonce_changes", "balance_changes", "code_changes"],
)
def test_bal_duplicate_tx_indices(field_name: str) -> None:
    """
    Test that BAL must not have duplicate tx indices in change lists.
    """
    addr = Address(0xA)

    changes: List[Union[BalNonceChange, BalBalanceChange, BalCodeChange]]

    # Duplicate tx_index=1
    if field_name == "nonce_changes":
        changes = [
            BalNonceChange(tx_index=HexNumber(1), post_nonce=HexNumber(1)),
            BalNonceChange(
                tx_index=HexNumber(1), post_nonce=HexNumber(2)
            ),  # duplicate tx_index
            BalNonceChange(tx_index=HexNumber(2), post_nonce=HexNumber(3)),
        ]
    elif field_name == "balance_changes":
        changes = [
            BalBalanceChange(
                tx_index=HexNumber(1), post_balance=HexNumber(100)
            ),
            BalBalanceChange(
                tx_index=HexNumber(1), post_balance=HexNumber(200)
            ),  # duplicate tx_index
            BalBalanceChange(
                tx_index=HexNumber(2), post_balance=HexNumber(300)
            ),
        ]
    elif field_name == "code_changes":
        changes = [
            BalCodeChange(tx_index=HexNumber(1), new_code=b"code1"),
            BalCodeChange(
                tx_index=HexNumber(1), new_code=b""
            ),  # duplicate tx_index
            BalCodeChange(tx_index=HexNumber(2), new_code=b"code2"),
        ]

    bal = BlockAccessList(
        [BalAccountChange(address=addr, **{field_name: changes})]
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match=f"Duplicate transaction indices in {field_name}.*Duplicates: \\[1\\]",
    ):
        bal.validate_structure()


def test_bal_storage_duplicate_tx_indices() -> None:
    """
    Test that storage changes must not have duplicate tx indices within same slot.
    """
    addr = Address(0xA)

    # Create storage changes with duplicate tx_index within the same slot
    bal = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                storage_changes=[
                    BalStorageSlot(
                        slot=StorageKey(0),
                        slot_changes=[
                            BalStorageChange(
                                tx_index=HexNumber(1),
                                post_value=StorageKey(100),
                            ),
                            BalStorageChange(
                                tx_index=HexNumber(1),
                                post_value=StorageKey(200),
                            ),  # duplicate tx_index
                            BalStorageChange(
                                tx_index=HexNumber(2),
                                post_value=StorageKey(300),
                            ),
                        ],
                    )
                ],
            )
        ]
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match="Duplicate transaction indices in storage slot.*Duplicates: \\[1\\]",
    ):
        bal.validate_structure()


def test_bal_multiple_violations() -> None:
    """
    Test that validation catches the first violation when multiple exist.
    """
    alice = Address(0xAA)
    bob = Address(0xBB)

    # Wrong address order AND duplicate tx indices
    bal = BlockAccessList(
        [
            BalAccountChange(
                address=bob,  # Should come after alice
                nonce_changes=[
                    BalNonceChange(
                        tx_index=HexNumber(1), post_nonce=HexNumber(1)
                    ),
                    BalNonceChange(
                        tx_index=HexNumber(1), post_nonce=HexNumber(2)
                    ),  # duplicate
                ],
            ),
            BalAccountChange(address=alice),
        ]
    )

    # Should catch the first error (address ordering)
    with pytest.raises(
        BlockAccessListValidationError,
        match="addresses are not in lexicographic order",
    ):
        bal.validate_structure()


def test_bal_empty_list_valid() -> None:
    """Test that an empty BAL is valid."""
    bal = BlockAccessList([])
    bal.validate_structure()  # Should not raise


def test_bal_single_account_valid() -> None:
    """Test that a BAL with a single account is valid."""
    bal = BlockAccessList(
        [
            BalAccountChange(
                address=Address(0xA),
                nonce_changes=[
                    BalNonceChange(
                        tx_index=HexNumber(1), post_nonce=HexNumber(1)
                    )
                ],
            )
        ]
    )
    bal.validate_structure()  # Should not raise
