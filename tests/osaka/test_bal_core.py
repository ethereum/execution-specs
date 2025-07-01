"""BAL core implementation tests."""

import pytest
from typing import Dict, Set

from ethereum.osaka.bal_builder import BALBuilder
from ethereum.osaka.bal_tracker import StateChangeTracker
from ethereum.osaka.bal_utils import compute_bal_hash, validate_bal_structure
from ethereum.osaka.ssz_types import (
    BlockAccessList, AccountChanges, StorageChange, BalanceChange,
    Address, StorageKey, StorageValue, TxIndex
)
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U16, U64, U256


class TestBALBuilder:
    """Test BAL builder functionality."""
    
    def test_builder_initialization(self):
        """Test builder initializes correctly."""
        builder = BALBuilder()
        assert hasattr(builder, 'accounts')
        assert len(builder.accounts) == 0
    
    def test_storage_operations(self):
        """Test storage read/write operations."""
        builder = BALBuilder()
        address = Address(b'\x01' * 20)
        slot = Bytes32(b'\x00' * 32)
        value = Bytes32(b'\x01' * 32)
        
        builder.add_storage_write(address, slot, 0, value)
        builder.add_storage_read(address, Bytes32(b'\x02' * 32))
        
        bal = builder.build()
        account = bal.account_changes[0]
        
        assert len(account.storage_changes) == 1
        assert len(account.storage_reads) == 1
        assert account.storage_changes[0].changes[0].new_value == value
    
    def test_balance_changes(self):
        """Test balance change tracking."""
        builder = BALBuilder()
        address = Address(b'\x01' * 20)
        balance = b'\x00' * 11 + b'\x42'
        
        builder.add_balance_change(address, 0, balance)
        
        bal = builder.build()
        account = bal.account_changes[0]
        
        assert len(account.balance_changes) == 1
        assert account.balance_changes[0].post_balance == balance
        assert account.balance_changes[0].tx_index == U16(0)
    
    def test_address_sorting(self):
        """Test addresses are sorted lexicographically."""
        builder = BALBuilder()
        addresses = [
            Address(b'\xff' * 20),
            Address(b'\x00' * 20),
            Address(b'\xaa' * 20),
        ]
        
        for addr in addresses:
            builder.add_balance_change(addr, 0, b'\x00' * 12)
        
        bal = builder.build()
        
        for i in range(len(bal.account_changes) - 1):
            addr1 = bal.account_changes[i].address
            addr2 = bal.account_changes[i + 1].address
            assert addr1 < addr2
    
    def test_storage_slot_sorting(self):
        """Test storage slots are sorted within accounts."""
        builder = BALBuilder()
        address = Address(b'\x01' * 20)
        slots = [
            Bytes32(b'\xff' * 32),
            Bytes32(b'\x00' * 32),
            Bytes32(b'\xaa' * 32),
        ]
        
        for slot in slots:
            builder.add_storage_write(address, slot, 0, Bytes32(b'\x01' * 32))
        
        bal = builder.build()
        account = bal.account_changes[0]
        
        for i in range(len(account.storage_changes) - 1):
            slot1 = account.storage_changes[i].slot
            slot2 = account.storage_changes[i + 1].slot
            assert slot1 < slot2
    
    def test_transaction_index_sorting(self):
        """Test transaction indices are sorted."""
        builder = BALBuilder()
        address = Address(b'\x01' * 20)
        tx_indices = [5, 1, 3, 0, 2]
        
        for tx_idx in tx_indices:
            builder.add_balance_change(address, tx_idx, tx_idx.to_bytes(12, 'big'))
        
        bal = builder.build()
        account = bal.account_changes[0]
        
        for i, change in enumerate(account.balance_changes):
            assert change.tx_index == U16(i)
    
    def test_deduplication(self):
        """Test storage read deduplication."""
        builder = BALBuilder()
        address = Address(b'\x01' * 20)
        slot = Bytes32(b'\x00' * 32)
        
        for _ in range(5):
            builder.add_storage_read(address, slot)
        
        bal = builder.build()
        account = bal.account_changes[0]
        
        assert len(account.storage_reads) == 1
        assert account.storage_reads[0].slot == slot


