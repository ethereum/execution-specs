from functools import partial
from typing import Dict

import pytest

from tests.helpers import ETHEREUM_TESTS_PATH, OSAKA_TEST_PATH
from tests.helpers.load_state_tests import (
    Load,
    fetch_state_test_files,
    idfn,
    run_blockchain_st_test,
)
from ethereum.osaka.bal_builder import BALBuilder
from ethereum.osaka.bal_utils import compute_bal_hash, validate_bal_structure
from ethereum.osaka.ssz_types import BlockAccessList
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint

ETHEREUM_BLOCKCHAIN_TESTS_DIR = f"{ETHEREUM_TESTS_PATH}/BlockchainTests/"
EEST_BLOCKCHAIN_TESTS_DIR = f"{OSAKA_TEST_PATH}/fixtures/blockchain_tests/"
NETWORK = "Osaka"
PACKAGE = "osaka"

# BAL-specific slow tests that might need special handling
BAL_SLOW_TESTS = (
    "bal_large_block_simulation",
    "bal_complex_contract_deployment",
)

# Tests that might need to be ignored for BAL functionality
BAL_IGNORE_TESTS = (
    # Add any BAL-specific test exclusions here
)

FIXTURES_LOADER = Load(NETWORK, PACKAGE)
run_bal_blockchain_tests = partial(run_blockchain_st_test, load=FIXTURES_LOADER)


# Note: These would normally load from external JSON fixtures in a real deployment
# For now, using inline test cases until BAL fixtures are created
def get_bal_test_cases():
    """Get BAL test cases (would normally load from fixtures)."""
    return [
        {
            "name": "simple_storage_access",
            "description": "Basic storage read/write tracking",
            "operations": [
                {
                    "type": "storage_write",
                    "address": "0x" + "01" * 20,
                    "slot": "0x" + "00" * 32,
                    "value": "0x" + "01" * 32,
                    "tx_index": 0
                }
            ],
            "expected": {
                "accounts": 1,
                "storage_changes": 1
            }
        },
        {
            "name": "multi_account_operations",
            "description": "Multiple accounts with various operations",
            "operations": [
                {
                    "type": "balance_change",
                    "address": "0x" + "01" * 20,
                    "amount": str(1000 * 10**18),
                    "tx_index": 0
                },
                {
                    "type": "storage_write",
                    "address": "0x" + "02" * 20,
                    "slot": "0x" + "00" * 32,
                    "value": "0x" + "42" * 32,
                    "tx_index": 1
                }
            ],
            "expected": {
                "accounts": 2,
                "balance_changes": 1,
                "storage_changes": 1
            }
        }
    ]


# Following existing pattern: parameterized tests with external data
@pytest.mark.parametrize("test_case", get_bal_test_cases(), ids=lambda x: x["name"])
def test_bal_functionality(test_case: Dict) -> None:
    """Test BAL functionality with various scenarios."""
    builder = BALBuilder()
    
    # Execute operations from test case
    for operation in test_case["operations"]:
        if operation["type"] == "storage_write":
            address = Bytes.fromhex(operation["address"][2:])
            slot = Bytes32.fromhex(operation["slot"][2:])
            value = Bytes32.fromhex(operation["value"][2:])
            tx_index = operation["tx_index"]
            
            builder.add_storage_write(address, slot, tx_index, value)
            
        elif operation["type"] == "storage_read":
            address = Bytes.fromhex(operation["address"][2:])
            slot = Bytes32.fromhex(operation["slot"][2:])
            
            builder.add_storage_read(address, slot)
            
        elif operation["type"] == "balance_change":
            address = Bytes.fromhex(operation["address"][2:])
            amount = int(operation["amount"])
            tx_index = operation["tx_index"]
            
            builder.add_balance_change(address, tx_index, amount.to_bytes(12, 'big'))
    
    # Build and validate BAL
    bal = builder.build()
    validate_bal_structure(bal)
    
    # Verify expectations
    expected = test_case["expected"]
    
    assert len(bal.account_changes) == expected["accounts"], \
        f"Expected {expected['accounts']} accounts, got {len(bal.account_changes)}"
    
    if "storage_changes" in expected:
        total_storage = sum(len(acc.storage_changes) for acc in bal.account_changes)
        assert total_storage == expected["storage_changes"], \
            f"Expected {expected['storage_changes']} storage changes, got {total_storage}"
    
    if "balance_changes" in expected:
        total_balance = sum(len(acc.balance_changes) for acc in bal.account_changes)
        assert total_balance == expected["balance_changes"], \
            f"Expected {expected['balance_changes']} balance changes, got {total_balance}"
    
    # Verify hash computation
    bal_hash = compute_bal_hash(bal)
    assert len(bal_hash) == 32, "BAL hash should be 32 bytes"


