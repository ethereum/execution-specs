"""
Comprehensive tests for Block Access List (BAL) implementation in EIP-7928.

This module tests the complete BAL implementation including:
- Core functionality (tracking, building, validation)
- State modifications and nonce tracking
- Integration with VM instructions
- Edge cases and error handling
"""

import pytest
from unittest.mock import MagicMock, patch
from ethereum_types.bytes import Bytes, Bytes20, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.forks.amsterdam.block_access_lists import (
    BlockAccessListBuilder,
    StateChangeTracker,
    add_balance_change,
    add_code_change,
    add_nonce_change,
    add_storage_read,
    add_storage_write,
    add_touched_account,
    build_block_access_list,
)
from ethereum.forks.amsterdam.block_access_lists.tracker import (
    capture_pre_state,
    set_block_access_index,
    track_balance_change,
    track_code_change,
    track_nonce_change,
    track_storage_write,
)
from ethereum.forks.amsterdam.block_access_lists.rlp_types import (
    MAX_CODE_CHANGES,
    BlockAccessIndex,
    BlockAccessList,
)


class TestBALCore:
    """Test core BAL functionality."""

    def test_block_access_list_builder_initialization(self) -> None:
        """Test BAL builder initializes correctly."""
        builder = BlockAccessListBuilder()
        assert builder.accounts == {}

    def test_block_access_list_builder_add_storage_write(self) -> None:
        """Test adding storage writes to BAL builder."""
        builder = BlockAccessListBuilder()
        address = Bytes20(b"\x01" * 20)
        slot = Bytes32(b"\x02" * 32)
        value = Bytes32(b"\x03" * 32)

        add_storage_write(builder, address, slot, BlockAccessIndex(0), value)

        assert address in builder.accounts
        assert slot in builder.accounts[address].storage_changes
        assert len(builder.accounts[address].storage_changes[slot]) == 1

        change = builder.accounts[address].storage_changes[slot][0]
        assert change.block_access_index == 0
        assert change.new_value == value

    def test_block_access_list_builder_add_storage_read(self) -> None:
        """Test adding storage reads to BAL builder."""
        builder = BlockAccessListBuilder()
        address = Bytes20(b"\x01" * 20)
        slot = Bytes32(b"\x02" * 32)

        add_storage_read(builder, address, slot)

        assert address in builder.accounts
        assert slot in builder.accounts[address].storage_reads

    def test_block_access_list_builder_add_balance_change(self) -> None:
        """Test adding balance changes to BAL builder."""
        builder = BlockAccessListBuilder()
        address = Bytes20(b"\x01" * 20)
        balance = U256(0)

        add_balance_change(builder, address, BlockAccessIndex(0), balance)

        assert address in builder.accounts
        assert len(builder.accounts[address].balance_changes) == 1

        change = builder.accounts[address].balance_changes[0]
        assert change.block_access_index == 0
        assert change.post_balance == balance

    def test_block_access_list_builder_add_nonce_change(self) -> None:
        """Test adding nonce changes to BAL builder."""
        builder = BlockAccessListBuilder()
        address = Bytes20(b"\x01" * 20)
        nonce = 42

        add_nonce_change(builder, address, BlockAccessIndex(0), U64(nonce))

        assert address in builder.accounts
        assert len(builder.accounts[address].nonce_changes) == 1

        change = builder.accounts[address].nonce_changes[0]
        assert change.block_access_index == 0
        assert change.new_nonce == U64(42)

    def test_block_access_list_builder_add_code_change(self) -> None:
        """Test adding code changes to BAL builder."""
        builder = BlockAccessListBuilder()
        address = Bytes20(b"\x01" * 20)
        code = Bytes(b"\x60\x80\x60\x40")

        add_code_change(builder, address, BlockAccessIndex(0), code)

        assert address in builder.accounts
        assert len(builder.accounts[address].code_changes) == 1

        change = builder.accounts[address].code_changes[0]
        assert change.block_access_index == 0
        assert change.new_code == code

    def test_block_access_list_builder_touched_account(self) -> None:
        """Test adding touched accounts without changes."""
        builder = BlockAccessListBuilder()
        address = Bytes20(b"\x01" * 20)

        add_touched_account(builder, address)

        assert address in builder.accounts
        assert builder.accounts[address].storage_changes == {}
        assert builder.accounts[address].storage_reads == set()
        assert builder.accounts[address].balance_changes == []
        assert builder.accounts[address].nonce_changes == []
        assert builder.accounts[address].code_changes == []

    def test_block_access_list_builder_build_complete(self) -> None:
        """Test building a complete BlockAccessList."""
        builder = BlockAccessListBuilder()

        # Add various changes
        address1 = Bytes20(b"\x01" * 20)
        address2 = Bytes20(b"\x02" * 20)
        slot1 = Bytes32(b"\x03" * 32)
        slot2 = Bytes32(b"\x04" * 32)

        # Address 1: storage write and read
        add_storage_write(
            builder,
            address1,
            slot1,
            BlockAccessIndex(1),
            Bytes32(b"\x05" * 32),
        )
        add_storage_read(builder, address1, slot2)
        add_balance_change(builder, address1, BlockAccessIndex(1), U256(0))

        # Address 2: only touched
        add_touched_account(builder, address2)

        # Build BAL
        block_access_list = build_block_access_list(builder)

        assert isinstance(block_access_list, BlockAccessList)
        assert len(block_access_list.account_changes) == 2

        # Verify sorting by address
        assert block_access_list.account_changes[0].address == address1
        assert block_access_list.account_changes[1].address == address2

        # Verify address1 changes
        acc1 = block_access_list.account_changes[0]
        assert len(acc1.storage_changes) == 1
        assert len(acc1.storage_reads) == 1
        assert acc1.storage_reads[0] == slot2  # Direct StorageKey
        assert len(acc1.balance_changes) == 1

        # Verify address2 is empty
        acc2 = block_access_list.account_changes[1]
        assert len(acc2.storage_changes) == 0
        assert len(acc2.storage_reads) == 0
        assert len(acc2.balance_changes) == 0


