"""
Comprehensive tests for Block Access List (BAL) implementation in EIP-7928.

This module tests the complete BAL implementation including:
- Core functionality (tracking, building, validation)
- State modifications and nonce tracking
- Integration with VM instructions
- Edge cases and error handling
"""

import ast
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.numeric import U32, U64, U256

from ethereum.osaka.bal_builder import BALBuilder
from ethereum.osaka.bal_tracker import StateChangeTracker
from ethereum.osaka.ssz_types import (
    AccountChanges,
    BalanceChange,
    BlockAccessList,
    CodeChange,
    NonceChange,
    SlotChanges,
    StorageChange,
    MAX_CODE_CHANGES,
)


class TestBALCore:
    """Test core BAL functionality."""
    
    def test_bal_builder_initialization(self):
        """Test BAL builder initializes correctly."""
        builder = BALBuilder()
        assert builder.accounts == {}
    
    def test_bal_builder_add_storage_write(self):
        """Test adding storage writes to BAL builder."""
        builder = BALBuilder()
        address = Bytes20(b'\x01' * 20)
        slot = Bytes32(b'\x02' * 32)
        value = Bytes32(b'\x03' * 32)
        
        builder.add_storage_write(address, slot, 0, value)
        
        assert address in builder.accounts
        assert slot in builder.accounts[address]['storage_changes']
        assert len(builder.accounts[address]['storage_changes'][slot]) == 1
        
        change = builder.accounts[address]['storage_changes'][slot][0]
        assert change.tx_index == U32(0)
        assert change.new_value == value
    
    def test_bal_builder_add_storage_read(self):
        """Test adding storage reads to BAL builder."""
        builder = BALBuilder()
        address = Bytes20(b'\x01' * 20)
        slot = Bytes32(b'\x02' * 32)
        
        builder.add_storage_read(address, slot)
        
        assert address in builder.accounts
        assert slot in builder.accounts[address]['storage_reads']
    
    def test_bal_builder_add_balance_change(self):
        """Test adding balance changes to BAL builder."""
        builder = BALBuilder()
        address = Bytes20(b'\x01' * 20)
        balance = Bytes(b'\x00' * 16)  # uint128
        
        builder.add_balance_change(address, 0, balance)
        
        assert address in builder.accounts
        assert len(builder.accounts[address]['balance_changes']) == 1
        
        change = builder.accounts[address]['balance_changes'][0]
        assert change.tx_index == U32(0)
        assert change.post_balance == balance
    
    def test_bal_builder_add_nonce_change(self):
        """Test adding nonce changes to BAL builder."""
        builder = BALBuilder()
        address = Bytes20(b'\x01' * 20)
        nonce = 42
        
        builder.add_nonce_change(address, 0, nonce)
        
        assert address in builder.accounts
        assert len(builder.accounts[address]['nonce_changes']) == 1
        
        change = builder.accounts[address]['nonce_changes'][0]
        assert change.tx_index == U32(0)
        assert change.new_nonce == U64(42)
    
    def test_bal_builder_add_code_change(self):
        """Test adding code changes to BAL builder."""
        builder = BALBuilder()
        address = Bytes20(b'\x01' * 20)
        code = Bytes(b'\x60\x80\x60\x40')
        
        builder.add_code_change(address, 0, code)
        
        assert address in builder.accounts
        assert len(builder.accounts[address]['code_changes']) == 1
        
        change = builder.accounts[address]['code_changes'][0]
        assert change.tx_index == U32(0)
        assert change.new_code == code
    
    def test_bal_builder_touched_account(self):
        """Test adding touched accounts without changes."""
        builder = BALBuilder()
        address = Bytes20(b'\x01' * 20)
        
        builder.add_touched_account(address)
        
        assert address in builder.accounts
        assert builder.accounts[address]['storage_changes'] == {}
        assert builder.accounts[address]['storage_reads'] == set()
        assert builder.accounts[address]['balance_changes'] == []
        assert builder.accounts[address]['nonce_changes'] == []
        assert builder.accounts[address]['code_changes'] == []
    
    def test_bal_builder_build_complete(self):
        """Test building a complete BlockAccessList."""
        builder = BALBuilder()
        
        # Add various changes
        address1 = Bytes20(b'\x01' * 20)
        address2 = Bytes20(b'\x02' * 20)
        slot1 = Bytes32(b'\x03' * 32)
        slot2 = Bytes32(b'\x04' * 32)
        
        # Address 1: storage write and read
        builder.add_storage_write(address1, slot1, 0, Bytes32(b'\x05' * 32))
        builder.add_storage_read(address1, slot2)
        builder.add_balance_change(address1, 0, Bytes(b'\x00' * 16))
        
        # Address 2: only touched
        builder.add_touched_account(address2)
        
        # Build BAL
        bal = builder.build()
        
        assert isinstance(bal, BlockAccessList)
        assert len(bal.account_changes) == 2
        
        # Verify sorting by address
        assert bal.account_changes[0].address == address1
        assert bal.account_changes[1].address == address2
        
        # Verify address1 changes
        acc1 = bal.account_changes[0]
        assert len(acc1.storage_changes) == 1
        assert len(acc1.storage_reads) == 1
        assert acc1.storage_reads[0] == slot2  # Direct StorageKey, not SlotRead
        assert len(acc1.balance_changes) == 1
        
        # Verify address2 is empty
        acc2 = bal.account_changes[1]
        assert len(acc2.storage_changes) == 0
        assert len(acc2.storage_reads) == 0
        assert len(acc2.balance_changes) == 0


