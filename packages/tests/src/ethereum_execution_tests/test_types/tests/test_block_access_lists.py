"""Unit tests for BlockAccessListExpectation validation."""

from typing import Any

import pytest

from ethereum_test_base_types import Address, StorageKey
from ethereum_test_types.block_access_list import (
    BalAccountAbsentValues,
    BalAccountChange,
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessList,
    BlockAccessListExpectation,
    BlockAccessListValidationError,
)


def test_address_exclusion_validation_passes() -> None:
    """Test that address exclusion works when address is not in BAL."""
    alice = Address(0xA)
    bob = Address(0xB)

    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=alice,
                nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
            ),
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            alice: BalAccountExpectation(
                nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)]
            ),
            bob: None,  # expect Bob is not in BAL (correctly)
        }
    )

    expectation.verify_against(actual_bal)


def test_address_exclusion_validation_raises_when_address_is_present() -> None:
    """Test that validation fails when excluded address is in BAL."""
    alice = Address(0xA)
    bob = Address(0xB)

    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=alice,
                nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
            ),
            BalAccountChange(
                address=bob,
                balance_changes=[
                    BalBalanceChange(tx_index=1, post_balance=100)
                ],
            ),
        ]
    )

    expectation = BlockAccessListExpectation(
        # explicitly expect Bob to NOT be in BAL (wrongly)
        account_expectations={bob: None},
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match="should not be in BAL but was found",
    ):
        expectation.verify_against(actual_bal)


@pytest.mark.parametrize(
    "empty_changes_definition,exception_message",
    [
        [
            BalAccountExpectation(),
            "ambiguous. Use BalAccountExpectation.empty()",
        ],
        [BalAccountExpectation.empty(), "No account changes expected for "],
    ],
    ids=["BalAccountExpectation()", "BalAccountExpectation.empty()"],
)
def test_empty_account_changes_definitions(
    empty_changes_definition: Any,
    exception_message: str,
) -> None:
    """
    Test that validation fails when expected empty changes but actual
    has changes.
    """
    alice = Address(0xA)

    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=alice,
                nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
            ),
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={alice: empty_changes_definition}
    )

    with pytest.raises(
        BlockAccessListValidationError, match=exception_message
    ):
        expectation.verify_against(actual_bal)


def test_empty_list_validation() -> None:
    """Test that empty list validates correctly."""
    alice = Address(0xA)

    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=alice,
                nonce_changes=[],
                balance_changes=[],
                code_changes=[],
                storage_changes=[],
                storage_reads=[],
            ),
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            alice: BalAccountExpectation(
                nonce_changes=[],
                balance_changes=[],
                code_changes=[],
                storage_changes=[],
                storage_reads=[],
            ),
        }
    )

    expectation.verify_against(actual_bal)


@pytest.mark.parametrize(
    "field,value",
    [
        ["nonce_changes", BalNonceChange(tx_index=1, post_nonce=1)],
        ["balance_changes", BalBalanceChange(tx_index=1, post_balance=100)],
        ["code_changes", BalCodeChange(tx_index=1, new_code=b"code")],
        [
            "storage_changes",
            BalStorageSlot(
                slot=0x01,
                slot_changes=[BalStorageChange(tx_index=1, post_value=0x42)],
            ),
        ],
        ["storage_reads", 0x01],
    ],
)
def test_empty_list_validation_fails(field: str, value: Any) -> None:
    """Test that validation fails when expecting empty but field has values."""
    alice = Address(0xA)

    alice_acct_change = BalAccountChange(
        address=alice,
        storage_reads=[0x02],
    )

    if field == "storage_reads":
        alice_acct_change.storage_reads = [value]
        # set another field to non-empty to avoid all-empty account change
        alice_acct_change.nonce_changes = [
            BalNonceChange(tx_index=1, post_nonce=1)
        ]

    else:
        setattr(alice_acct_change, field, [value])
    actual_bal = BlockAccessList([alice_acct_change])

    alice_acct_expectation = BalAccountExpectation(
        storage_reads=[0x02],
    )
    if field == "storage_reads":
        alice_acct_expectation.storage_reads = []
        # match the filled field in actual to avoid all-empty
        # account expectation
        alice_acct_expectation.nonce_changes = [
            BalNonceChange(tx_index=1, post_nonce=1)
        ]
    else:
        setattr(alice_acct_expectation, field, [])

    expectation = BlockAccessListExpectation(
        account_expectations={alice: alice_acct_expectation}
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match=f"Expected {field} to be empty",
    ):
        expectation.verify_against(actual_bal)