class TestBALTracker:
    """Test BAL state change tracker functionality."""

    def test_tracker_initialization(self) -> None:
        """Test tracker initializes with BAL builder."""
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)
        assert tracker.block_access_list_builder is builder
        assert tracker.pre_storage_cache == {}
        assert tracker.current_block_access_index == 0

    def test_tracker_set_block_access_index(self) -> None:
        """Test setting block access index."""
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)

        set_block_access_index(tracker, 5)
        assert tracker.current_block_access_index == 5
        # Pre-storage cache should be cleared for new block access index
        assert tracker.pre_storage_cache == {}

    @patch("ethereum.forks.amsterdam.state.get_storage")
    def test_tracker_capture_pre_state(
        self, mock_get_storage: MagicMock
    ) -> None:
        """Test capturing pre-state values."""
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)

        mock_state = MagicMock()
        address = Bytes20(b"\x01" * 20)
        slot = Bytes32(b"\x02" * 32)
        expected_value = U256(42)

        mock_get_storage.return_value = expected_value

        # First call should fetch from state
        value = capture_pre_state(tracker, address, slot, mock_state)
        assert value == expected_value
        mock_get_storage.assert_called_once_with(mock_state, address, slot)

        # Second call should use cache
        mock_get_storage.reset_mock()
        value2 = capture_pre_state(tracker, address, slot, mock_state)
        assert value2 == expected_value
        mock_get_storage.assert_not_called()

    @patch("ethereum.forks.amsterdam.block_access_lists.tracker.capture_pre_state")
    def test_tracker_storage_write_actual_change(
        self, mock_capture: MagicMock
    ) -> None:
        """Test tracking storage write with actual change."""
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)
        tracker.current_block_access_index = 1

        mock_state = MagicMock()
        address = Bytes20(b"\x01" * 20)
        slot = Bytes32(b"\x02" * 32)
        old_value = U256(42)
        new_value = U256(100)

        mock_capture.return_value = old_value

        track_storage_write(tracker, address, slot, new_value, mock_state)

        # Should add storage write since value changed
        assert address in builder.accounts
        assert slot in builder.accounts[address].storage_changes
        assert len(builder.accounts[address].storage_changes[slot]) == 1

        change = builder.accounts[address].storage_changes[slot][0]
        assert change.block_access_index == 1
        assert change.new_value == new_value.to_be_bytes32()

    @patch("ethereum.forks.amsterdam.block_access_lists.tracker.capture_pre_state")
    def test_tracker_storage_write_no_change(
        self, mock_capture: MagicMock
    ) -> None:
        """Test tracking storage write with no actual change."""
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)
        tracker.current_block_access_index = 1

        mock_state = MagicMock()
        address = Bytes20(b"\x01" * 20)
        slot = Bytes32(b"\x02" * 32)
        same_value = U256(42)

        mock_capture.return_value = same_value

        track_storage_write(tracker, address, slot, same_value, mock_state)

        # Should add storage read since value didn't change
        assert address in builder.accounts
        assert slot in builder.accounts[address].storage_reads
        assert slot not in builder.accounts[address].storage_changes

    def test_tracker_balance_change(self) -> None:
        """Test tracking balance changes."""
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)
        tracker.current_block_access_index = 2

        address = Bytes20(b"\x01" * 20)
        new_balance = U256(1000)

        track_balance_change(tracker, address, new_balance)

        assert address in builder.accounts
        assert len(builder.accounts[address].balance_changes) == 1

        change = builder.accounts[address].balance_changes[0]
        assert change.block_access_index == 2
        # Balance is stored as U256 per EIP-7928
        assert change.post_balance == new_balance

    def test_tracker_nonce_change(self) -> None:
        """Test tracking nonce changes."""
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)
        tracker.current_block_access_index = 3

        address = Bytes20(b"\x01" * 20)
        new_nonce = U64(10)

        track_nonce_change(tracker, address, Uint(new_nonce))

        assert address in builder.accounts
        assert len(builder.accounts[address].nonce_changes) == 1

        change = builder.accounts[address].nonce_changes[0]
        assert change.block_access_index == 3
        assert change.new_nonce == new_nonce

    def test_tracker_code_change(self) -> None:
        """Test tracking code changes."""
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)
        tracker.current_block_access_index = 1

        address = Bytes20(b"\x01" * 20)
        new_code = Bytes(b"\x60\x80\x60\x40")

        track_code_change(tracker, address, new_code)

        assert address in builder.accounts
        assert len(builder.accounts[address].code_changes) == 1

        change = builder.accounts[address].code_changes[0]
        assert change.block_access_index == 1
        assert change.new_code == new_code