class TestBALTracker:
    """Test BAL state change tracker functionality."""
    
    def test_tracker_initialization(self):
        """Test tracker initializes with BAL builder."""
        builder = BALBuilder()
        tracker = StateChangeTracker(builder)
        assert tracker.bal_builder is builder
        assert tracker.pre_storage_cache == {}
        assert tracker.current_tx_index == 0
    
    def test_tracker_set_transaction_index(self):
        """Test setting transaction index."""
        builder = BALBuilder()
        tracker = StateChangeTracker(builder)
        
        tracker.set_transaction_index(5)
        assert tracker.current_tx_index == 5
        # Pre-storage cache should persist across transactions
        assert tracker.pre_storage_cache == {}
    
    @patch('ethereum.osaka.bal_tracker.get_storage')
    def test_tracker_capture_pre_state(self, mock_get_storage):
        """Test capturing pre-state values."""
        builder = BALBuilder()
        tracker = StateChangeTracker(builder)
        
        address = Bytes20(b'\x01' * 20)
        key = Bytes32(b'\x02' * 32)
        mock_state = MagicMock()
        mock_get_storage.return_value = U256(100)
        
        # First call should fetch from state
        value = tracker.capture_pre_state(address, key, mock_state)
        assert value == U256(100)
        assert (address, key) in tracker.pre_storage_cache
        mock_get_storage.assert_called_once_with(mock_state, address, key)
        
        # Second call should use cache
        mock_get_storage.reset_mock()
        value2 = tracker.capture_pre_state(address, key, mock_state)
        assert value2 == U256(100)
        mock_get_storage.assert_not_called()
    
    @patch('ethereum.osaka.bal_tracker.get_storage')
    def test_tracker_storage_write_changed(self, mock_get_storage):
        """Test tracking storage write with changed value."""
        builder = BALBuilder()
        tracker = StateChangeTracker(builder)
        
        address = Bytes20(b'\x01' * 20)
        key = Bytes32(b'\x02' * 32)
        mock_state = MagicMock()
        mock_get_storage.return_value = U256(100)
        
        tracker.track_storage_write(address, key, U256(200), mock_state)
        
        # Should add storage write since value changed
        assert address in builder.accounts
        assert key in builder.accounts[address]['storage_changes']
        assert key not in builder.accounts[address]['storage_reads']
    
    @patch('ethereum.osaka.bal_tracker.get_storage')
    def test_tracker_storage_write_unchanged(self, mock_get_storage):
        """Test tracking storage write with unchanged value."""
        builder = BALBuilder()
        tracker = StateChangeTracker(builder)
        
        address = Bytes20(b'\x01' * 20)
        key = Bytes32(b'\x02' * 32)
        mock_state = MagicMock()
        mock_get_storage.return_value = U256(100)
        
        tracker.track_storage_write(address, key, U256(100), mock_state)
        
        # Should add as read instead since value unchanged
        assert address in builder.accounts
        assert key not in builder.accounts[address]['storage_changes']
        assert key in builder.accounts[address]['storage_reads']
    
    def test_tracker_balance_change_uint128(self):
        """Test balance change converts to uint128 correctly."""
        builder = BALBuilder()
        tracker = StateChangeTracker(builder)
        
        address = Bytes20(b'\x01' * 20)
        mock_state = MagicMock()
        
        # Test with a large balance that fits in uint128
        balance = U256(2**127 - 1)
        tracker.track_balance_change(address, balance, mock_state)
        
        assert address in builder.accounts
        changes = builder.accounts[address]['balance_changes']
        assert len(changes) == 1
        # Should be 16 bytes (uint128)
        assert len(changes[0].post_balance) == 16