def test_partial_validation() -> None:
    """Test that unset fields are not validated."""
    alice = Address(0xA)

    # Actual BAL has multiple types of changes
    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=alice,
                nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                balance_changes=[
                    BalBalanceChange(tx_index=1, post_balance=100)
                ],
                storage_reads=[0x01, 0x02],
            ),
        ]
    )

    # Only validate nonce changes, ignore balance and storage
    expectation = BlockAccessListExpectation(
        account_expectations={
            alice: BalAccountExpectation(
                nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
                # balance_changes and storage_reads not set and won't be
                # validated
            ),
        }
    )

    expectation.verify_against(actual_bal)


def test_storage_changes_validation() -> None:
    """Test storage changes validation."""
    contract = Address(0xC)

    # Actual BAL with storage changes
    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=contract,
                storage_changes=[
                    BalStorageSlot(
                        slot=0x01,
                        slot_changes=[
                            BalStorageChange(tx_index=1, post_value=0x42)
                        ],
                    )
                ],
            ),
        ]
    )

    # Expect the same storage changes
    expectation = BlockAccessListExpectation(
        account_expectations={
            contract: BalAccountExpectation(
                storage_changes=[
                    BalStorageSlot(
                        slot=0x01,
                        slot_changes=[
                            BalStorageChange(tx_index=1, post_value=0x42)
                        ],
                    )
                ],
            ),
        }
    )

    expectation.verify_against(actual_bal)


def test_missing_expected_address() -> None:
    """Test that validation fails when expected address is missing."""
    alice = Address(0xA)
    bob = Address(0xB)

    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=alice,
                nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
            ),
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            # wrongly expect Bob to be present
            bob: BalAccountExpectation(
                nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
            ),
        }
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match="Expected address .* not found in actual BAL",
    ):
        expectation.verify_against(actual_bal)


@pytest.mark.parametrize(
    "addresses,error_message",
    [
        (
            [
                Address(0xB),
                Address(0xA),  # should come first
            ],
            "BAL addresses are not in lexicographic order",
        ),
        (
            [
                Address(0x1),
                Address(0x3),
                Address(0x2),
            ],
            "BAL addresses are not in lexicographic order",
        ),
    ],
)
def test_actual_bal_address_ordering_validation(
    addresses: Any, error_message: str
) -> None:
    """Test that actual BAL must have addresses in lexicographic order."""
    # Create BAL with addresses in the given order
    actual_bal = BlockAccessList(
        [
            BalAccountChange(address=addr, nonce_changes=[])
            for addr in addresses
        ]
    )

    expectation = BlockAccessListExpectation(account_expectations={})

    with pytest.raises(BlockAccessListValidationError, match=error_message):
        expectation.verify_against(actual_bal)


@pytest.mark.parametrize(
    "storage_slots,error_message",
    [
        (
            [StorageKey(0x02), StorageKey(0x01)],  # 0x02 before 0x01
            "Storage slots not in ascending order",
        ),
        (
            [StorageKey(0x01), StorageKey(0x03), StorageKey(0x02)],
            "Storage slots not in ascending order",
        ),
    ],
)
def test_actual_bal_storage_slot_ordering(
    storage_slots: Any, error_message: str
) -> None:
    """Test that actual BAL must have storage slots in lexicographic order."""
    addr = Address(0xA)

    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                storage_changes=[
                    BalStorageSlot(slot=slot, slot_changes=[])
                    for slot in storage_slots
                ],
            )
        ]
    )

    expectation = BlockAccessListExpectation(account_expectations={})

    with pytest.raises(BlockAccessListValidationError, match=error_message):
        expectation.verify_against(actual_bal)


