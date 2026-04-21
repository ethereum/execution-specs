"""Unit tests for BAL modifier functions."""

from typing import Callable

import pytest

from execution_testing.base_types import Address
from execution_testing.test_types.block_access_list import (
    BalAccountChange,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    BalStorageChange,
    BalStorageSlot,
    BlockAccessList,
)
from execution_testing.test_types.block_access_list.modifiers import (
    append_change,
    append_storage,
    duplicate_account,
    duplicate_balance_change,
    duplicate_code_change,
    duplicate_nonce_change,
    duplicate_slot_change,
    duplicate_storage_read,
    duplicate_storage_slot,
    insert_storage_read,
    modify_balance,
    modify_code,
    modify_nonce,
    modify_storage,
    remove_nonces,
    reorder_accounts,
    swap_bal_indices,
)

ALICE = Address(0xA)
CONTRACT = Address(0xC)


@pytest.fixture()
def sample_bal() -> BlockAccessList:
    """Build a minimal BAL with one flat account and one storage account."""
    return BlockAccessList(
        [
            BalAccountChange(
                address=ALICE,
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1),
                ],
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=100),
                ],
                code_changes=[
                    BalCodeChange(block_access_index=1, new_code=b"\x60"),
                ],
            ),
            BalAccountChange(
                address=CONTRACT,
                storage_changes=[
                    BalStorageSlot(
                        slot=1,
                        slot_changes=[
                            BalStorageChange(
                                block_access_index=1, post_value=0x42
                            ),
                        ],
                    ),
                ],
                storage_reads=[2, 5],
            ),
        ]
    )


def test_duplicate_account(sample_bal: BlockAccessList) -> None:
    """Duplicate an account entry."""
    result = duplicate_account(ALICE)(sample_bal)
    alice_entries = [a for a in result.root if a.address == ALICE]
    assert len(alice_entries) == 2


def test_duplicate_account_missing_raises() -> None:
    """Raise when the target address is absent."""
    bal = BlockAccessList([BalAccountChange(address=ALICE, nonce_changes=[])])
    with pytest.raises(ValueError, match="not found"):
        duplicate_account(CONTRACT)(bal)


def test_duplicate_nonce_change(sample_bal: BlockAccessList) -> None:
    """Duplicate a nonce change by block_access_index."""
    result = duplicate_nonce_change(ALICE, 1)(sample_bal)
    assert len(result.root[0].nonce_changes) == 2
    assert (
        result.root[0].nonce_changes[0].block_access_index
        == result.root[0].nonce_changes[1].block_access_index
    )


def test_duplicate_nonce_change_missing_index_raises(
    sample_bal: BlockAccessList,
) -> None:
    """Raise when the block_access_index is absent."""
    with pytest.raises(ValueError, match="not found"):
        duplicate_nonce_change(ALICE, 99)(sample_bal)


def test_duplicate_balance_change(sample_bal: BlockAccessList) -> None:
    """Duplicate a balance change by block_access_index."""
    result = duplicate_balance_change(ALICE, 1)(sample_bal)
    assert len(result.root[0].balance_changes) == 2


def test_duplicate_balance_change_missing_index_raises(
    sample_bal: BlockAccessList,
) -> None:
    """Raise when the block_access_index is absent."""
    with pytest.raises(ValueError, match="not found"):
        duplicate_balance_change(ALICE, 99)(sample_bal)


# --- duplicate_code_change ---


def test_duplicate_code_change(sample_bal: BlockAccessList) -> None:
    """Duplicate a code change by block_access_index."""
    result = duplicate_code_change(ALICE, 1)(sample_bal)
    assert len(result.root[0].code_changes) == 2
    assert (
        result.root[0].code_changes[0].block_access_index
        == result.root[0].code_changes[1].block_access_index
    )


def test_duplicate_code_change_missing_index_raises(
    sample_bal: BlockAccessList,
) -> None:
    """Raise when the block_access_index is absent."""
    with pytest.raises(ValueError, match="not found"):
        duplicate_code_change(ALICE, 99)(sample_bal)