class TestBALIntegration:
    """Test BAL integration with block execution."""

    def test_system_contract_indices(self) -> None:
        """Test that system contracts use block_access_index 0."""
        builder = BlockAccessListBuilder()

        # Simulate pre-execution system contract changes
        beacon_roots_addr = Bytes20(bytes.fromhex("000F3df6D732807Ef1319fB7B8bB8522d0Beac02"))
        history_addr = Bytes20(bytes.fromhex("0000F90827F1C53a10cb7A02335B175320002935"))

        # These should use index 0
        add_storage_write(
            builder,
            beacon_roots_addr,
            Bytes32(b"\x00" * 32),
            BlockAccessIndex(0),
            Bytes32(b"\x01" * 32),
        )
        add_storage_write(
            builder,
            history_addr,
            Bytes32(b"\x00" * 32),
            BlockAccessIndex(0),
            Bytes32(b"\x02" * 32),
        )

        block_access_list = build_block_access_list(builder)

        for account in block_access_list.account_changes:
            if account.address in [beacon_roots_addr, history_addr]:
                for slot_changes in account.storage_changes:
                    for change in slot_changes.changes:
                        assert change.block_access_index == 0

    def test_transaction_indices(self) -> None:
        """Test that transactions use indices 1 to len(transactions)."""
        builder = BlockAccessListBuilder()

        # Simulate 3 transactions
        for tx_num in range(1, 4):
            address = Bytes20(tx_num.to_bytes(20, "big"))
            # Transactions should use indices 1, 2, 3
            add_balance_change(
                builder, address, BlockAccessIndex(tx_num), U256(0)
            )

        block_access_list = build_block_access_list(builder)

        assert len(block_access_list.account_changes) == 3
        for i, account in enumerate(block_access_list.account_changes):
            assert len(account.balance_changes) == 1
            assert account.balance_changes[0].block_access_index == i + 1

    def test_post_execution_index(self) -> None:
        """Test that post-execution changes use index len(transactions) + 1."""
        builder = BlockAccessListBuilder()
        num_transactions = 5

        # Simulate withdrawal (post-execution)
        withdrawal_addr = Bytes20(b"\xff" * 20)
        post_exec_index = num_transactions + 1

        add_balance_change(
            builder,
            withdrawal_addr,
            BlockAccessIndex(post_exec_index),
            U256(0),
        )

        block_access_list = build_block_access_list(builder)

        for account in block_access_list.account_changes:
            if account.address == withdrawal_addr:
                assert len(account.balance_changes) == 1
                assert (
                    account.balance_changes[0].block_access_index
                    == post_exec_index
                )

    def test_mixed_indices_ordering(self) -> None:
        """Test that mixed indices are properly ordered in the BAL."""
        builder = BlockAccessListBuilder()
        address = Bytes20(b"\x01" * 20)

        # Add changes with different indices (out of order)
        add_balance_change(
            builder, address, BlockAccessIndex(3), U256(0x03030303)
        )
        add_balance_change(
            builder, address, BlockAccessIndex(1), U256(0x01010101)
        )
        add_balance_change(
            builder, address, BlockAccessIndex(2), U256(0x02020202)
        )
        add_balance_change(builder, address, BlockAccessIndex(0), U256(0))

        block_access_list = build_block_access_list(builder)

        assert len(block_access_list.account_changes) == 1
        account = block_access_list.account_changes[0]
        assert len(account.balance_changes) == 4

        # Should be sorted by block_access_index
        for i in range(4):
            assert account.balance_changes[i].block_access_index == i
            expected = (
                U256(0)
                if i == 0
                else U256(int.from_bytes(bytes([i]) * 4, "big"))
            )
            assert account.balance_changes[i].post_balance == expected


