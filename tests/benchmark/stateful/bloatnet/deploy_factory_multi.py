#!/usr/bin/env python3
"""
Deploy CREATE2 factories for different contract sizes for BloatNet benchmarks.

This script deploys CREATE2 factories that can deploy contracts of specific sizes
(0.5, 1, 2, 5, 10, 24 KB) using the corresponding initcode contracts.

USAGE:
    1. First deploy initcode contracts:
       python3 deploy_initcode_multi.py

    2. Then deploy the factories:
       python3 deploy_factory_multi.py

    3. The factory addresses will be saved to stubs.json

REQUIREMENTS:
    - web3.py
    - eth-utils
    - ethereum-test-tools (for Opcodes)
    - Local geth instance running on http://127.0.0.1:8545
    - initcode_addresses.json from deploy_initcode_multi.py
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Tuple

# Add path to execution-spec-tests if needed
# sys.path.insert(0, "/path/to/execution-spec-tests")

from execution_testing import Op
from eth_utils import keccak
from web3 import Web3


def build_factory(initcode_address: str, initcode_hash: bytes, initcode_size: int) -> bytes:
    """
    Build a CREATE2 factory contract with getConfig() method.

    Storage layout:
    - Slot 0: Counter (number of deployed contracts)
    - Slot 1: Init code hash for CREATE2 address calculation
    - Slot 2: Init code address

    Interface:
    - When called with CALLDATASIZE == 0: Returns (num_deployed_contracts, init_code_hash)
    - When called otherwise: Deploys a new contract via CREATE2
    """

    # Factory constructor: Store init code hash and address
    factory_constructor = (
        Op.PUSH32(initcode_hash)  # Push init code hash
        + Op.PUSH1(1)  # Slot 1
        + Op.SSTORE  # Store init code hash
        + Op.PUSH20(bytes.fromhex(initcode_address[2:]))  # Push initcode address
        + Op.PUSH1(2)  # Slot 2
        + Op.SSTORE  # Store initcode address
    )

    # Factory runtime code
    factory_runtime = (
        # Check if this is a getConfig() call (CALLDATASIZE == 0)
        Op.CALLDATASIZE
        + Op.ISZERO
        + Op.PUSH1(0x31)  # Jump to getConfig (hardcoded offset)
        + Op.JUMPI

        # === CREATE2 DEPLOYMENT PATH ===
        # Load initcode address from storage slot 2
        + Op.PUSH1(2)  # Slot 2
        + Op.SLOAD  # Load initcode address

        # EXTCODECOPY: copy initcode to memory
        + Op.PUSH2(initcode_size)  # Size
        + Op.PUSH1(0)  # Source offset
        + Op.PUSH1(0)  # Dest offset
        + Op.DUP4  # Address (from bottom of stack)
        + Op.EXTCODECOPY  # Copy initcode to memory

        # Prepare for CREATE2
        + Op.PUSH2(initcode_size)  # Size
        + Op.SWAP1  # Put size under address
        + Op.POP  # Remove address

        # CREATE2 with current counter as salt
        + Op.PUSH1(0)  # Slot 0
        + Op.SLOAD  # Load counter (use as salt)
        + Op.SWAP1  # Put size on top
        + Op.PUSH1(0)  # Offset in memory
        + Op.PUSH1(0)  # Value
        + Op.CREATE2  # Create contract

        # Store the created address for return
        + Op.DUP1
        + Op.PUSH1(0)
        + Op.MSTORE

        # Increment counter
        + Op.PUSH1(0)  # Slot 0
        + Op.DUP1  # Duplicate
        + Op.SLOAD  # Load counter
        + Op.PUSH1(1)  # Increment
        + Op.ADD  # Add
        + Op.SWAP1  # Swap
        + Op.SSTORE  # Store new counter

        # Return the created address
        + Op.PUSH1(32)  # Return 32 bytes
        + Op.PUSH1(0)  # From memory position 0
        + Op.RETURN

        # === GETCONFIG PATH ===
        + Op.JUMPDEST  # Destination for getConfig (0x31)
        + Op.PUSH1(0)  # Slot 0
        + Op.SLOAD  # Load number of deployed contracts
        + Op.PUSH1(0)  # Memory position 0
        + Op.MSTORE  # Store in memory

        + Op.PUSH1(1)  # Slot 1
        + Op.SLOAD  # Load init code hash
        + Op.PUSH1(32)  # Memory position 32
        + Op.MSTORE  # Store in memory

        + Op.PUSH1(64)  # Return 64 bytes (2 * 32)
        + Op.PUSH1(0)  # From memory position 0
        + Op.RETURN
    )

    # Build deployment bytecode
    factory_runtime_bytes = bytes(factory_runtime)
    runtime_size = len(factory_runtime_bytes)

    # Deployment code that copies and returns runtime
    constructor_bytes = bytes(factory_constructor)
    constructor_size = len(constructor_bytes)
    deployer_size = 14  # Size of deployer code below
    runtime_offset = constructor_size + deployer_size

    deployer = (
        # Copy runtime code to memory
        Op.PUSH2(runtime_size)  # Size of runtime (3 bytes)
        + Op.PUSH1(runtime_offset)  # Offset to runtime (2 bytes)
        + Op.PUSH1(0)  # Dest in memory (2 bytes)
        + Op.CODECOPY  # (1 byte)
        # Return runtime code
        + Op.PUSH2(runtime_size)  # Size to return (3 bytes)
        + Op.PUSH1(0)  # Offset in memory (2 bytes)
        + Op.RETURN  # (1 byte) = Total: 14 bytes
    )

    factory_deployment = factory_constructor + deployer + factory_runtime
    return bytes(factory_deployment)


def deploy_factory(w3: Web3, size_kb: float, initcode_info: Dict[str, Any]) -> Tuple[str, bytes]:
    """Deploy a CREATE2 factory for a specific contract size."""
    account = w3.eth.accounts[0]

    print(f"\n--- Deploying Factory for {size_kb}KB contracts ---")

    initcode_address = initcode_info["address"]
    initcode_hash_str = initcode_info["hash"]
    initcode_size = initcode_info["bytecode_size"]

    # Convert hash string to bytes
    initcode_hash = bytes.fromhex(initcode_hash_str[2:] if initcode_hash_str.startswith("0x") else initcode_hash_str)

    print(f"Using initcode at: {initcode_address}")
    print(f"Init code hash: {initcode_hash_str}")
    print(f"Init code size: {initcode_size} bytes")

    # Build factory bytecode
    factory_bytecode = build_factory(initcode_address, initcode_hash, initcode_size)
    print(f"Factory deployment size: {len(factory_bytecode)} bytes")

    # Deploy factory
    tx_hash = w3.eth.send_transaction({
        "from": account,
        "data": "0x" + factory_bytecode.hex(),
        "gas": 10000000  # 10M gas for deployment
    })
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt['status'] != 1:
        print(f"❌ Failed to deploy factory for {size_kb}KB")
        return None, None

    factory_address = receipt['contractAddress']
    print(f"✅ Factory deployed at: {factory_address}")

    # Verify factory storage
    counter = w3.eth.get_storage_at(factory_address, 0)
    stored_hash = w3.eth.get_storage_at(factory_address, 1)
    stored_initcode_addr = w3.eth.get_storage_at(factory_address, 2)

    print(f"Factory storage verification:")
    print(f"  Slot 0 (counter): {int.from_bytes(counter, 'big')}")
    print(f"  Slot 1 (hash): 0x{stored_hash.hex()}")
    print(f"  Slot 2 (initcode): 0x{stored_initcode_addr.hex()}")
    print(f"  Hash matches: {stored_hash == initcode_hash}")

    return factory_address, initcode_hash


def test_getconfig(w3: Web3, factory_address: str, expected_hash: bytes) -> bool:
    """Test the getConfig() method of a factory."""
    print(f"Testing getConfig() on factory at {factory_address}...")

    # Call getConfig() with empty calldata
    result = w3.eth.call({
        "to": factory_address,
        "data": ""  # Empty calldata triggers getConfig
    })

    if len(result) != 64:
        print(f"❌ Unexpected result length: {len(result)} (expected 64)")
        return False

    # Parse the result
    num_deployed = int.from_bytes(result[:32], 'big')
    returned_hash = result[32:64]

    print(f"  Number of deployed contracts: {num_deployed}")
    print(f"  Init code hash: 0x{returned_hash.hex()}")
    print(f"  Hash matches expected: {returned_hash == expected_hash}")

    return returned_hash == expected_hash


def main():
    """Deploy factories for all contract sizes."""
    import argparse

    parser = argparse.ArgumentParser(description='Deploy CREATE2 factories for multiple sizes')
    parser.add_argument('--rpc-url', default='http://127.0.0.1:8545', help='RPC URL')
    parser.add_argument('--initcode-file', default='initcode_addresses.json',
                        help='Path to initcode addresses JSON file')
    parser.add_argument('--output', default='stubs.json',
                        help='Output file for factory addresses (default: stubs.json)')
    args = parser.parse_args()

    # Connect to local geth instance
    w3 = Web3(Web3.HTTPProvider(args.rpc_url))
    if not w3.is_connected():
        print(f"❌ Failed to connect to {args.rpc_url}")
        sys.exit(1)

    print(f"Connected to: {args.rpc_url}")
    print(f"Account: {w3.eth.accounts[0]}")

    # Load initcode addresses
    try:
        with open(args.initcode_file, 'r') as f:
            initcode_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ {args.initcode_file} not found")
        print("Run deploy_initcode_multi.py first")
        sys.exit(1)

    # Deploy factory for each size
    stubs = {}
    for key, initcode_info in initcode_data.items():
        size_kb = initcode_info["size_kb"]
        factory_address, initcode_hash = deploy_factory(w3, size_kb, initcode_info)

        if factory_address:
            # Test getConfig
            if test_getconfig(w3, factory_address, initcode_hash):
                print(f"✅ Factory for {size_kb}KB working correctly")

            # Add to stubs with descriptive key
            stub_key = f"bloatnet_factory_{key}"
            stubs[stub_key] = factory_address

    # Save stubs to file
    if stubs:
        with open(args.output, 'w') as f:
            json.dump(stubs, f, indent=2)
        print(f"\n✅ All factory addresses saved to {args.output}")

        # Print summary
        print("\n=== Factory Summary ===")
        for stub_key, address in stubs.items():
            print(f"{stub_key}: {address}")
    else:
        print("\n❌ No factories deployed successfully")
        sys.exit(1)

if __name__ == "__main__":
    main()