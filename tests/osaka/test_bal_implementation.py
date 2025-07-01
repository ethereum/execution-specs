"""
Tests for EIP-7928 Block Access List Implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This module contains comprehensive tests for the Block Access List implementation
including SSZ data structures, BAL builder, tracking, and validation.
"""

import pytest
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U16, U64, U256, Uint

from ethereum.osaka.bal_builder import BALBuilder
from ethereum.osaka.bal_tracker import StateChangeTracker
from ethereum.osaka.bal_utils import compute_bal_hash, validate_bal_against_execution
from ethereum.osaka.fork_types import Address
from ethereum.osaka.ssz_types import (
    AccountChanges,
    BalanceChange,
    BlockAccessList,
    CodeChange,
    NonceChange,
    SlotChanges,
    SlotRead,
    StorageChange,
)


class TestSSZDataStructures:
    """Test SSZ data structures for Block Access Lists."""

    def test_storage_change_creation(self):
        """Test StorageChange creation."""
        change = StorageChange(
            tx_index=U16(1),
            new_value=Bytes32(b'\x00' * 31 + b'\x42')
        )
        assert change.tx_index == U16(1)
        assert change.new_value == Bytes32(b'\x00' * 31 + b'\x42')

    def test_balance_change_creation(self):
        """Test BalanceChange creation."""
        balance_bytes = b'\x00' * 8 + (1000).to_bytes(4, 'big')
        change = BalanceChange(
            tx_index=U16(0),
            post_balance=balance_bytes
        )
        assert change.tx_index == U16(0)
        assert change.post_balance == balance_bytes

    def test_nonce_change_creation(self):
        """Test NonceChange creation."""
        change = NonceChange(
            tx_index=U16(2),
            new_nonce=U64(5)
        )
        assert change.tx_index == U16(2)
        assert change.new_nonce == U64(5)

    def test_code_change_creation(self):
        """Test CodeChange creation."""
        code = Bytes(b'\x60\x80\x60\x40')  # Simple bytecode
        change = CodeChange(
            tx_index=U16(1),
            new_code=code
        )
        assert change.tx_index == U16(1)
        assert change.new_code == code

    def test_slot_changes_creation(self):
        """Test SlotChanges creation."""
        slot = Bytes32(b'\x00' * 31 + b'\x01')
        changes = (
            StorageChange(tx_index=U16(0), new_value=Bytes32(b'\x00' * 31 + b'\x42')),
            StorageChange(tx_index=U16(1), new_value=Bytes32(b'\x00' * 31 + b'\x43')),
        )
        slot_changes = SlotChanges(slot=slot, changes=changes)
        assert slot_changes.slot == slot
        assert len(slot_changes.changes) == 2

    def test_slot_read_creation(self):
        """Test SlotRead creation."""
        slot = Bytes32(b'\x00' * 31 + b'\x02')
        slot_read = SlotRead(slot=slot)
        assert slot_read.slot == slot

    def test_account_changes_creation(self):
        """Test AccountChanges creation."""
        address = Address(b'\x12' * 20)
        storage_changes = (
            SlotChanges(
                slot=Bytes32(b'\x00' * 31 + b'\x01'),
                changes=(StorageChange(tx_index=U16(0), new_value=Bytes32(b'\x00' * 31 + b'\x42')),)
            ),
        )
        storage_reads = (SlotRead(slot=Bytes32(b'\x00' * 31 + b'\x02')),)
        balance_changes = (BalanceChange(tx_index=U16(0), post_balance=b'\x00' * 8 + (1000).to_bytes(4, 'big')),)
        nonce_changes = (NonceChange(tx_index=U16(1), new_nonce=U64(5)),)
        code_changes = ()

        account = AccountChanges(
            address=address,
            storage_changes=storage_changes,
            storage_reads=storage_reads,
            balance_changes=balance_changes,
            nonce_changes=nonce_changes,
            code_changes=code_changes
        )
        assert account.address == address
        assert len(account.storage_changes) == 1
        assert len(account.storage_reads) == 1
        assert len(account.balance_changes) == 1
        assert len(account.nonce_changes) == 1
        assert len(account.code_changes) == 0

    def test_block_access_list_creation(self):
        """Test BlockAccessList creation."""
        address = Address(b'\x12' * 20)
        account_changes = (
            AccountChanges(
                address=address,
                storage_changes=(),
                storage_reads=(),
                balance_changes=(),
                nonce_changes=(),
                code_changes=()
            ),
        )
        bal = BlockAccessList(account_changes=account_changes)
        assert len(bal.account_changes) == 1
        assert bal.account_changes[0].address == address