class TestBALIntegration:
    """Test BAL integration with the broader system."""
    
    def test_ssz_types_constants(self):
        """Test SSZ type constants are correct."""
        assert MAX_CODE_CHANGES == 1
    
    def test_storage_reads_type(self):
        """Test storage_reads is now direct StorageKey list."""
        address = Bytes20(b'\x01' * 20)
        storage_key = Bytes32(b'\x02' * 32)
        
        account_changes = AccountChanges(
            address=address,
            storage_changes=(),
            storage_reads=(storage_key,),  # Direct StorageKey, not SlotRead
            balance_changes=(),
            nonce_changes=(),
            code_changes=()
        )
        
        assert account_changes.storage_reads[0] == storage_key
        assert isinstance(account_changes.storage_reads[0], Bytes32)
    
    def test_balance_type_is_bytes(self):
        """Test Balance type is Bytes for uint128."""
        balance = Bytes(b'\x00' * 16)  # 16 bytes for uint128
        balance_change = BalanceChange(
            tx_index=U32(0),
            post_balance=balance
        )
        assert isinstance(balance_change.post_balance, Bytes)
        assert len(balance_change.post_balance) == 16
    
    def test_increment_nonce_accepts_bal_tracker(self):
        """Test that increment_nonce in state.py accepts bal_tracker."""
        state_py_path = Path("src/ethereum/osaka/state.py")
        assert state_py_path.exists(), "state.py not found"
        
        with open(state_py_path, 'r') as f:
            content = f.read()
        
        # Find increment_nonce function
        func_start = content.find("def increment_nonce")
        assert func_start != -1, "increment_nonce function not found"
        
        func_end = content.find("\ndef ", func_start + 1)
        if func_end == -1:
            func_end = len(content)
        
        func_content = content[func_start:func_end]
        
        # Should accept bal_tracker parameter
        assert "bal_tracker: Optional" in func_content, \
            "increment_nonce doesn't accept bal_tracker parameter"
        
        # Should track nonce changes when bal_tracker is provided
        assert "if bal_tracker is not None:" in func_content, \
            "increment_nonce doesn't check for bal_tracker"
        assert "bal_tracker.track_nonce_change" in func_content, \
            "increment_nonce doesn't call track_nonce_change"
    
    def test_create_operations_pass_tracker(self):
        """Test that CREATE operations pass bal_tracker."""
        system_py_path = Path("src/ethereum/osaka/vm/instructions/system.py")
        assert system_py_path.exists(), "system.py not found"
        
        with open(system_py_path, 'r') as f:
            content = f.read()
        
        # Check generic_create passes bal_tracker
        assert "increment_nonce" in content and "bal_tracker" in content, \
            "CREATE operations don't pass bal_tracker to increment_nonce"
    
    def test_bal_validation_exists(self):
        """Test that BAL validation exists in fork.py."""
        fork_py_path = Path("src/ethereum/osaka/fork.py")
        assert fork_py_path.exists(), "fork.py not found"
        
        with open(fork_py_path, 'r') as f:
            content = f.read()
        
        # Should have BAL-related imports
        assert "from .bal_tracker import StateChangeTracker" in content
        assert "from .bal_utils import compute_bal_hash" in content
        
        # Should validate BAL hash
        assert "bal_hash" in content
        assert "compute_bal_hash" in content
    
    def test_all_bal_files_have_valid_syntax(self):
        """Test all BAL-related files have valid Python syntax."""
        bal_files = [
            "src/ethereum/osaka/bal_builder.py",
            "src/ethereum/osaka/bal_tracker.py", 
            "src/ethereum/osaka/bal_utils.py",
            "src/ethereum/osaka/ssz_types.py",
        ]
        
        for file_path in bal_files:
            path = Path(file_path)
            assert path.exists(), f"{file_path} not found"
            
            with open(path, 'r') as f:
                content = f.read()
            
            try:
                ast.parse(content)
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {file_path}: {e}")


