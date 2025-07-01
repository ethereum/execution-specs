"""BAL SSZ encoding and serialization tests."""

import pytest
from typing import List, Optional

from ethereum.osaka.bal_builder import BALBuilder
from ethereum.osaka.bal_utils import compute_bal_hash
from ethereum.osaka.ssz_types import (
    BlockAccessList, AccountChanges, StorageChange, 
    MAX_CODE_SIZE, MAX_TXS, MAX_ACCOUNTS
)
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U16, U64, U256

# Try to import SSZ library, skip tests if not available
try:
    import ssz
    SSZ_AVAILABLE = True
except ImportError:
    SSZ_AVAILABLE = False


class TestSSZBasics:
    """Test basic SSZ encoding and decoding."""
    
    @pytest.mark.skipif(not SSZ_AVAILABLE, reason="SSZ library not available")
    def test_empty_bal_ssz(self):
        """Test SSZ encoding of empty BAL."""
        builder = BALBuilder()
        bal = builder.build()
        
        encoded = ssz.encode(bal, sedes=BlockAccessList)
        decoded = ssz.decode(encoded, sedes=BlockAccessList)
        
        assert len(decoded.account_changes) == 0
        assert isinstance(decoded, BlockAccessList)
    
    @pytest.mark.skipif(not SSZ_AVAILABLE, reason="SSZ library not available")
    def test_simple_bal_ssz(self):
        """Test SSZ encoding of simple BAL."""
        builder = BALBuilder()
        address = Bytes(b'\x01' * 20)
        
        builder.add_storage_write(address, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x01' * 32))
        builder.add_balance_change(address, 0, b'\x00' * 12)
        
        bal = builder.build()
        
        encoded = ssz.encode(bal, sedes=BlockAccessList)
        decoded = ssz.decode(encoded, sedes=BlockAccessList)
        
        assert len(decoded.account_changes) == 1
        account = decoded.account_changes[0]
        assert account.address == address
        assert len(account.storage_changes) == 1
        assert len(account.balance_changes) == 1
    
    @pytest.mark.skipif(not SSZ_AVAILABLE, reason="SSZ library not available")
    def test_ssz_roundtrip(self):
        """Test SSZ encoding roundtrip preserves data."""
        builder = BALBuilder()
        
        # Create complex BAL
        for i in range(5):
            addr = Bytes(i.to_bytes(20, 'big'))
            builder.add_storage_write(addr, Bytes32(b'\x00' * 32), 0, Bytes32(i.to_bytes(32, 'big')))
            builder.add_balance_change(addr, 0, i.to_bytes(12, 'big'))
        
        original_bal = builder.build()
        
        # Encode and decode
        encoded = ssz.encode(original_bal, sedes=BlockAccessList)
        decoded_bal = ssz.decode(encoded, sedes=BlockAccessList)
        
        # Re-encode to compare
        re_encoded = ssz.encode(decoded_bal, sedes=BlockAccessList)
        
        assert encoded == re_encoded
    
    def test_hash_without_ssz(self):
        """Test hash computation works without SSZ."""
        builder = BALBuilder()
        address = Bytes(b'\x01' * 20)
        
        builder.add_storage_write(address, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x01' * 32))
        
        bal = builder.build()
        hash_val = compute_bal_hash(bal)
        
        assert len(hash_val) == 32
        assert isinstance(hash_val, bytes)


class TestSSZPatterns:
    """Test SSZ with different BAL patterns."""
    
    @pytest.mark.skipif(not SSZ_AVAILABLE, reason="SSZ library not available")
    def test_dex_pattern_ssz(self):
        """Test DEX-like transaction pattern SSZ encoding."""
        builder = BALBuilder()
        
        # Simulate DEX operations
        user = Bytes(b'\x01' * 20)
        token_a = Bytes(b'\x0a' * 20)
        token_b = Bytes(b'\x0b' * 20)
        pair = Bytes(b'\xab' * 20)
        
        # Token balance reads
        user_balance_a = Bytes32(user + b'\x00' * 12)
        user_balance_b = Bytes32(user + b'\x00' * 12)
        
        builder.add_storage_read(token_a, user_balance_a)
        builder.add_storage_read(token_b, user_balance_b)
        
        # Balance updates after swap
        new_balance_a = (500 * 10**18).to_bytes(32, 'big')
        new_balance_b = (1 * 10**18).to_bytes(32, 'big')
        
        builder.add_storage_write(token_a, user_balance_a, 0, new_balance_a)
        builder.add_storage_write(token_b, user_balance_b, 0, new_balance_b)
        
        # Pair reserves update
        reserves_slot = Bytes32(b'\x00' * 31 + b'\x08')
        new_reserves = (2000 * 10**6).to_bytes(16, 'big') + (100 * 10**18).to_bytes(16, 'big')
        builder.add_storage_write(pair, reserves_slot, 0, new_reserves)
        
        # Gas payment
        gas_cost = (21000 * 50 * 10**9).to_bytes(12, 'big')
        builder.add_balance_change(user, 0, gas_cost)
        
        bal = builder.build()
        
        encoded = ssz.encode(bal, sedes=BlockAccessList)
        decoded = ssz.decode(encoded, sedes=BlockAccessList)
        
        # Verify structure preserved
        assert len(decoded.account_changes) >= 3  # user, tokens, pair
        
        # Verify specific patterns
        user_account = next((acc for acc in decoded.account_changes if acc.address == user), None)
        assert user_account is not None
        assert len(user_account.balance_changes) == 1
    
    @pytest.mark.skipif(not SSZ_AVAILABLE, reason="SSZ library not available")
    def test_contract_deployment_ssz(self):
        """Test contract deployment pattern SSZ encoding."""
        builder = BALBuilder()
        
        deployer = Bytes(b'\x01' * 20)
        new_contract = Bytes(b'\x02' * 20)
        
        # Deployment operations
        builder.add_nonce_change(deployer, 0, 5)
        
        # Contract code
        contract_code = Bytes(b'\x60\x80\x60\x40' * 100)  # Larger contract
        builder.add_code_change(new_contract, 0, contract_code)
        
        # Constructor storage
        owner_slot = Bytes32(b'\x00' * 32)
        builder.add_storage_write(new_contract, owner_slot, 0, Bytes32(deployer + b'\x00' * 12))
        
        # Gas costs
        gas_cost = (1500000 * 30 * 10**9).to_bytes(12, 'big')
        builder.add_balance_change(deployer, 0, gas_cost)
        
        bal = builder.build()
        
        encoded = ssz.encode(bal, sedes=BlockAccessList)
        decoded = ssz.decode(encoded, sedes=BlockAccessList)
        
        # Verify deployment preserved
        contract_account = next((acc for acc in decoded.account_changes if acc.address == new_contract), None)
        assert contract_account is not None
        assert len(contract_account.code_changes) == 1
        assert len(contract_account.code_changes[0].new_code) == len(contract_code)
    
    @pytest.mark.skipif(not SSZ_AVAILABLE, reason="SSZ library not available")
    def test_large_storage_pattern_ssz(self):
        """Test large storage operation pattern SSZ encoding."""
        builder = BALBuilder()
        contract = Bytes(b'\x01' * 20)
        
        # Many storage operations
        num_slots = 50
        for i in range(num_slots):
            slot = Bytes32(i.to_bytes(32, 'big'))
            
            if i % 3 == 0:
                # Read
                builder.add_storage_read(contract, slot)
            else:
                # Write
                value = Bytes32((i * 10).to_bytes(32, 'big'))
                builder.add_storage_write(contract, slot, 0, value)
        
        bal = builder.build()
        
        encoded = ssz.encode(bal, sedes=BlockAccessList)
        decoded = ssz.decode(encoded, sedes=BlockAccessList)
        
        account = decoded.account_changes[0]
        
        # Verify large structure preserved
        expected_reads = len([i for i in range(num_slots) if i % 3 == 0])
        expected_writes = num_slots - expected_reads
        
        assert len(account.storage_reads) == expected_reads
        assert len(account.storage_changes) == expected_writes


class TestSSZEdgeCases:
    """Test SSZ with edge cases."""
    
    @pytest.mark.skipif(not SSZ_AVAILABLE, reason="SSZ library not available")
    def test_zero_values_ssz(self):
        """Test SSZ encoding of zero values."""
        builder = BALBuilder()
        
        zero_addr = Bytes(b'\x00' * 20)
        builder.add_storage_write(zero_addr, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x00' * 32))
        builder.add_balance_change(zero_addr, 0, b'\x00' * 12)
        builder.add_nonce_change(zero_addr, 0, 0)
        
        bal = builder.build()
        
        encoded = ssz.encode(bal, sedes=BlockAccessList)
        decoded = ssz.decode(encoded, sedes=BlockAccessList)
        
        account = decoded.account_changes[0]
        assert account.address == zero_addr
        assert account.storage_changes[0].changes[0].new_value == Bytes32(b'\x00' * 32)
        assert account.balance_changes[0].post_balance == b'\x00' * 12
        assert account.nonce_changes[0].new_nonce == U64(0)
    
    @pytest.mark.skipif(not SSZ_AVAILABLE, reason="SSZ library not available")
    def test_max_values_ssz(self):
        """Test SSZ encoding of maximum values."""
        builder = BALBuilder()
        
        max_addr = Bytes(b'\xff' * 20)
        builder.add_storage_write(max_addr, Bytes32(b'\xff' * 32), 65535, Bytes32(b'\xff' * 32))
        builder.add_balance_change(max_addr, 65535, b'\xff' * 12)
        builder.add_nonce_change(max_addr, 65535, 2**64 - 1)
        
        # Max code size
        max_code = Bytes(b'\x60' * MAX_CODE_SIZE)
        builder.add_code_change(max_addr, 0, max_code)
        
        bal = builder.build()
        
        encoded = ssz.encode(bal, sedes=BlockAccessList)
        decoded = ssz.decode(encoded, sedes=BlockAccessList)
        
        account = decoded.account_changes[0]
        assert account.storage_changes[0].changes[0].tx_index == U16(65535)
        assert account.balance_changes[0].tx_index == U16(65535)
        assert account.nonce_changes[0].new_nonce == U64(2**64 - 1)
        assert len(account.code_changes[0].new_code) == MAX_CODE_SIZE
    
    def test_deterministic_encoding(self):
        """Test encoding is deterministic."""
        # Create same BAL twice
        builders = [BALBuilder(), BALBuilder()]
        
        address = Bytes(b'\x01' * 20)
        for builder in builders:
            builder.add_storage_write(address, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x01' * 32))
            builder.add_balance_change(address, 0, b'\x00' * 12)
        
        bal1, bal2 = [builder.build() for builder in builders]
        
        # Hashes should be identical
        hash1 = compute_bal_hash(bal1)
        hash2 = compute_bal_hash(bal2)
        
        assert hash1 == hash2
        
        if SSZ_AVAILABLE:
            # SSZ encoding should also be identical
            encoded1 = ssz.encode(bal1, sedes=BlockAccessList)
            encoded2 = ssz.encode(bal2, sedes=BlockAccessList)
            assert encoded1 == encoded2
    
    @pytest.mark.skipif(not SSZ_AVAILABLE, reason="SSZ library not available")
    @pytest.mark.slow
    def test_large_bal_ssz(self):
        """Test SSZ with large BAL structure."""
        builder = BALBuilder()
        
        # Create many accounts
        num_accounts = min(500, MAX_ACCOUNTS // 10)  # Reasonable test size
        
        for i in range(num_accounts):
            addr = Bytes(i.to_bytes(20, 'big'))
            builder.add_balance_change(addr, 0, i.to_bytes(12, 'big'))
        
        bal = builder.build()
        
        encoded = ssz.encode(bal, sedes=BlockAccessList)
        decoded = ssz.decode(encoded, sedes=BlockAccessList)
        
        assert len(decoded.account_changes) == num_accounts
        
        # Verify sorting preserved after SSZ roundtrip
        prev_addr = b''
        for account in decoded.account_changes:
            curr_addr = bytes(account.address)
            assert curr_addr > prev_addr
            prev_addr = curr_addr


def test_hash_consistency():
    """Test hash consistency across different scenarios."""
    test_cases = []
    
    # Create different BAL configurations
    configs = [
        # Storage only
        lambda b, a: b.add_storage_write(a, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x01' * 32)),
        # Balance only  
        lambda b, a: b.add_balance_change(a, 0, b'\x00' * 12),
        # Both
        lambda b, a: [
            b.add_storage_write(a, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x01' * 32)),
            b.add_balance_change(a, 0, b'\x00' * 12)
        ],
    ]
    
    for i, config in enumerate(configs):
        builder = BALBuilder()
        address = Bytes(bytes([i + 1]) + b'\x00' * 19)
        config(builder, address)
        
        bal = builder.build()
        hash_val = compute_bal_hash(bal)
        test_cases.append(hash_val)
    
    # All hashes should be different
    assert len(set(test_cases)) == len(test_cases)
    
    # All should be valid 32-byte hashes
    for hash_val in test_cases:
        assert len(hash_val) == 32
        assert isinstance(hash_val, bytes)


if __name__ == "__main__":
    pytest.main([__file__])