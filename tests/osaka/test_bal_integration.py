"""BAL integration tests."""

import pytest
from typing import Dict, List

from ethereum.osaka.bal_builder import BALBuilder
from ethereum.osaka.bal_tracker import StateChangeTracker
from ethereum.osaka.bal_utils import compute_bal_hash, validate_bal_structure
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U16, U64, U256


class TestRealWorldScenarios:
    """Test real-world transaction scenarios."""
    
    def test_dex_swap(self):
        """Test DEX swap scenario."""
        builder = BALBuilder()
        
        user = Bytes(b'\x01' * 20)
        token_a = Bytes(b'\x0a' * 20)
        token_b = Bytes(b'\x0b' * 20)
        router = Bytes(b'\xde' * 20)
        pair = Bytes(b'\xab' * 20)
        
        approval_slot = Bytes32(user + router)
        approval_amount = (1000 * 10**6).to_bytes(32, 'big')
        builder.add_storage_write(token_a, approval_slot, 0, approval_amount)
        
        user_balance_slot = Bytes32(user + b'\x00' * 12)
        reserves_slot = Bytes32(b'\x00' * 31 + b'\x08')
        
        builder.add_storage_read(token_a, user_balance_slot)
        builder.add_storage_read(pair, reserves_slot)
        
        new_balance = (500 * 10**6).to_bytes(32, 'big')
        builder.add_storage_write(token_a, user_balance_slot, 1, new_balance)
        
        gas_cost = (21000 * 50 * 10**9).to_bytes(12, 'big')
        builder.add_balance_change(user, 1, gas_cost)
        
        bal = builder.build()
        validate_bal_structure(bal)
        
        assert len(bal.account_changes) >= 3
        
        user_account = next((acc for acc in bal.account_changes if acc.address == user), None)
        assert user_account is not None
        assert len(user_account.balance_changes) == 1
    
    def test_contract_deployment(self):
        """Test contract deployment scenario."""
        builder = BALBuilder()
        
        deployer = Bytes(b'\x01' * 20)
        new_contract = Bytes(b'\x02' * 20)
        
        builder.add_nonce_change(deployer, 0, 5)
        
        gas_cost = (2000000 * 20 * 10**9).to_bytes(12, 'big')
        builder.add_balance_change(deployer, 0, gas_cost)
        
        contract_code = Bytes(b'\x60\x80\x60\x40\x52' * 20)
        builder.add_code_change(new_contract, 0, contract_code)
        
        owner_slot = Bytes32(b'\x00' * 32)
        builder.add_storage_write(new_contract, owner_slot, 0, Bytes32(deployer + b'\x00' * 12))
        
        bal = builder.build()
        validate_bal_structure(bal)
        
        contract_account = next((acc for acc in bal.account_changes if acc.address == new_contract), None)
        assert contract_account is not None
        assert len(contract_account.code_changes) == 1
        assert len(contract_account.storage_changes) == 1
        
        deployer_account = next((acc for acc in bal.account_changes if acc.address == deployer), None)
        assert deployer_account is not None
        assert len(deployer_account.nonce_changes) == 1
        assert deployer_account.nonce_changes[0].new_nonce == U64(5)
    
    def test_multi_transaction_block(self):
        """Test complex block with multiple transaction types."""
        builder = BALBuilder()
        
        users = [Bytes(bytes([i]) + b'\x00' * 19) for i in range(1, 4)]
        contract = Bytes(b'\x10' * 20)
        miner = Bytes(b'\xee' * 20)
        
        sender, recipient = users[0], users[1]
        transfer_amount = (100 * 10**18).to_bytes(12, 'big')
        gas_cost = (21000 * 20 * 10**9).to_bytes(12, 'big')
        
        builder.add_balance_change(sender, 0, gas_cost)
        builder.add_balance_change(recipient, 0, transfer_amount)
        
        trader = users[2]
        
        pool_slot = Bytes32(b'\x00' * 31 + b'\x01')
        builder.add_storage_read(contract, pool_slot)
        
        new_reserves = (5000 * 10**18).to_bytes(32, 'big')
        builder.add_storage_write(contract, pool_slot, 1, new_reserves)
        
        trader_gas = (150000 * 25 * 10**9).to_bytes(12, 'big')
        builder.add_balance_change(trader, 1, trader_gas)
        
        total_fees = int.from_bytes(gas_cost, 'big') + int.from_bytes(trader_gas, 'big')
        builder.add_balance_change(miner, 1, total_fees.to_bytes(12, 'big'))
        
        bal = builder.build()
        validate_bal_structure(bal)
        
        assert len(bal.account_changes) >= 5
        
        all_tx_indices = set()
        for account in bal.account_changes:
            for balance_change in account.balance_changes:
                all_tx_indices.add(balance_change.tx_index)
            for slot_changes in account.storage_changes:
                for change in slot_changes.changes:
                    all_tx_indices.add(change.tx_index)
        
        expected_indices = {U16(0), U16(1)}
        assert all_tx_indices.issubset(expected_indices)
    
    def test_selfdestruct_scenario(self):
        """Test SELFDESTRUCT with beneficiary transfer."""
        builder = BALBuilder()
        
        victim_contract = Bytes(b'\x01' * 20)
        beneficiary = Bytes(b'\x02' * 20)
        caller = Bytes(b'\x03' * 20)
        
        contract_balance = (50 * 10**18).to_bytes(12, 'big')
        builder.add_balance_change(beneficiary, 0, contract_balance)
        
        builder.add_touched_account(victim_contract)
        
        gas_cost = (30000 * 20 * 10**9).to_bytes(12, 'big')
        builder.add_balance_change(caller, 0, gas_cost)
        
        bal = builder.build()
        validate_bal_structure(bal)
        
        beneficiary_account = next((acc for acc in bal.account_changes if acc.address == beneficiary), None)
        assert beneficiary_account is not None
        assert len(beneficiary_account.balance_changes) == 1