class TestRLPEncoding:
    """Test RLP encoding of BAL structures."""

    def test_rlp_encoding_import(self) -> None:
        """Test that RLP encoding utilities can be imported."""
        from ethereum.forks.amsterdam.block_access_lists import (
            compute_block_access_list_hash,
            rlp_encode_block_access_list,
        )

        assert rlp_encode_block_access_list is not None
        assert compute_block_access_list_hash is not None

    def test_rlp_encode_simple_bal(self) -> None:
        """Test RLP encoding of a simple BAL."""
        from ethereum.forks.amsterdam.block_access_lists import (
            rlp_encode_block_access_list,
        )

        builder = BlockAccessListBuilder()
        address = Bytes20(b"\x01" * 20)

        add_balance_change(builder, address, BlockAccessIndex(1), U256(0))

        block_access_list = build_block_access_list(builder)
        encoded = rlp_encode_block_access_list(block_access_list)

        # Should produce valid RLP bytes
        assert isinstance(encoded, (bytes, Bytes))
        assert len(encoded) > 0

    def test_block_access_list_hash_computation(self) -> None:
        """Test BAL hash computation using RLP."""
        from ethereum.forks.amsterdam.block_access_lists import (
            compute_block_access_list_hash,
        )

        builder = BlockAccessListBuilder()
        address = Bytes20(b"\x01" * 20)

        add_storage_write(
            builder,
            address,
            Bytes32(b"\x02" * 32),
            BlockAccessIndex(1),
            Bytes32(b"\x03" * 32),
        )

        block_access_list = build_block_access_list(builder)
        hash_val = compute_block_access_list_hash(block_access_list)

        # Should produce a 32-byte hash
        assert len(hash_val) == 32

        # Same BAL should produce same hash
        hash_val2 = compute_block_access_list_hash(block_access_list)
        assert hash_val == hash_val2

    def test_rlp_encode_complex_bal(self) -> None:
        """Test RLP encoding of a complex BAL with multiple change types."""
        from ethereum.forks.amsterdam.block_access_lists import (
            rlp_encode_block_access_list,
        )

        builder = BlockAccessListBuilder()

        # Add various types of changes
        address = Bytes20(b"\x01" * 20)
        slot = Bytes32(b"\x02" * 32)

        # Pre-execution (index 0)
        add_storage_write(
            builder, address, slot, BlockAccessIndex(0), Bytes32(b"\x03" * 32)
        )

        # Transaction (index 1)
        add_balance_change(builder, address, BlockAccessIndex(1), U256(0))
        add_nonce_change(builder, address, BlockAccessIndex(1), U64(1))

        # Post-execution (index 2)
        add_code_change(
            builder, address, BlockAccessIndex(2), Bytes(b"\x60\x80")
        )

        block_access_list = build_block_access_list(builder)
        encoded = rlp_encode_block_access_list(block_access_list)

        # Should produce valid RLP bytes
        assert isinstance(encoded, (bytes, Bytes))
        assert len(encoded) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_bal(self) -> None:
        """Test building an empty BAL."""
        builder = BlockAccessListBuilder()
        block_access_list = build_block_access_list(builder)

        assert isinstance(block_access_list, BlockAccessList)
        assert len(block_access_list.account_changes) == 0

    def test_multiple_changes_same_slot(self) -> None:
        """Test multiple changes to the same storage slot."""
        builder = BlockAccessListBuilder()
        address = Bytes20(b"\x01" * 20)
        slot = Bytes32(b"\x02" * 32)

        # Multiple writes to same slot at different indices
        add_storage_write(
            builder, address, slot, BlockAccessIndex(0), Bytes32(b"\x00" * 32)
        )
        add_storage_write(
            builder, address, slot, BlockAccessIndex(1), Bytes32(b"\x01" * 32)
        )
        add_storage_write(
            builder, address, slot, BlockAccessIndex(2), Bytes32(b"\x02" * 32)
        )

        block_access_list = build_block_access_list(builder)

        assert len(block_access_list.account_changes) == 1
        account = block_access_list.account_changes[0]
        assert len(account.storage_changes) == 1

        slot_changes = account.storage_changes[0]
        assert slot_changes.slot == slot
        assert len(slot_changes.changes) == 3

        # Changes should be sorted by index
        for i in range(3):
            assert slot_changes.changes[i].block_access_index == i

    def test_max_code_changes_constant(self) -> None:
        """Test that MAX_CODE_CHANGES constant is available."""
        assert MAX_CODE_CHANGES == 1

    def test_address_sorting(self) -> None:
        """Test that addresses are sorted lexicographically in BAL."""
        builder = BlockAccessListBuilder()

        # Add addresses in reverse order
        addresses = [
            Bytes20(b"\xff" * 20),
            Bytes20(b"\xaa" * 20),
            Bytes20(b"\x11" * 20),
            Bytes20(b"\x00" * 20),
        ]

        for addr in addresses:
            add_touched_account(builder, addr)

        block_access_list = build_block_access_list(builder)

        # Should be sorted lexicographically
        sorted_addresses = sorted(addresses)
        for i, account in enumerate(block_access_list.account_changes):
            assert account.address == sorted_addresses[i]


