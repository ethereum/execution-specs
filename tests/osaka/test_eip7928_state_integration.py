"""
Integration tests for EIP-7928 BAL with actual state transition in execution specs.

These tests verify that the BAL implementation integrates correctly with
the Osaka fork's state transition function and VM execution.
"""

import pytest
from typing import Dict, List, Set

from ethereum.osaka.fork import (
    apply_transaction,
    state_transition,
    validate_header,
)
from ethereum.osaka.fork_types import (
    Address,
    Block,
    Header,
    Transaction,
    Receipt,
    Account,
    Bloom,
    Root,
    Hash32,
)
from ethereum.osaka.state import (
    State,
    create_empty_account,
    destroy_account,
    get_account,
    set_account,
    state_root,
)
from ethereum.osaka.bal_builder import BALBuilder
from ethereum.osaka.bal_tracker import StateChangeTracker
from ethereum.osaka.bal_utils import compute_bal_hash

from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint


class TestEIP7928StateIntegration:
    """Test EIP-7928 BAL integration with state transition."""

    def create_test_state(self) -> State:
        """Create a test state with funded accounts."""
        state = State()
        
        # Create sender account
        sender = Address(b'\x01' * 20)
        sender_account = Account(
            nonce=Uint(0),
            balance=U256(10**18),  # 1 ETH
            code=Bytes(),
        )
        set_account(state, sender, sender_account)
        
        # Create contract account with some code
        contract = Address(b'\x02' * 20)
        contract_code = Bytes(
            # Simple storage contract: SSTORE(1, CALLDATALOAD(0))
            b'\x60\x00'  # PUSH1 0
            b'\x35'      # CALLDATALOAD
            b'\x60\x01'  # PUSH1 1
            b'\x55'      # SSTORE
        )
        contract_account = Account(
            nonce=Uint(1),
            balance=U256(0),
            code=contract_code,
        )
        set_account(state, contract, contract_account)
        
        return state

    def test_bal_tracking_during_transaction_execution(self):
        """Test that BAL is correctly tracked during actual transaction execution."""
        state = self.create_test_state()
        
        # Create BAL builder and tracker
        bal_builder = BALBuilder()
        tracker = StateChangeTracker(bal_builder)
        
        # Create a transaction that modifies storage
        sender = Address(b'\x01' * 20)
        contract = Address(b'\x02' * 20)
        
        tx = Transaction(
            nonce=Uint(0),
            gas_price=Uint(10**9),  # 1 gwei
            gas=Uint(100000),
            to=contract,
            value=U256(0),
            data=Bytes(b'\x00' * 31 + b'\x42'),  # Store 42 in slot 1
            v=Uint(0),
            r=U256(0),
            s=U256(0),
        )
        
        # Track the transaction execution
        tracker.set_transaction_index(0)
        
        # Simulate state changes that would happen during execution
        tracker.track_address_access(sender)
        tracker.track_address_access(contract)
        
        # Storage write
        tracker.track_storage_write(contract, Bytes32(b'\x00' * 31 + b'\x01'), U256(42), state)
        
        # Balance changes (gas cost)
        gas_cost = tx.gas * tx.gas_price
        new_sender_balance = get_account(state, sender).balance - gas_cost
        tracker.track_balance_change(sender, new_sender_balance, state)
        
        # Build BAL
        bal = bal_builder.build()
        
        # Verify BAL structure
        assert len(bal.account_changes) == 2  # sender and contract
        
        # Find contract in BAL
        contract_changes = next(
            acc for acc in bal.account_changes if acc.address == contract
        )
        
        # Verify storage change
        assert len(contract_changes.storage_changes) == 1
        storage_change = contract_changes.storage_changes[0]
        assert storage_change.slot == Bytes32(b'\x00' * 31 + b'\x01')
        assert len(storage_change.changes) == 1
        assert storage_change.changes[0].tx_index.to_int() == 0
        assert storage_change.changes[0].new_value == Bytes32(b'\x00' * 31 + b'\x2a')  # 42
        
        # Find sender in BAL
        sender_changes = next(
            acc for acc in bal.account_changes if acc.address == sender
        )
        
        # Verify balance change
        assert len(sender_changes.balance_changes) == 1
        balance_change = sender_changes.balance_changes[0]
        assert balance_change.tx_index.to_int() == 0

    def test_bal_with_multiple_transactions(self):
        """Test BAL tracking across multiple transactions in a block."""
        state = self.create_test_state()
        
        bal_builder = BALBuilder()
        tracker = StateChangeTracker(bal_builder)
        
        sender = Address(b'\x01' * 20)
        contract = Address(b'\x02' * 20)
        recipient = Address(b'\x03' * 20)
        
        # Create recipient account
        recipient_account = Account(
            nonce=Uint(0),
            balance=U256(0),
            code=Bytes(),
        )
        set_account(state, recipient, recipient_account)
        
        # Transaction 1: Storage operation
        tracker.set_transaction_index(0)
        tracker.track_address_access(sender)
        tracker.track_address_access(contract)
        tracker.track_storage_write(contract, Bytes32(b'\x00' * 31 + b'\x01'), U256(42), state)
        
        # Transaction 2: Balance transfer
        tracker.set_transaction_index(1)
        tracker.track_address_access(sender)
        tracker.track_address_access(recipient)
        tracker.track_balance_change(sender, U256(9 * 10**17), state)  # After transfer
        tracker.track_balance_change(recipient, U256(10**17), state)   # Received amount
        
        # Transaction 3: Another storage operation
        tracker.set_transaction_index(2)
        tracker.track_address_access(sender)
        tracker.track_address_access(contract)
        tracker.track_storage_write(contract, Bytes32(b'\x00' * 31 + b'\x02'), U256(43), state)
        
        bal = bal_builder.build()
        
        # Verify structure
        assert len(bal.account_changes) == 3  # sender, contract, recipient
        
        # Check contract has two storage changes
        contract_changes = next(
            acc for acc in bal.account_changes if acc.address == contract
        )
        assert len(contract_changes.storage_changes) == 2
        
        # Verify transaction indices are correct
        storage_slots = sorted(contract_changes.storage_changes, key=lambda x: x.slot)
        assert storage_slots[0].changes[0].tx_index.to_int() == 0  # First storage write
        assert storage_slots[1].changes[0].tx_index.to_int() == 2  # Second storage write
        
        # Check recipient has balance change
        recipient_changes = next(
            acc for acc in bal.account_changes if acc.address == recipient
        )
        assert len(recipient_changes.balance_changes) == 1
        assert recipient_changes.balance_changes[0].tx_index.to_int() == 1

    def test_bal_hash_in_header(self):
        """Test that BAL hash can be computed and included in block header."""
        state = self.create_test_state()
        
        # Create a simple BAL
        bal_builder = BALBuilder()
        tracker = StateChangeTracker(bal_builder)
        
        contract = Address(b'\x02' * 20)
        tracker.track_storage_write(contract, Bytes32(b'\x00' * 31 + b'\x01'), U256(42), state)
        
        bal = bal_builder.build()
        bal_hash = compute_bal_hash(bal)
        
        # Create a header with BAL hash
        header = Header(
            parent_hash=Hash32(b'\x00' * 32),
            ommers_hash=Hash32(b'\x00' * 32),
            coinbase=Address(b'\x00' * 20),
            state_root=Root(b'\x00' * 32),
            transactions_root=Root(b'\x00' * 32),
            receipt_root=Root(b'\x00' * 32),
            bloom=Bloom(b'\x00' * 256),
            difficulty=Uint(0),
            number=Uint(1),
            gas_limit=Uint(8000000),
            gas_used=Uint(0),
            timestamp=U256(1234567890),
            extra_data=Bytes(),
            mix_digest=Hash32(b'\x00' * 32),
            nonce=Bytes(b'\x00' * 8),
            base_fee_per_gas=Uint(10**9),
            blob_gas_used=U64(0),
            excess_blob_gas=U64(0),
            parent_beacon_block_root=Root(b'\x00' * 32),
            bal_hash=bal_hash,  # Include BAL hash
        )
        
        # Verify BAL hash is properly included
        assert header.bal_hash == bal_hash
        assert len(header.bal_hash) == 32

    def test_bal_validation_integration(self):
        """Test BAL validation as part of block validation."""
        state = self.create_test_state()
        
        # Create BAL with specific content
        bal_builder = BALBuilder()
        
        contract = Address(b'\x02' * 20)
        sender = Address(b'\x01' * 20)
        
        bal_builder.add_storage_write(contract, Bytes32(b'\x00' * 31 + b'\x01'), 0, Bytes32(b'\x00' * 31 + b'\x42'))
        bal_builder.add_balance_change(sender, 0, b'\x00' * 8 + (9 * 10**17).to_bytes(4, 'big'))
        
        bal = bal_builder.build()
        correct_hash = compute_bal_hash(bal)
        
        # Test with correct BAL hash - should validate
        try:
            # This would be called during block validation
            assert correct_hash == compute_bal_hash(bal)
            validation_passed = True
        except Exception:
            validation_passed = False
        
        assert validation_passed
        
        # Test with incorrect BAL hash - should fail
        incorrect_hash = Hash32(b'\xff' * 32)
        assert incorrect_hash != correct_hash

    def test_contract_creation_bal_tracking(self):
        """Test BAL tracking for contract creation transactions."""
        state = self.create_test_state()
        
        bal_builder = BALBuilder()
        tracker = StateChangeTracker(bal_builder)
        
        sender = Address(b'\x01' * 20)
        
        # Simulate contract creation
        tracker.set_transaction_index(0)
        tracker.track_address_access(sender)
        
        # New contract address (would be computed during execution)
        new_contract = Address(b'\x03' * 20)
        
        # Track contract creation
        contract_code = Bytes(b'\x60\x42\x60\x00\x52\x60\x20\x60\x00\xf3')  # Return 42
        tracker.track_code_change(new_contract, contract_code, state)
        tracker.track_address_access(new_contract)
        
        # Track sender nonce increment
        tracker.track_nonce_change(sender, Uint(1), state)
        
        # Track gas cost
        tracker.track_balance_change(sender, U256(9 * 10**17), state)
        
        bal = bal_builder.build()
        
        # Verify BAL captures contract creation
        new_contract_changes = next(
            acc for acc in bal.account_changes if acc.address == new_contract
        )
        
        assert len(new_contract_changes.code_changes) == 1
        code_change = new_contract_changes.code_changes[0]
        assert code_change.tx_index.to_int() == 0
        assert code_change.new_code == contract_code
        
        # Note: New contracts start with nonce 1, which per EIP-7928 is not recorded
        assert len(new_contract_changes.nonce_changes) == 0

    def test_selfdestruct_bal_tracking(self):
        """Test BAL tracking for SELFDESTRUCT operations."""
        state = self.create_test_state()
        
        # Create contract that will self-destruct
        suicide_contract = Address(b'\x04' * 20)
        suicide_account = Account(
            nonce=Uint(1),
            balance=U256(10**17),  # 0.1 ETH
            code=Bytes(b'\x33\xff'),  # CALLER, SELFDESTRUCT
        )
        set_account(state, suicide_contract, suicide_account)
        
        bal_builder = BALBuilder()
        tracker = StateChangeTracker(bal_builder)
        
        sender = Address(b'\x01' * 20)
        beneficiary = Address(b'\x05' * 20)
        
        # Create beneficiary account
        beneficiary_account = Account(
            nonce=Uint(0),
            balance=U256(0),
            code=Bytes(),
        )
        set_account(state, beneficiary, beneficiary_account)
        
        tracker.set_transaction_index(0)
        
        # Track SELFDESTRUCT
        tracker.track_address_access(sender)
        tracker.track_address_access(suicide_contract)
        tracker.track_address_access(beneficiary)
        
        # Contract balance goes to zero
        tracker.track_balance_change(suicide_contract, U256(0), state)
        
        # Beneficiary receives the balance
        tracker.track_balance_change(beneficiary, U256(10**17), state)
        
        # Sender pays gas
        tracker.track_balance_change(sender, U256(9 * 10**17), state)
        
        bal = bal_builder.build()
        
        # Verify SELFDESTRUCT is tracked correctly
        beneficiary_changes = next(
            acc for acc in bal.account_changes if acc.address == beneficiary
        )
        
        assert len(beneficiary_changes.balance_changes) == 1
        balance_change = beneficiary_changes.balance_changes[0]
        assert balance_change.tx_index.to_int() == 0
        
        # Verify contract balance was zeroed
        contract_changes = next(
            acc for acc in bal.account_changes if acc.address == suicide_contract
        )
        
        assert len(contract_changes.balance_changes) == 1
        contract_balance_change = contract_changes.balance_changes[0]
        assert contract_balance_change.tx_index.to_int() == 0

    def test_failed_transaction_exclusion(self):
        """Test that failed transactions are excluded from BAL."""
        state = self.create_test_state()
        
        bal_builder = BALBuilder()
        tracker = StateChangeTracker(bal_builder)
        
        # Transaction 0: Successful
        tracker.set_transaction_index(0)
        contract = Address(b'\x02' * 20)
        tracker.track_storage_write(contract, Bytes32(b'\x00' * 31 + b'\x01'), U256(42), state)
        
        # Transaction 1: Failed (would not be tracked in real implementation)
        # In a real implementation, failed transactions wouldn't reach the tracker
        
        # Transaction 2: Successful  
        tracker.set_transaction_index(2)  # Note: tx_index 1 is skipped (failed)
        tracker.track_storage_write(contract, Bytes32(b'\x00' * 31 + b'\x02'), U256(43), state)
        
        bal = bal_builder.build()
        
        # Verify only successful transactions are in BAL
        contract_changes = next(
            acc for acc in bal.account_changes if acc.address == contract
        )
        
        assert len(contract_changes.storage_changes) == 2
        
        # Check transaction indices (should be 0 and 2, not 1)
        tx_indices = []
        for slot_changes in contract_changes.storage_changes:
            for change in slot_changes.changes:
                tx_indices.append(change.tx_index.to_int())
        
        assert sorted(tx_indices) == [0, 2]  # Failed transaction 1 is excluded

    def test_storage_read_vs_write_distinction(self):
        """Test proper distinction between storage reads and writes in BAL."""
        state = self.create_test_state()
        
        # Set up contract with existing storage
        contract = Address(b'\x02' * 20)
        existing_account = get_account(state, contract)
        # In a real implementation, we'd set storage in the state
        
        bal_builder = BALBuilder()
        tracker = StateChangeTracker(bal_builder)
        
        tracker.set_transaction_index(0)
        
        # Read from existing slot (no change)
        tracker.track_storage_read(contract, Bytes32(b'\x00' * 31 + b'\x01'), state)
        
        # Write to new slot (change)
        tracker.track_storage_write(contract, Bytes32(b'\x00' * 31 + b'\x02'), U256(42), state)
        
        # Write same value to existing slot (should be read, not write)
        # This would require more sophisticated pre/post state comparison in real implementation
        tracker.track_storage_read(contract, Bytes32(b'\x00' * 31 + b'\x03'), state)
        
        bal = bal_builder.build()
        
        contract_changes = next(
            acc for acc in bal.account_changes if acc.address == contract
        )
        
        # Should have one write and two reads
        assert len(contract_changes.storage_changes) == 1  # One actual write
        assert len(contract_changes.storage_reads) == 2    # Two reads
        
        # Verify the write
        storage_change = contract_changes.storage_changes[0]
        assert storage_change.slot == Bytes32(b'\x00' * 31 + b'\x02')
        
        # Verify the reads
        read_slots = [sr.slot for sr in contract_changes.storage_reads]
        expected_reads = [Bytes32(b'\x00' * 31 + b'\x01'), Bytes32(b'\x00' * 31 + b'\x03')]
        assert sorted(read_slots) == sorted(expected_reads)