def test_duplicate_storage_slot(sample_bal: BlockAccessList) -> None:
    """Duplicate a storage slot entry."""
    result = duplicate_storage_slot(CONTRACT, 1)(sample_bal)
    contract = [a for a in result.root if a.address == CONTRACT][0]
    assert len(contract.storage_changes) == 2
    assert contract.storage_changes[0].slot == contract.storage_changes[1].slot


def test_duplicate_storage_slot_missing_raises(
    sample_bal: BlockAccessList,
) -> None:
    """Raise when the slot is absent."""
    with pytest.raises(ValueError, match="not found"):
        duplicate_storage_slot(CONTRACT, 99)(sample_bal)


def test_duplicate_storage_read(sample_bal: BlockAccessList) -> None:
    """Duplicate a storage read entry."""
    result = duplicate_storage_read(CONTRACT, 2)(sample_bal)
    contract = [a for a in result.root if a.address == CONTRACT][0]
    assert len(contract.storage_reads) == 3
    assert contract.storage_reads[0] == contract.storage_reads[1] == 2


def test_duplicate_storage_read_missing_raises(
    sample_bal: BlockAccessList,
) -> None:
    """Raise when the slot is absent from storage_reads."""
    with pytest.raises(ValueError, match="not found"):
        duplicate_storage_read(CONTRACT, 99)(sample_bal)


def test_duplicate_slot_change(sample_bal: BlockAccessList) -> None:
    """Duplicate a slot change within a storage slot."""
    result = duplicate_slot_change(CONTRACT, 1, 1)(sample_bal)
    contract = [a for a in result.root if a.address == CONTRACT][0]
    assert len(contract.storage_changes[0].slot_changes) == 2
    assert (
        contract.storage_changes[0].slot_changes[0].block_access_index
        == contract.storage_changes[0].slot_changes[1].block_access_index
    )


def test_duplicate_slot_change_missing_index_raises(
    sample_bal: BlockAccessList,
) -> None:
    """Raise when the block_access_index is absent within the slot."""
    with pytest.raises(ValueError, match="not found"):
        duplicate_slot_change(CONTRACT, 1, 99)(sample_bal)


def test_duplicate_slot_change_missing_slot_raises(
    sample_bal: BlockAccessList,
) -> None:
    """Raise when the parent slot is absent."""
    with pytest.raises(ValueError, match="not found"):
        duplicate_slot_change(CONTRACT, 99, 1)(sample_bal)


def test_insert_storage_read(sample_bal: BlockAccessList) -> None:
    """Insert a storage read at the correct sorted position."""
    result = insert_storage_read(CONTRACT, 3)(sample_bal)
    contract = [a for a in result.root if a.address == CONTRACT][0]
    assert len(contract.storage_reads) == 3
    assert list(contract.storage_reads) == [2, 3, 5]


def test_insert_storage_read_at_beginning(
    sample_bal: BlockAccessList,
) -> None:
    """Insert before all existing reads."""
    result = insert_storage_read(CONTRACT, 1)(sample_bal)
    contract = [a for a in result.root if a.address == CONTRACT][0]
    assert list(contract.storage_reads) == [1, 2, 5]


def test_insert_storage_read_at_end(sample_bal: BlockAccessList) -> None:
    """Insert after all existing reads."""
    result = insert_storage_read(CONTRACT, 10)(sample_bal)
    contract = [a for a in result.root if a.address == CONTRACT][0]
    assert list(contract.storage_reads) == [2, 5, 10]


def test_insert_storage_read_missing_address_raises() -> None:
    """Raise when the address is absent."""
    bal = BlockAccessList([BalAccountChange(address=ALICE, nonce_changes=[])])
    with pytest.raises(ValueError, match="not found"):
        insert_storage_read(CONTRACT, 1)(bal)


def test_modify_nonce_missing_index_raises(
    sample_bal: BlockAccessList,
) -> None:
    """Raise when the block_access_index is absent from nonce_changes."""
    with pytest.raises(ValueError, match="not found"):
        modify_nonce(ALICE, 99, 42)(sample_bal)