class TestValueCalls:
    """Test value call scenarios including 0 ETH calls."""
    
    def test_zero_eth_value_call_tracks_address_without_balance(self) -> None:
        """Test that 0 ETH calls track recipient address without balance changes."""
        from ethereum.forks.amsterdam.block_access_lists.tracker import track_address_access
        
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)
        set_block_access_index(tracker, Uint(1))
        
        recipient = Bytes20(b"\x02" * 20)
        
        # Track only the address access without balance change
        track_address_access(tracker, recipient)
        
        block_access_list = build_block_access_list(builder)
        
        # Verify recipient is tracked without balance changes
        recipient_found = False
        for account in block_access_list.account_changes:
            if account.address == recipient:
                recipient_found = True
                assert len(account.balance_changes) == 0
                break
        
        assert recipient_found
    
    def test_nonzero_eth_value_call_tracks_with_balance(self) -> None:
        """Test that non-zero ETH calls track addresses with balance changes."""
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)
        set_block_access_index(tracker, Uint(1))
        
        sender = Bytes20(b"\x01" * 20)
        recipient = Bytes20(b"\x02" * 20)
        
        # Track balance changes for value transfer
        track_balance_change(tracker, sender, U256(900))
        track_balance_change(tracker, recipient, U256(100))
        
        block_access_list = build_block_access_list(builder)
        
        # Verify both addresses tracked with balance changes
        sender_found = False
        recipient_found = False
        
        for account in block_access_list.account_changes:
            if account.address == sender:
                sender_found = True
                assert len(account.balance_changes) == 1
                assert account.balance_changes[0].post_balance == U256(900)
            elif account.address == recipient:
                recipient_found = True
                assert len(account.balance_changes) == 1
                assert account.balance_changes[0].post_balance == U256(100)
        
        assert sender_found and recipient_found
    
    def test_multiple_zero_eth_calls_deduplication(self) -> None:
        """Test that multiple 0 ETH calls to same address are deduplicated."""
        from ethereum.forks.amsterdam.block_access_lists.tracker import track_address_access
        
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)
        set_block_access_index(tracker, Uint(1))
        
        recipient = Bytes20(b"\x02" * 20)
        
        # Multiple calls to same address
        track_address_access(tracker, recipient)
        track_address_access(tracker, recipient)
        track_address_access(tracker, recipient)
        
        block_access_list = build_block_access_list(builder)
        
        # Verify address appears exactly once without balance changes
        recipient_count = sum(1 for account in block_access_list.account_changes 
                            if account.address == recipient)
        assert recipient_count == 1
        
        for account in block_access_list.account_changes:
            if account.address == recipient:
                assert len(account.balance_changes) == 0