class TestBALEdgeCases:
    """Test BAL edge cases and error handling."""
    
    def test_storage_read_write_deduplication(self):
        """Test that storage slots both read and written only appear in writes."""
        builder = BALBuilder()
        address = Bytes20(b'\x01' * 20)
        slot = Bytes32(b'\x02' * 32)
        
        # Add both read and write for same slot
        builder.add_storage_read(address, slot)
        builder.add_storage_write(address, slot, 0, Bytes32(b'\x03' * 32))
        
        # Build BAL
        bal = builder.build()
        
        # Slot should only appear in storage_changes, not storage_reads
        acc = bal.account_changes[0]
        assert len(acc.storage_changes) == 1
        assert acc.storage_changes[0].slot == slot
        assert len(acc.storage_reads) == 0
    
    def test_deterministic_sorting(self):
        """Test BAL produces deterministic output with sorting."""
        builder = BALBuilder()
        
        # Add addresses in non-sorted order
        addresses = [
            Bytes20(b'\x03' * 20),
            Bytes20(b'\x01' * 20),
            Bytes20(b'\x02' * 20),
        ]
        
        for addr in addresses:
            builder.add_touched_account(addr)
        
        # Build BAL
        bal = builder.build()
        
        # Addresses should be sorted
        assert len(bal.account_changes) == 3
        assert bal.account_changes[0].address == Bytes20(b'\x01' * 20)
        assert bal.account_changes[1].address == Bytes20(b'\x02' * 20)
        assert bal.account_changes[2].address == Bytes20(b'\x03' * 20)
    
    def test_transaction_indexing(self):
        """Test transaction indices are tracked correctly."""
        builder = BALBuilder()
        tracker = StateChangeTracker(builder)
        
        address = Bytes20(b'\x01' * 20)
        mock_state = MagicMock()
        
        # Add changes from different transactions
        tracker.set_transaction_index(0)
        tracker.track_balance_change(address, U256(100), mock_state)
        
        tracker.set_transaction_index(1)
        tracker.track_balance_change(address, U256(200), mock_state)
        
        tracker.set_transaction_index(2)
        tracker.track_balance_change(address, U256(300), mock_state)
        
        # Build BAL
        bal = builder.build()
        
        # Should have all three changes with correct indices
        acc = bal.account_changes[0]
        assert len(acc.balance_changes) == 3
        assert acc.balance_changes[0].tx_index == U32(0)
        assert acc.balance_changes[1].tx_index == U32(1)
        assert acc.balance_changes[2].tx_index == U32(2)
    
    def test_max_code_changes_limit(self):
        """Test MAX_CODE_CHANGES constant is enforced conceptually."""
        # This is more of a specification test
        # In practice, the limit would be enforced during block validation
        assert MAX_CODE_CHANGES == 1, "MAX_CODE_CHANGES should be 1 per EIP-7928"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])