def test_bal_builder_basic() -> None:
    """Test basic BAL builder functionality."""
    builder = BALBuilder()
    
    # Add operations
    address = Bytes(b'\x01' * 20)
    slot = Bytes32(b'\x00' * 32)
    value = Bytes32(b'\x01' * 32)
    
    builder.add_storage_write(address, slot, 0, value)
    builder.add_storage_read(address, Bytes32(b'\x02' * 32))
    builder.add_balance_change(address, 0, b'\x00' * 12)
    
    # Build and validate
    bal = builder.build()
    validate_bal_structure(bal)
    
    assert len(bal.account_changes) == 1
    account = bal.account_changes[0]
    assert account.address == address
    assert len(account.storage_changes) == 1
    assert len(account.storage_reads) == 1
    assert len(account.balance_changes) == 1


def test_bal_hash_deterministic() -> None:
    """Test that BAL hash is deterministic."""
    # Create identical BALs
    builders = [BALBuilder(), BALBuilder()]
    
    address = Bytes(b'\x01' * 20)
    slot = Bytes32(b'\x00' * 32)
    value = Bytes32(b'\x01' * 32)
    
    for builder in builders:
        builder.add_storage_write(address, slot, 0, value)
        builder.add_balance_change(address, 0, b'\x00' * 12)
    
    bal1, bal2 = [builder.build() for builder in builders]
    hash1, hash2 = [compute_bal_hash(bal) for bal in [bal1, bal2]]
    
    assert hash1 == hash2, "Identical BALs should produce identical hashes"


def test_bal_sorting() -> None:
    """Test that BAL maintains proper sorting."""
    builder = BALBuilder()
    
    # Add addresses in reverse order
    addresses = [Bytes(bytes([i]) * 20) for i in [3, 1, 2]]
    
    for i, addr in enumerate(addresses):
        builder.add_balance_change(addr, 0, i.to_bytes(12, 'big'))
    
    bal = builder.build()
    
    # Verify addresses are sorted
    sorted_addresses = sorted(addresses)
    for i, account in enumerate(bal.account_changes):
        assert account.address == sorted_addresses[i], "Addresses should be sorted"


def test_bal_edge_cases() -> None:
    """Test BAL edge cases."""
    builder = BALBuilder()
    
    # Zero address
    zero_addr = Bytes(b'\x00' * 20)
    builder.add_storage_write(zero_addr, Bytes32(b'\x00' * 32), 0, Bytes32(b'\x00' * 32))
    
    # Max values
    max_addr = Bytes(b'\xff' * 20)
    builder.add_balance_change(max_addr, 65535, b'\xff' * 12)
    
    bal = builder.build()
    validate_bal_structure(bal)
    
    assert len(bal.account_changes) == 2


@pytest.mark.slow
def test_bal_large_dataset() -> None:
    """Test BAL with large dataset."""
    builder = BALBuilder()
    
    # Create many accounts
    num_accounts = 1000
    for i in range(num_accounts):
        addr = Bytes(i.to_bytes(20, 'big'))
        builder.add_balance_change(addr, 0, i.to_bytes(12, 'big'))
    
    bal = builder.build()
    validate_bal_structure(bal)
    
    assert len(bal.account_changes) == num_accounts
    
    # Verify sorting maintained
    prev_addr = b''
    for account in bal.account_changes:
        curr_addr = bytes(account.address)
        assert curr_addr > prev_addr, "Sorting should be maintained"
        prev_addr = curr_addr


# Integration with existing test infrastructure
# This would be the primary test entry point in a real deployment
@pytest.mark.parametrize(
    "test_case",
    fetch_state_test_files(
        ETHEREUM_BLOCKCHAIN_TESTS_DIR,
        EEST_BLOCKCHAIN_TESTS_DIR,
        lambda file_path: "bal" in file_path.lower() or "block_access" in file_path.lower()
    ),
    ids=idfn,
)
def test_ethereum_bal_tests(test_case: Dict) -> None:
    """
    Run ethereum/tests BAL tests through state transition.
    
    This test would integrate with the broader test suite when BAL fixtures
    are added to ethereum/tests repository.
    """
    # Skip for now since BAL fixtures don't exist yet in ethereum/tests
    pytest.skip("BAL fixtures not yet available in ethereum/tests")
    
    # When available, this would run:
    # run_bal_blockchain_tests(test_case)


if __name__ == "__main__":
    pytest.main([__file__])