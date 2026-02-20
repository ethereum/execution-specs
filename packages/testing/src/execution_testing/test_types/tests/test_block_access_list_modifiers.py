"""Unit tests for BAL modifier functions."""

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
    duplicate_account,
    duplicate_balance_change,
    duplicate_code_change,
    duplicate_nonce_change,
    duplicate_slot_change,
    duplicate_storage_read,
    duplicate_storage_slot,
    insert_storage_read,
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