@pytest.mark.parametrize(
    "storage_reads,error_message",
    [
        (
            [StorageKey(0x02), StorageKey(0x01)],
            "Storage reads not in ascending order",
        ),
        (
            [StorageKey(0x01), StorageKey(0x03), StorageKey(0x02)],
            "Storage reads not in ascending order",
        ),
    ],
)
def test_actual_bal_storage_reads_ordering(
    storage_reads: Any, error_message: str
) -> None:
    """Test that actual BAL must have storage reads in lexicographic order."""
    addr = Address(0xA)

    actual_bal = BlockAccessList(
        [BalAccountChange(address=addr, storage_reads=storage_reads)]
    )

    expectation = BlockAccessListExpectation(account_expectations={})

    with pytest.raises(BlockAccessListValidationError, match=error_message):
        expectation.verify_against(actual_bal)


@pytest.mark.parametrize(
    "field_name",
    ["nonce_changes", "balance_changes", "code_changes"],
)
def test_actual_bal_tx_indices_ordering(field_name: str) -> None:
    """Test that actual BAL must have tx indices in ascending order."""
    addr = Address(0xA)

    tx_indices = [2, 3, 1]  # out of order

    changes: Any = []
    if field_name == "nonce_changes":
        changes = [
            BalNonceChange(tx_index=idx, post_nonce=1) for idx in tx_indices
        ]
    elif field_name == "balance_changes":
        changes = [
            BalBalanceChange(tx_index=idx, post_balance=100)
            for idx in tx_indices
        ]
    elif field_name == "code_changes":
        changes = [
            BalCodeChange(tx_index=idx, new_code=b"code") for idx in tx_indices
        ]

    actual_bal = BlockAccessList(
        [BalAccountChange(address=addr, **{field_name: changes})]
    )

    expectation = BlockAccessListExpectation(account_expectations={})

    with pytest.raises(
        BlockAccessListValidationError,
        match="Transaction indices not in ascending order",
    ):
        expectation.verify_against(actual_bal)


@pytest.mark.parametrize(
    "field_name",
    ["nonce_changes", "balance_changes", "code_changes"],
)
def test_actual_bal_duplicate_tx_indices(field_name: str) -> None:
    """
    Test that actual BAL must not have duplicate tx indices in change lists.
    """
    addr = Address(0xA)

    # Duplicate tx_index=1
    changes: Any = []
    if field_name == "nonce_changes":
        changes = [
            BalNonceChange(tx_index=1, post_nonce=1),
            BalNonceChange(tx_index=1, post_nonce=2),  # duplicate tx_index
            BalNonceChange(tx_index=2, post_nonce=3),
        ]
    elif field_name == "balance_changes":
        changes = [
            BalBalanceChange(tx_index=1, post_balance=100),
            BalBalanceChange(
                tx_index=1, post_balance=200
            ),  # duplicate tx_index
            BalBalanceChange(tx_index=2, post_balance=300),
        ]
    elif field_name == "code_changes":
        changes = [
            BalCodeChange(tx_index=1, new_code=b"code1"),
            BalCodeChange(tx_index=1, new_code=b""),  # duplicate tx_index
            BalCodeChange(tx_index=2, new_code=b"code2"),
        ]

    actual_bal = BlockAccessList(
        [BalAccountChange(address=addr, **{field_name: changes})]
    )

    expectation = BlockAccessListExpectation(account_expectations={})

    with pytest.raises(
        BlockAccessListValidationError,
        match=f"Duplicate transaction indices in {field_name}.*Duplicates: \\[1\\]",
    ):
        expectation.verify_against(actual_bal)


def test_actual_bal_storage_duplicate_tx_indices() -> None:
    """
    Test that storage changes must not have duplicate tx indices within same
    slot.
    """
    addr = Address(0xA)

    # Create storage changes with duplicate tx_index within the same slot
    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                storage_changes=[
                    BalStorageSlot(
                        slot=0x01,
                        slot_changes=[
                            BalStorageChange(tx_index=1, post_value=0x100),
                            BalStorageChange(
                                tx_index=1, post_value=0x200
                            ),  # duplicate tx_index
                            BalStorageChange(tx_index=2, post_value=0x300),
                        ],
                    )
                ],
            )
        ]
    )

    expectation = BlockAccessListExpectation(account_expectations={})

    with pytest.raises(
        BlockAccessListValidationError,
        match="Duplicate transaction indices in storage slot.*Duplicates: \\[1\\]",
    ):
        expectation.verify_against(actual_bal)