class TestBALBuilder:
    """Test BAL Builder functionality."""

    def test_bal_builder_initialization(self):
        """Test BAL builder initialization."""
        builder = BALBuilder()
        assert len(builder.accounts) == 0

    def test_add_storage_write(self):
        """Test adding storage writes."""
        builder = BALBuilder()
        address = Address(b'\x12' * 20)
        slot = Bytes32(b'\x00' * 31 + b'\x01')
        value = Bytes32(b'\x00' * 31 + b'\x42')
        
        builder.add_storage_write(address, slot, 0, value)
        
        assert address in builder.accounts
        assert slot in builder.accounts[address]['storage_changes']
        assert len(builder.accounts[address]['storage_changes'][slot]) == 1
        
        change = builder.accounts[address]['storage_changes'][slot][0]
        assert change.tx_index == U16(0)
        assert change.new_value == value

    def test_add_storage_read(self):
        """Test adding storage reads."""
        builder = BALBuilder()
        address = Address(b'\x12' * 20)
        slot = Bytes32(b'\x00' * 31 + b'\x01')
        
        builder.add_storage_read(address, slot)
        
        assert address in builder.accounts
        assert slot in builder.accounts[address]['storage_reads']

    def test_add_balance_change(self):
        """Test adding balance changes."""
        builder = BALBuilder()
        address = Address(b'\x12' * 20)
        balance_bytes = b'\x00' * 8 + (1000).to_bytes(4, 'big')
        
        builder.add_balance_change(address, 0, balance_bytes)
        
        assert address in builder.accounts
        assert len(builder.accounts[address]['balance_changes']) == 1
        
        change = builder.accounts[address]['balance_changes'][0]
        assert change.tx_index == U16(0)
        assert change.post_balance == balance_bytes

    def test_add_nonce_change(self):
        """Test adding nonce changes."""
        builder = BALBuilder()
        address = Address(b'\x12' * 20)
        
        builder.add_nonce_change(address, 1, 5)
        
        assert address in builder.accounts
        assert len(builder.accounts[address]['nonce_changes']) == 1
        
        change = builder.accounts[address]['nonce_changes'][0]
        assert change.tx_index == U16(1)
        assert change.new_nonce == U64(5)

    def test_add_code_change(self):
        """Test adding code changes."""
        builder = BALBuilder()
        address = Address(b'\x12' * 20)
        code = Bytes(b'\x60\x80\x60\x40')
        
        builder.add_code_change(address, 1, code)
        
        assert address in builder.accounts
        assert len(builder.accounts[address]['code_changes']) == 1
        
        change = builder.accounts[address]['code_changes'][0]
        assert change.tx_index == U16(1)
        assert change.new_code == code

    def test_add_touched_account(self):
        """Test adding touched accounts."""
        builder = BALBuilder()
        address = Address(b'\x12' * 20)
        
        builder.add_touched_account(address)
        
        assert address in builder.accounts
        # Should have empty change lists
        assert len(builder.accounts[address]['storage_changes']) == 0
        assert len(builder.accounts[address]['storage_reads']) == 0
        assert len(builder.accounts[address]['balance_changes']) == 0
        assert len(builder.accounts[address]['nonce_changes']) == 0
        assert len(builder.accounts[address]['code_changes']) == 0

    def test_build_simple_bal(self):
        """Test building a simple BAL."""
        builder = BALBuilder()
        address = Address(b'\x12' * 20)
        slot = Bytes32(b'\x00' * 31 + b'\x01')
        value = Bytes32(b'\x00' * 31 + b'\x42')
        balance_bytes = b'\x00' * 8 + (1000).to_bytes(4, 'big')
        
        builder.add_storage_write(address, slot, 0, value)
        builder.add_balance_change(address, 0, balance_bytes)
        
        bal = builder.build()
        
        assert len(bal.account_changes) == 1
        account = bal.account_changes[0]
        assert account.address == address
        assert len(account.storage_changes) == 1
        assert len(account.balance_changes) == 1

    def test_build_with_sorting(self):
        """Test that build() produces sorted output."""
        builder = BALBuilder()
        address1 = Address(b'\x01' * 20)
        address2 = Address(b'\x02' * 20)
        
        # Add in reverse order
        builder.add_touched_account(address2)
        builder.add_touched_account(address1)
        
        bal = builder.build()
        
        # Should be sorted by address
        assert len(bal.account_changes) == 2
        assert bal.account_changes[0].address == address1
        assert bal.account_changes[1].address == address2