class TestDataIntegrity:
    """Test BAL data structure integrity."""
    
    def test_address_uniqueness(self):
        """Test address uniqueness in BAL."""
        builder = BALBuilder()
        address = Address(b'\x01' * 20)
        
        builder.add_storage_write(address, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x01' * 32))
        builder.add_balance_change(address, 1, b'\x00' * 12)
        
        bal = builder.build()
        
        assert len(bal.account_changes) == 1
        assert bal.account_changes[0].address == address
    
    def test_storage_key_uniqueness(self):
        """Test storage key uniqueness per address."""
        builder = BALBuilder()
        address = Address(b'\x01' * 20)
        slot = Bytes32(b'\x00' * 32)
        
        builder.add_storage_write(address, slot, 0, Bytes32(b'\x01' * 32))
        builder.add_storage_write(address, slot, 1, Bytes32(b'\x02' * 32))
        
        bal = builder.build()
        account = bal.account_changes[0]
        
        assert len(account.storage_changes) == 1
        assert len(account.storage_changes[0].changes) == 2
    
    def test_read_write_separation(self):
        """Test reads and writes are properly separated."""
        builder = BALBuilder()
        address = Address(b'\x01' * 20)
        
        read_slot = Bytes32(b'\x01' * 32)
        write_slot = Bytes32(b'\x02' * 32)
        
        builder.add_storage_read(address, read_slot)
        builder.add_storage_write(address, write_slot, 0, Bytes32(b'\x01' * 32))
        
        bal = builder.build()
        account = bal.account_changes[0]
        
        assert len(account.storage_reads) == 1
        assert len(account.storage_changes) == 1
        assert account.storage_reads[0].slot == read_slot
        assert account.storage_changes[0].slot == write_slot
    
    def test_data_type_correctness(self):
        """Test all data types are correct sizes."""
        builder = BALBuilder()
        address = Address(b'\x01' * 20)
        
        builder.add_storage_write(address, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x01' * 32))
        builder.add_balance_change(address, 0, b'\x00' * 12)
        builder.add_nonce_change(address, 0, 42)
        
        bal = builder.build()
        account = bal.account_changes[0]
        
        assert len(account.address) == 20
        assert len(account.storage_changes[0].slot) == 32
        assert len(account.storage_changes[0].changes[0].new_value) == 32
        assert len(account.balance_changes[0].post_balance) == 12
        assert isinstance(account.nonce_changes[0].new_nonce, U64)


class TestBALHashing:
    """Test BAL hash computation."""
    
    def test_hash_deterministic(self):
        """Test BAL hash is deterministic."""
        builder1 = BALBuilder()
        builder2 = BALBuilder()
        
        address = Address(b'\x01' * 20)
        
        for builder in [builder1, builder2]:
            builder.add_storage_write(address, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x01' * 32))
        
        bal1 = builder1.build()
        bal2 = builder2.build()
        
        hash1 = compute_bal_hash(bal1)
        hash2 = compute_bal_hash(bal2)
        
        assert hash1 == hash2
        assert len(hash1) == 32
    
    def test_hash_different_data(self):
        """Test different BALs produce different hashes."""
        builder1 = BALBuilder()
        builder2 = BALBuilder()
        
        address = Address(b'\x01' * 20)
        
        builder1.add_storage_write(address, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x01' * 32))
        builder2.add_storage_write(address, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x02' * 32))
        
        bal1 = builder1.build()
        bal2 = builder2.build()
        
        hash1 = compute_bal_hash(bal1)
        hash2 = compute_bal_hash(bal2)
        
        assert hash1 != hash2
    
    def test_validation(self):
        """Test BAL structure validation."""
        builder = BALBuilder()
        address = Address(b'\x01' * 20)
        
        builder.add_storage_write(address, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x01' * 32))
        
        bal = builder.build()
        validate_bal_structure(bal)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_bal(self):
        """Test empty BAL."""
        builder = BALBuilder()
        bal = builder.build()
        
        assert len(bal.account_changes) == 0
        validate_bal_structure(bal)
        hash_val = compute_bal_hash(bal)
        assert len(hash_val) == 32
    
    def test_zero_values(self):
        """Test zero address and values."""
        builder = BALBuilder()
        zero_addr = Address(b'\x00' * 20)
        
        builder.add_storage_write(zero_addr, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x00' * 32))
        builder.add_balance_change(zero_addr, 0, b'\x00' * 12)
        
        bal = builder.build()
        validate_bal_structure(bal)
        
        assert len(bal.account_changes) == 1
        assert bal.account_changes[0].address == zero_addr
    
    def test_max_values(self):
        """Test maximum values."""
        builder = BALBuilder()
        max_addr = Address(b'\xff' * 20)
        
        builder.add_storage_write(max_addr, Bytes32(b'\xff' * 32), 65535, Bytes32(b'\xff' * 32))
        builder.add_balance_change(max_addr, 65535, b'\xff' * 12)
        builder.add_nonce_change(max_addr, 65535, 2**64 - 1)
        
        bal = builder.build()
        validate_bal_structure(bal)
        
        account = bal.account_changes[0]
        assert account.storage_changes[0].changes[0].tx_index == U16(65535)
        assert account.balance_changes[0].tx_index == U16(65535)
        assert account.nonce_changes[0].new_nonce == U64(2**64 - 1)
    
    @pytest.mark.slow
    def test_large_dataset(self):
        """Test large number of accounts."""
        builder = BALBuilder()
        
        num_accounts = 1000
        for i in range(num_accounts):
            addr = Address(i.to_bytes(20, 'big'))
            builder.add_balance_change(addr, 0, i.to_bytes(12, 'big'))
        
        bal = builder.build()
        validate_bal_structure(bal)
        
        assert len(bal.account_changes) == num_accounts
        
        prev_addr = b''
        for account in bal.account_changes:
            curr_addr = bytes(account.address)
            assert curr_addr > prev_addr
            prev_addr = curr_addr


def test_bal_tracker_integration():
    """Test BAL tracker integration."""
    builder = BALBuilder()
    tracker = StateChangeTracker(builder)
    
    address = Address(b'\x01' * 20)
    
    tracker.set_transaction_index(0)
    tracker.track_address_access(address)
    
    bal = builder.build()
    assert len(bal.account_changes) >= 1


if __name__ == "__main__":
    pytest.main([__file__])