class TestRevertScenarios:
    """Test block access list behavior during reverts."""
    
    @patch("ethereum.forks.amsterdam.state.get_storage")
    def test_storage_write_becomes_read_on_revert(self, mock_get_storage: MagicMock) -> None:
        """Test that storage writes become reads when transaction reverts."""
        from ethereum.forks.amsterdam.block_access_lists.tracker import (
            begin_call_frame,
            rollback_call_frame,
            track_storage_write,
            track_storage_read,
        )
        
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)
        set_block_access_index(tracker, Uint(1))
        
        address = Bytes20(b"\x01" * 20)
        slot1 = Bytes32(b"\x01" * 32)
        slot2 = Bytes32(b"\x02" * 32)
        
        # Begin call frame
        begin_call_frame(tracker)
        
        # Mock state for storage operations
        class MockState:
            _storage_tries = {}
            
        state = MockState()
        
        # Mock get_storage to return U256(0) for reads
        mock_get_storage.return_value = U256(0)
        
        # Track storage operations that will be reverted
        track_storage_read(tracker, address, slot1, state)  # Read slot 0x01
        
        # Mock get_storage to return old value for slot2
        mock_get_storage.return_value = U256(10)  # Different from new value
        
        # Storage write to slot 0x02 (will be reverted)
        track_storage_write(tracker, address, slot2, U256(42), state)
        
        # Rollback the call frame (simulating revert)
        rollback_call_frame(tracker)
        
        # Build and check the access list
        block_access_list = build_block_access_list(builder)
        
        # Find the account in the access list
        account_found = False
        for account in block_access_list.account_changes:
            if account.address == address:
                account_found = True
                # Both slots should be in storage_reads
                assert slot1 in builder.accounts[address].storage_reads
                assert slot2 in builder.accounts[address].storage_reads
                # No storage changes should exist
                assert len(account.storage_changes) == 0
                break
        
        assert account_found
    
    def test_balance_changes_removed_on_revert(self) -> None:
        """Test that balance changes are removed on revert but address remains."""
        from ethereum.forks.amsterdam.block_access_lists.tracker import (
            begin_call_frame,
            rollback_call_frame,
        )
        
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)
        set_block_access_index(tracker, Uint(1))
        
        address = Bytes20(b"\x01" * 20)
        
        # Begin call frame
        begin_call_frame(tracker)
        
        # Track balance change that will be reverted
        track_balance_change(tracker, address, U256(1000))
        
        # Rollback the call frame
        rollback_call_frame(tracker)
        
        # Build and check the access list
        block_access_list = build_block_access_list(builder)
        
        # Address should still be in access list but without balance changes
        account_found = False
        for account in block_access_list.account_changes:
            if account.address == address:
                account_found = True
                assert len(account.balance_changes) == 0
                break
        
        assert account_found
    
    def test_nested_call_frames_with_partial_revert(self) -> None:
        """Test nested call frames where inner frame reverts but outer succeeds."""
        from ethereum.forks.amsterdam.block_access_lists.tracker import (
            begin_call_frame,
            commit_call_frame,
            rollback_call_frame,
        )
        
        builder = BlockAccessListBuilder()
        tracker = StateChangeTracker(builder)
        set_block_access_index(tracker, Uint(1))
        
        address1 = Bytes20(b"\x01" * 20)
        address2 = Bytes20(b"\x02" * 20)
        
        # Outer call frame
        begin_call_frame(tracker)
        track_balance_change(tracker, address1, U256(900))
        
        # Inner call frame (will be reverted)
        begin_call_frame(tracker)
        track_balance_change(tracker, address2, U256(100))
        
        # Rollback inner frame
        rollback_call_frame(tracker)
        
        # Commit outer frame
        commit_call_frame(tracker)
        
        # Build and check the access list
        block_access_list = build_block_access_list(builder)
        
        # address1 should have balance change, address2 should not
        address1_found = False
        address2_found = False
        
        for account in block_access_list.account_changes:
            if account.address == address1:
                address1_found = True
                assert len(account.balance_changes) == 1
                assert account.balance_changes[0].post_balance == U256(900)
            elif account.address == address2:
                address2_found = True
                assert len(account.balance_changes) == 0
        
        assert address1_found
        assert address2_found  # Address2 touched but no changes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