def test_expected_addresses_auto_sorted() -> None:
    """
    Test that expected addresses are automatically sorted before comparison.

    The BAL *Expectation address order should not matter for the dict. We DO,
    however, validate that the actual BAL (from t8n) is sorted correctly.
    """
    alice = Address(0xA)
    bob = Address(0xB)
    charlie = Address(0xC)

    actual_bal = BlockAccessList(
        [
            BalAccountChange(address=alice, nonce_changes=[]),
            BalAccountChange(address=bob, nonce_changes=[]),
            BalAccountChange(address=charlie, nonce_changes=[]),
        ]
    )

    # expectation order should not matter for the dict though we DO validate
    # that the _actual_ BAL (from t8n) is sorted correctly
    expectation = BlockAccessListExpectation(
        account_expectations={
            charlie: BalAccountExpectation(nonce_changes=[]),
            alice: BalAccountExpectation(nonce_changes=[]),
            bob: BalAccountExpectation(nonce_changes=[]),
        }
    )

    expectation.verify_against(actual_bal)


@pytest.mark.parametrize(
    "expected_slots,should_pass",
    [
        # Correct order - should pass
        ([StorageKey(0x01), StorageKey(0x02), StorageKey(0x03)], True),
        # Partial subset in correct order - should pass
        ([StorageKey(0x01), StorageKey(0x03)], True),
        # Out of order - should fail
        ([StorageKey(0x01), StorageKey(0x03), StorageKey(0x02)], False),
        # Wrong order from start - should fail
        ([StorageKey(0x02), StorageKey(0x01)], False),
    ],
)
def test_expected_storage_slots_ordering(
    expected_slots: Any, should_pass: bool
) -> None:
    """Test that expected storage slots must be defined in correct order."""
    addr = Address(0xA)

    # Actual BAL with storage slots in correct order
    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                storage_changes=[
                    BalStorageSlot(slot=StorageKey(0x01), slot_changes=[]),
                    BalStorageSlot(slot=StorageKey(0x02), slot_changes=[]),
                    BalStorageSlot(slot=StorageKey(0x03), slot_changes=[]),
                ],
            )
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            addr: BalAccountExpectation(
                storage_changes=[
                    BalStorageSlot(slot=slot, slot_changes=[])
                    for slot in expected_slots
                ],
            ),
        }
    )

    if should_pass:
        expectation.verify_against(actual_bal)
    else:
        with pytest.raises(
            BlockAccessListValidationError,
            match="not found or not in correct order",
        ):
            expectation.verify_against(actual_bal)


@pytest.mark.parametrize(
    "expected_reads,should_pass",
    [
        # Correct order - should pass
        ([StorageKey(0x01), StorageKey(0x02), StorageKey(0x03)], True),
        # Partial subset in correct order - should pass
        ([StorageKey(0x02), StorageKey(0x03)], True),
        # Out of order - should fail
        ([StorageKey(0x03), StorageKey(0x02)], False),
        # Wrong order with all elements - should fail
        ([StorageKey(0x01), StorageKey(0x03), StorageKey(0x02)], False),
    ],
)
def test_expected_storage_reads_ordering(
    expected_reads: Any, should_pass: bool
) -> None:
    """Test that expected storage reads must be defined in correct order."""
    addr = Address(0xA)

    # Actual BAL with storage reads in correct order
    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                storage_reads=[
                    StorageKey(0x01),
                    StorageKey(0x02),
                    StorageKey(0x03),
                ],
            )
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            addr: BalAccountExpectation(storage_reads=expected_reads),
        }
    )

    if should_pass:
        expectation.verify_against(actual_bal)
    else:
        with pytest.raises(
            BlockAccessListValidationError,
            match="not found or not in correct order",
        ):
            expectation.verify_against(actual_bal)


@pytest.mark.parametrize(
    "expected_tx_indices,should_pass",
    [
        # Correct order - should pass
        ([1, 2, 3], True),
        # Partial subset in correct order - should pass
        ([1, 3], True),
        # Single element - should pass
        ([2], True),
        # Out of order - should fail
        ([2, 1], False),
        # Wrong order with all elements - should fail
        ([1, 3, 2], False),
    ],
)
def test_expected_tx_indices_ordering(
    expected_tx_indices: Any, should_pass: bool
) -> None:
    """Test that expected tx indices must be defined in correct order."""
    addr = Address(0xA)

    # actual BAL with tx indices in correct order
    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                nonce_changes=[
                    BalNonceChange(tx_index=1, post_nonce=1),
                    BalNonceChange(tx_index=2, post_nonce=2),
                    BalNonceChange(tx_index=3, post_nonce=3),
                ],
            )
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            addr: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(tx_index=idx, post_nonce=idx)
                    for idx in expected_tx_indices
                ],
            ),
        }
    )

    if should_pass:
        expectation.verify_against(actual_bal)
    else:
        with pytest.raises(
            BlockAccessListValidationError,
            match="not found or not in correct order",
        ):
            expectation.verify_against(actual_bal)