class TestBALUtils:
    """Test BAL utility functions."""

    def test_compute_bal_hash_deterministic(self):
        """Test that BAL hash computation is deterministic."""
        # Create identical BALs
        bal1 = BlockAccessList(account_changes=())
        bal2 = BlockAccessList(account_changes=())
        
        hash1 = compute_bal_hash(bal1)
        hash2 = compute_bal_hash(bal2)
        
        assert hash1 == hash2
        assert len(hash1) == 32  # keccak256 produces 32 bytes

    def test_compute_bal_hash_different_for_different_bals(self):
        """Test that different BALs produce different hashes."""
        address1 = Address(b'\x01' * 20)
        address2 = Address(b'\x02' * 20)
        
        account1 = AccountChanges(
            address=address1,
            storage_changes=(),
            storage_reads=(),
            balance_changes=(),
            nonce_changes=(),
            code_changes=()
        )
        
        account2 = AccountChanges(
            address=address2,
            storage_changes=(),
            storage_reads=(),
            balance_changes=(),
            nonce_changes=(),
            code_changes=()
        )
        
        bal1 = BlockAccessList(account_changes=(account1,))
        bal2 = BlockAccessList(account_changes=(account2,))
        
        hash1 = compute_bal_hash(bal1)
        hash2 = compute_bal_hash(bal2)
        
        assert hash1 != hash2

    def test_validate_bal_against_execution_empty(self):
        """Test validating empty BAL against empty execution."""
        bal = BlockAccessList(account_changes=())
        accessed_addresses = set()
        accessed_storage_keys = set()
        state_changes = {}
        
        result = validate_bal_against_execution(
            bal, accessed_addresses, accessed_storage_keys, state_changes
        )
        
        assert result is True

    def test_validate_bal_against_execution_with_data(self):
        """Test validating BAL with data against execution."""
        address = Address(b'\x12' * 20)
        slot = Bytes32(b'\x00' * 31 + b'\x01')
        
        account = AccountChanges(
            address=address,
            storage_changes=(),
            storage_reads=(SlotRead(slot=slot),),
            balance_changes=(),
            nonce_changes=(),
            code_changes=()
        )
        
        bal = BlockAccessList(account_changes=(account,))
        accessed_addresses = {address}
        accessed_storage_keys = {(address, slot)}
        state_changes = {}
        
        result = validate_bal_against_execution(
            bal, accessed_addresses, accessed_storage_keys, state_changes
        )
        
        assert result is True

    def test_validate_bal_missing_address(self):
        """Test validation fails when BAL missing accessed address."""
        bal = BlockAccessList(account_changes=())
        accessed_addresses = {Address(b'\x12' * 20)}
        accessed_storage_keys = set()
        state_changes = {}
        
        result = validate_bal_against_execution(
            bal, accessed_addresses, accessed_storage_keys, state_changes
        )
        
        assert result is False


class TestBALTracker:
    """Test BAL state change tracker."""

    def test_tracker_initialization(self):
        """Test tracker initialization."""
        builder = BALBuilder()
        tracker = StateChangeTracker(builder)
        assert tracker.bal_builder is builder
        assert tracker.current_tx_index == 0

    def test_set_transaction_index(self):
        """Test setting transaction index."""
        builder = BALBuilder()
        tracker = StateChangeTracker(builder)
        
        tracker.set_transaction_index(5)
        assert tracker.current_tx_index == 5

    def test_track_address_access(self):
        """Test tracking address access."""
        builder = BALBuilder()
        tracker = StateChangeTracker(builder)
        address = Address(b'\x12' * 20)
        
        tracker.track_address_access(address)
        
        assert address in builder.accounts


class TestEIP7928Integration:
    """Integration tests for EIP-7928 functionality."""

    def test_complete_bal_workflow(self):
        """Test complete BAL construction workflow."""
        # Create builder and tracker
        builder = BALBuilder()
        tracker = StateChangeTracker(builder)
        
        # Simulate transaction 0
        tracker.set_transaction_index(0)
        address1 = Address(b'\x01' * 20)
        address2 = Address(b'\x02' * 20)
        
        # Add various changes
        slot = Bytes32(b'\x00' * 31 + b'\x01')
        value = Bytes32(b'\x00' * 31 + b'\x42')
        balance_bytes = b'\x00' * 8 + (1000).to_bytes(4, 'big')
        
        builder.add_storage_write(address1, slot, 0, value)
        builder.add_balance_change(address1, 0, balance_bytes)
        builder.add_touched_account(address2)
        
        # Build BAL
        bal = builder.build()
        
        # Verify structure
        assert len(bal.account_changes) == 2
        
        # Check address1 (should be first due to sorting)
        account1 = bal.account_changes[0]
        assert account1.address == address1
        assert len(account1.storage_changes) == 1
        assert len(account1.balance_changes) == 1
        
        # Check address2 (should be second)
        account2 = bal.account_changes[1]
        assert account2.address == address2
        assert len(account2.storage_changes) == 0
        assert len(account2.balance_changes) == 0
        
        # Verify hash can be computed
        bal_hash = compute_bal_hash(bal)
        assert len(bal_hash) == 32