def test_modify_balance_missing_index_raises(
    sample_bal: BlockAccessList,
) -> None:
    """Raise when the block_access_index is absent from balance_changes."""
    with pytest.raises(ValueError, match="not found"):
        modify_balance(ALICE, 99, 9999)(sample_bal)


def test_modify_code_missing_index_raises(sample_bal: BlockAccessList) -> None:
    """Raise when the block_access_index is absent from code_changes."""
    with pytest.raises(ValueError, match="not found"):
        modify_code(ALICE, 99, b"\x00")(sample_bal)


def test_modify_storage_missing_index_raises(
    sample_bal: BlockAccessList,
) -> None:
    """Raise when block_access_index is absent within the storage slot."""
    with pytest.raises(ValueError, match="not found"):
        modify_storage(CONTRACT, 99, 1, 0xFF)(sample_bal)


def test_modify_storage_missing_slot_raises(
    sample_bal: BlockAccessList,
) -> None:
    """Raise when the storage slot itself is absent."""
    with pytest.raises(ValueError, match="not found"):
        modify_storage(CONTRACT, 1, 99, 0xFF)(sample_bal)


def test_modify_nonce_reused_callable_missing_index_still_raises() -> None:
    """Raise even when the same modifier callable is reused across BALs."""
    modifier = modify_nonce(ALICE, 1, 42)
    valid_bal = BlockAccessList(
        [
            BalAccountChange(
                address=ALICE,
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1),
                ],
            )
        ]
    )
    missing_index_bal = BlockAccessList(
        [
            BalAccountChange(
                address=ALICE,
                nonce_changes=[],
            )
        ]
    )

    modifier(valid_bal)

    with pytest.raises(ValueError, match="not found"):
        modifier(missing_index_bal)


def test_reorder_accounts_duplicate_index_raises(
    sample_bal: BlockAccessList,
) -> None:
    """Raise when indices contain duplicates (not a valid permutation)."""
    with pytest.raises(ValueError, match="valid permutation"):
        reorder_accounts([0, 0])(sample_bal)


def test_reorder_accounts_out_of_range_raises(
    sample_bal: BlockAccessList,
) -> None:
    """Raise when indices are not a valid permutation (skipped index)."""
    with pytest.raises(ValueError, match="valid permutation"):
        reorder_accounts([0, 2])(sample_bal)


_EMPTY_BAL = BlockAccessList([])
_ALICE_ONLY_BAL = BlockAccessList(
    [BalAccountChange(address=ALICE, nonce_changes=[])]
)


@pytest.mark.parametrize(
    "modifier_factory, missing_bal",
    [
        pytest.param(
            lambda: remove_nonces(ALICE), _EMPTY_BAL, id="remove_nonces"
        ),
        pytest.param(
            lambda: swap_bal_indices(1, 1), _EMPTY_BAL, id="swap_bal_indices"
        ),
        pytest.param(
            lambda: append_change(
                ALICE, BalNonceChange(block_access_index=2, post_nonce=5)
            ),
            _EMPTY_BAL,
            id="append_change",
        ),
        pytest.param(
            lambda: append_storage(CONTRACT, slot=7, read=True),
            _EMPTY_BAL,
            id="append_storage",
        ),
        pytest.param(
            lambda: duplicate_account(ALICE),
            _EMPTY_BAL,
            id="duplicate_account",
        ),
        pytest.param(
            lambda: duplicate_nonce_change(ALICE, 1),
            _ALICE_ONLY_BAL,
            id="duplicate_nonce_change",
        ),
        pytest.param(
            lambda: insert_storage_read(CONTRACT, 99),
            _EMPTY_BAL,
            id="insert_storage_read",
        ),
    ],
)
def test_reused_callable_does_not_carry_found_state(
    sample_bal: BlockAccessList,
    modifier_factory: Callable[
        [], Callable[[BlockAccessList], BlockAccessList]
    ],
    missing_bal: BlockAccessList,
) -> None:
    """A modifier's found-state must not persist across calls."""
    modifier = modifier_factory()
    modifier(sample_bal)
    with pytest.raises(ValueError, match="not found"):
        modifier(missing_bal)