@pytest.mark.parametrize("has_change_should_raise", [True, False])
def test_absent_values_nonce_changes(has_change_should_raise: bool) -> None:
    """Test nonce_changes_at_tx validator with present/absent changes."""
    alice = Address(0xA)

    nonce_changes = [BalNonceChange(tx_index=1, post_nonce=1)]
    if has_change_should_raise:
        # add nonce change at tx 2 which should trigger failure
        nonce_changes.append(BalNonceChange(tx_index=2, post_nonce=2))

    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=alice,
                nonce_changes=nonce_changes,
            ),
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            # no nonce changes at tx 2
            alice: BalAccountExpectation(
                absent_values=BalAccountAbsentValues(
                    nonce_changes=[BalNonceChange(tx_index=2, post_nonce=2)]
                )
            )
        }
    )

    if has_change_should_raise:
        with pytest.raises(
            Exception, match="Unexpected nonce change found at tx 0x2"
        ):
            expectation.verify_against(actual_bal)
    else:
        expectation.verify_against(actual_bal)


@pytest.mark.parametrize("has_change_should_raise", [True, False])
def test_absent_values_balance_changes(has_change_should_raise: bool) -> None:
    """Test balance_changes_at_tx validator with present/absent changes."""
    alice = Address(0xA)

    balance_changes = [BalBalanceChange(tx_index=1, post_balance=100)]
    if has_change_should_raise:
        # add balance change at tx 2 which should trigger failure
        balance_changes.append(BalBalanceChange(tx_index=2, post_balance=200))

    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=alice,
                balance_changes=balance_changes,
            ),
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            alice: BalAccountExpectation(
                absent_values=BalAccountAbsentValues(
                    balance_changes=[
                        BalBalanceChange(tx_index=2, post_balance=200)
                    ]
                )
            ),
        }
    )

    if has_change_should_raise:
        with pytest.raises(
            Exception,
            match="Unexpected balance change found at tx 0x2",
        ):
            expectation.verify_against(actual_bal)
    else:
        expectation.verify_against(actual_bal)


@pytest.mark.parametrize("has_change_should_raise", [True, False])
def test_absent_values_storage_changes(has_change_should_raise: bool) -> None:
    """Test storage_changes_at_slots validator with present/absent changes."""
    contract = Address(0xC)

    storage_changes = [
        BalStorageSlot(
            slot=0x01,
            slot_changes=[BalStorageChange(tx_index=1, post_value=0x99)],
        )
    ]
    if has_change_should_raise:
        storage_changes.append(
            BalStorageSlot(
                slot=0x42,
                slot_changes=[BalStorageChange(tx_index=1, post_value=0xBEEF)],
            )
        )

    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=contract,
                storage_changes=storage_changes,
            ),
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            # no storage changes at slot 0x42
            contract: BalAccountExpectation(
                absent_values=BalAccountAbsentValues(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x42,
                            slot_changes=[
                                BalStorageChange(tx_index=1, post_value=0xBEEF)
                            ],
                        )
                    ]
                )
            ),
        }
    )

    if has_change_should_raise:
        with pytest.raises(
            Exception, match="Unexpected storage change found at slot"
        ):
            expectation.verify_against(actual_bal)
    else:
        expectation.verify_against(actual_bal)