class TestStateIntegration:
    """Test integration with state transition functionality."""
    
    def test_tracker_transaction_indexing(self):
        """Test transaction index tracking."""
        builder = BALBuilder()
        tracker = StateChangeTracker(builder)
        
        address = Bytes(b'\x01' * 20)
        
        tracker.set_transaction_index(0)
        tracker.track_address_access(address)
        
        tracker.set_transaction_index(1)
        tracker.track_address_access(address)
        
        bal = builder.build()
        assert len(bal.account_changes) >= 1
    
    def test_withdrawal_processing(self):
        """Test consensus layer withdrawal processing."""
        builder = BALBuilder()
        
        validators = [
            Bytes(b'\x01' * 20),
            Bytes(b'\x02' * 20),
            Bytes(b'\x03' * 20),
        ]
        
        amounts = [32 * 10**18, 1 * 10**18, 0.5 * 10**18]
        
        for i, (validator, amount) in enumerate(zip(validators, amounts)):
            withdrawal_tx_index = 1000 + i
            current_balance = 1000 * 10**18
            new_balance = (current_balance + amount).to_bytes(12, 'big')
            
            builder.add_balance_change(validator, withdrawal_tx_index, new_balance)
        
        bal = builder.build()
        validate_bal_structure(bal)
        
        assert len(bal.account_changes) == len(validators)
        
        for i, validator in enumerate(validators):
            validator_account = next((acc for acc in bal.account_changes if acc.address == validator), None)
            assert validator_account is not None
            assert len(validator_account.balance_changes) == 1
    
    def test_complex_storage_patterns(self):
        """Test complex storage access patterns."""
        builder = BALBuilder()
        
        contract = Bytes(b'\x01' * 20)
        base_slot = Bytes32(b'\x00' * 32)
        
        for i in range(5):
            key = Bytes32(bytes([i]) + b'\x00' * 31)
            mapping_slot = Bytes32((int.from_bytes(key, 'big') + int.from_bytes(base_slot, 'big')).to_bytes(32, 'big'))
            builder.add_storage_read(contract, mapping_slot)
        
        for i in range(2, 4):
            key = Bytes32(bytes([i]) + b'\x00' * 31)
            mapping_slot = Bytes32((int.from_bytes(key, 'big') + int.from_bytes(base_slot, 'big')).to_bytes(32, 'big'))
            value = Bytes32(b'\x00' * 31 + bytes([i * 10]))
            builder.add_storage_write(contract, mapping_slot, 0, value)
        
        bal = builder.build()
        validate_bal_structure(bal)
        
        account = bal.account_changes[0]
        
        assert len(account.storage_reads) == 3
        assert len(account.storage_changes) == 2
        
        read_slots = {sr.slot for sr in account.storage_reads}
        write_slots = {sc.slot for sc in account.storage_changes}
        assert len(read_slots.intersection(write_slots)) == 0


def test_hash_consistency_across_scenarios():
    """Test hash consistency across different scenarios."""
    scenarios = []
    
    for scenario_id in range(3):
        builder = BALBuilder()
        address = Bytes(bytes([scenario_id + 1]) + b'\x00' * 19)
        
        if scenario_id == 0:
            builder.add_storage_write(address, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x01' * 32))
        elif scenario_id == 1:
            builder.add_balance_change(address, 0, b'\x00' * 12)
        else:
            builder.add_storage_write(address, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x01' * 32))
            builder.add_balance_change(address, 0, b'\x00' * 12)
        
        bal = builder.build()
        validate_bal_structure(bal)
        scenarios.append(compute_bal_hash(bal))
    
    assert len(set(scenarios)) == 3
    
    for hash_val in scenarios:
        assert len(hash_val) == 32


if __name__ == "__main__":
    pytest.main([__file__])