@pytest.mark.parametrize("has_read_should_raise", [True, False])
def test_absent_values_storage_reads(has_read_should_raise: bool) -> None:
    """Test storage_reads_at_slots validator with present/absent reads."""
    contract = Address(0xC)

    # Create actual BAL with or without storage read at slot 0x42
    storage_reads = [StorageKey(0x01)]
    if has_read_should_raise:
        storage_reads.append(StorageKey(0x42))

    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=contract,
                storage_reads=storage_reads,
            ),
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            # no storage reads at slot 0x42
            contract: BalAccountExpectation(
                absent_values=BalAccountAbsentValues(
                    storage_reads=[StorageKey(0x42)]
                )
            ),
        }
    )

    if has_read_should_raise:
        with pytest.raises(
            Exception, match="Unexpected storage read found at slot"
        ):
            expectation.verify_against(actual_bal)
    else:
        expectation.verify_against(actual_bal)


@pytest.mark.parametrize("has_change_should_raise", [True, False])
def test_absent_values_code_changes(has_change_should_raise: bool) -> None:
    """Test code_changes_at_tx validator with present/absent changes."""
    alice = Address(0xA)

    code_changes = [BalCodeChange(tx_index=1, new_code=b"\x00")]
    if has_change_should_raise:
        # add code change at tx 2 which should trigger failure
        code_changes.append(BalCodeChange(tx_index=2, new_code=b"\x60\x00"))

    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=alice,
                code_changes=code_changes,
            ),
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            # no code changes at tx 2
            alice: BalAccountExpectation(
                absent_values=BalAccountAbsentValues(
                    code_changes=[
                        BalCodeChange(tx_index=2, new_code=b"\x60\x00")
                    ]
                )
            ),
        }
    )

    if has_change_should_raise:
        with pytest.raises(
            Exception, match="Unexpected code change found at tx 0x2"
        ):
            expectation.verify_against(actual_bal)
    else:
        expectation.verify_against(actual_bal)


def test_multiple_absent_valuess() -> None:
    """Test multiple absence validators working together."""
    contract = Address(0xC)

    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=contract,
                nonce_changes=[],
                balance_changes=[],
                storage_changes=[
                    BalStorageSlot(
                        slot=0x01,
                        slot_changes=[
                            BalStorageChange(tx_index=1, post_value=0x99)
                        ],
                    )
                ],
                storage_reads=[StorageKey(0x01)],
                code_changes=[],
            ),
        ]
    )

    # Test that multiple validators all pass
    expectation = BlockAccessListExpectation(
        account_expectations={
            contract: BalAccountExpectation(
                storage_changes=[
                    BalStorageSlot(
                        slot=0x01,
                        slot_changes=[
                            BalStorageChange(tx_index=1, post_value=0x99)
                        ],
                    )
                ],
                absent_values=BalAccountAbsentValues(
                    nonce_changes=[
                        BalNonceChange(tx_index=1, post_nonce=0),
                        BalNonceChange(tx_index=2, post_nonce=0),
                    ],
                    balance_changes=[
                        BalBalanceChange(tx_index=1, post_balance=0),
                        BalBalanceChange(tx_index=2, post_balance=0),
                    ],
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x42,
                            slot_changes=[
                                BalStorageChange(tx_index=1, post_value=0)
                            ],
                        ),
                        BalStorageSlot(
                            slot=0x43,
                            slot_changes=[
                                BalStorageChange(tx_index=1, post_value=0)
                            ],
                        ),
                    ],
                    storage_reads=[StorageKey(0x42), StorageKey(0x43)],
                    code_changes=[
                        BalCodeChange(tx_index=1, new_code=b""),
                        BalCodeChange(tx_index=2, new_code=b""),
                    ],
                ),
            ),
        }
    )

    expectation.verify_against(actual_bal)


def test_absent_values_with_multiple_tx_indices() -> None:
    """Test absence validators with multiple transaction indices."""
    alice = Address(0xA)

    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=alice,
                nonce_changes=[
                    # nonce changes at tx 1 and 3
                    BalNonceChange(tx_index=1, post_nonce=1),
                    BalNonceChange(tx_index=3, post_nonce=2),
                ],
            ),
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            alice: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(tx_index=1, post_nonce=1),
                    BalNonceChange(tx_index=3, post_nonce=2),
                ],
                absent_values=BalAccountAbsentValues(
                    nonce_changes=[
                        BalNonceChange(tx_index=2, post_nonce=0),
                        BalNonceChange(tx_index=4, post_nonce=0),
                    ]
                ),
            ),
        }
    )

    expectation.verify_against(actual_bal)

    expectation_fail = BlockAccessListExpectation(
        account_expectations={
            alice: BalAccountExpectation(
                absent_values=BalAccountAbsentValues(
                    nonce_changes=[
                        # wrongly forbid change at txs 1 and 2
                        # (1 exists, so should fail)
                        BalNonceChange(tx_index=1, post_nonce=1),
                        BalNonceChange(tx_index=2, post_nonce=0),
                    ]
                ),
            ),
        }
    )

    with pytest.raises(
        Exception, match="Unexpected nonce change found at tx 0x1"
    ):
        expectation_fail.verify_against(actual_bal)


def test_bal_account_absent_values_comprehensive() -> None:
    """Test comprehensive BalAccountAbsentValues usage."""
    addr = Address(0xA)

    # Test forbidding nonce changes
    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)],
            )
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            addr: BalAccountExpectation(
                absent_values=BalAccountAbsentValues(
                    nonce_changes=[BalNonceChange(tx_index=1, post_nonce=1)]
                )
            ),
        }
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match="Unexpected nonce change found at tx",
    ):
        expectation.verify_against(actual_bal)

    # Test forbidding balance changes
    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                balance_changes=[
                    BalBalanceChange(tx_index=2, post_balance=100)
                ],
            )
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            addr: BalAccountExpectation(
                absent_values=BalAccountAbsentValues(
                    balance_changes=[
                        BalBalanceChange(tx_index=2, post_balance=100)
                    ]
                )
            ),
        }
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match="Unexpected balance change found at tx",
    ):
        expectation.verify_against(actual_bal)

    # Test forbidding code changes
    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                code_changes=[BalCodeChange(tx_index=3, new_code=b"\x60\x00")],
            )
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            addr: BalAccountExpectation(
                absent_values=BalAccountAbsentValues(
                    code_changes=[
                        BalCodeChange(tx_index=3, new_code=b"\x60\x00")
                    ]
                )
            ),
        }
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match="Unexpected code change found at tx",
    ):
        expectation.verify_against(actual_bal)

    # Test forbidding storage reads
    actual_bal = BlockAccessList(
        [BalAccountChange(address=addr, storage_reads=[StorageKey(0x42)])]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            addr: BalAccountExpectation(
                absent_values=BalAccountAbsentValues(
                    storage_reads=[StorageKey(0x42)]
                )
            ),
        }
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match="Unexpected storage read found at slot",
    ):
        expectation.verify_against(actual_bal)

    # Test forbidding storage changes
    actual_bal = BlockAccessList(
        [
            BalAccountChange(
                address=addr,
                storage_changes=[
                    BalStorageSlot(
                        slot=0x01,
                        slot_changes=[
                            BalStorageChange(tx_index=1, post_value=99)
                        ],
                    )
                ],
            )
        ]
    )

    expectation = BlockAccessListExpectation(
        account_expectations={
            addr: BalAccountExpectation(
                absent_values=BalAccountAbsentValues(
                    storage_changes=[
                        BalStorageSlot(
                            slot=0x01,
                            slot_changes=[
                                BalStorageChange(tx_index=1, post_value=99)
                            ],
                        )
                    ]
                )
            ),
        }
    )

    with pytest.raises(
        BlockAccessListValidationError,
        match="Unexpected storage change found at slot",
    ):
        expectation.verify_against(actual_bal)


@pytest.mark.parametrize(
    "field_name,field_value",
    [
        ("nonce_changes", []),
        ("balance_changes", []),
        ("code_changes", []),
        ("storage_changes", []),
        ("storage_reads", []),
    ],
)
def test_bal_account_absent_values_empty_list_validation_raises(
    field_name: str, field_value: Any
) -> None:
    """
    Test that empty lists in BalAccountAbsentValues fields
    raise appropriate errors.
    """
    with pytest.raises(ValueError, match="Empty lists are not allowed"):
        BalAccountAbsentValues(**{field_name: field_value})


def test_bal_account_absent_values_empty_slot_changes_raises() -> None:
    """
    Test that empty slot_changes in storage_changes
    raises appropriate error.
    """
    with pytest.raises(ValueError, match="Empty lists are not allowed"):
        BalAccountAbsentValues(
            storage_changes=[
                BalStorageSlot(
                    slot=0x42,
                    slot_changes=[],  # Empty list should raise error
                )
            ]
        )
