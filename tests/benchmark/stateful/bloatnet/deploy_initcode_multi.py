#!/usr/bin/env python3
"""
Deploy multiple initcode contracts for different bytecode sizes for BloatNet benchmarks.

This script deploys initcode contracts that will be used by CREATE2 factories
to create contracts of different sizes (0.5, 1, 2, 5, 10, 24 KB).

USAGE:
    1. Start a local geth instance:
       geth --dev --http --http.api eth,web3,net,debug --http.corsdomain "*"

    2. Run this script to deploy all initcode contracts:
       python3 deploy_initcode_multi.py

    3. The initcode addresses will be saved to initcode_addresses.json

REQUIREMENTS:
    - web3.py
    - eth-utils
    - ethereum-test-tools (for Opcodes)
    - Local geth instance running on http://127.0.0.1:8545
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Add path to execution-spec-tests if needed
# sys.path.insert(0, "/path/to/execution-spec-tests")

from execution_testing import Op, While
from eth_utils import keccak
from web3 import Web3

# Contract size configurations (in KB)
CONTRACT_SIZES_KB = [0.5, 1, 2, 5, 10, 24]

# Maximum contract size in bytes (24 KB)
MAX_CONTRACT_SIZE = 24576

def build_initcode(target_size_kb: float) -> bytes:
    """
    Build initcode that generates contracts of specific size using ADDRESS for randomness.

    Args:
        target_size_kb: Target contract size in kilobytes

    Returns:
        The initcode bytecode that will generate a contract of the specified size
    """
    target_size = int(target_size_kb * 1024)

    if target_size > MAX_CONTRACT_SIZE:
        target_size = MAX_CONTRACT_SIZE

    # For small contracts (< 1KB), use simple padding
    if target_size < 1024:
        initcode = (
            # Store deployer address for uniqueness
            Op.MSTORE(0, Op.ADDRESS)
            # Pad with JUMPDEST opcodes (1 byte each)
            + Op.JUMPDEST * max(0, target_size - 33 - 10)  # Account for other opcodes
            # Ensure first byte is STOP
            + Op.MSTORE8(0, 0x00)
            # Return the contract
            + Op.RETURN(0, target_size)
        )
    else:
        # For larger contracts, use the keccak256 expansion pattern
        # Generate XOR table for expansion
        xor_table_size = min(256, target_size // 256)
        xor_table = [keccak(i.to_bytes(32, "big")) for i in range(xor_table_size)]

        initcode = (
            # Store ADDRESS as initial seed - creates uniqueness per deployment
            Op.MSTORE(0, Op.ADDRESS)
            # Loop to expand bytecode using SHA3 and XOR operations
            + While(
                body=(
                    Op.SHA3(Op.SUB(Op.MSIZE, 32), 32)
                    # Use XOR table to expand without excessive SHA3 calls
                    + sum(
                        (Op.PUSH32(xor_value) + Op.XOR + Op.DUP1 + Op.MSIZE + Op.MSTORE)
                        for xor_value in xor_table
                    )
                    + Op.POP
                ),
                condition=Op.LT(Op.MSIZE, target_size),
            )
            # Set first byte to STOP for efficient CALL handling
            + Op.MSTORE8(0, 0x00)
            # Return the full contract
            + Op.RETURN(0, target_size)
        )

    return bytes(initcode)

def deploy_initcode(w3: Web3, size_kb: float) -> Dict[str, Any]:
    """Deploy an initcode contract for a specific size."""
    account = w3.eth.accounts[0]

    print(f"\n--- Building initcode for {size_kb}KB contracts ---")
    initcode_bytes = build_initcode(size_kb)
    print(f"Initcode size: {len(initcode_bytes)} bytes")

    # Calculate the hash for verification
    initcode_hash = keccak(initcode_bytes)
    print(f"Initcode hash: 0x{initcode_hash.hex()}")

    # Deploy the initcode as a contract
    # We need to deploy the raw initcode bytecode without executing it
    # To do this, we create deployment code that just returns the initcode
    print(f"Deploying initcode contract for {size_kb}KB...")

    # Create simple deployment bytecode that returns the initcode as-is
    deployment_code = (
        # CODECOPY(destOffset=0, offset=codesize_of_prefix, size=initcode_size)
        bytes(Op.PUSH2(len(initcode_bytes)))  # Push initcode size (3 bytes)
        + bytes(Op.DUP1)  # Duplicate for RETURN (1 byte)
        + bytes(Op.PUSH1(0x0c))  # Offset after this prefix (2 bytes)
        + bytes(Op.PUSH1(0))  # Dest offset (2 bytes)
        + bytes(Op.CODECOPY)  # Copy initcode (1 byte)
        # RETURN(offset=0, size=initcode_size)
        + bytes(Op.PUSH1(0))  # Offset (2 bytes)
        + bytes(Op.RETURN)  # Return (1 byte) = Total: 12 bytes (0x0c)
        + initcode_bytes  # Actual initcode
    )

    # Deploy the contract
    tx_hash = w3.eth.send_transaction({
        "from": account,
        "data": "0x" + deployment_code.hex(),
        "gas": 16_000_000  # Fusaka tx gas limit (16M)
    })
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt['status'] != 1:
        print(f"❌ Failed to deploy initcode for {size_kb}KB")
        return None

    initcode_address = receipt['contractAddress']
    print(f"✅ Initcode deployed at: {initcode_address}")

    # Verify the deployed bytecode
    deployed_code = w3.eth.get_code(initcode_address)
    print(f"Deployed bytecode size: {len(deployed_code)} bytes")

    # Verify hash
    actual_hash = keccak(deployed_code)
    print(f"Actual hash: 0x{actual_hash.hex()}")

    if actual_hash == initcode_hash:
        print(f"✅ Hash verification successful")
    else:
        print(f"⚠️ Hash mismatch! Expected: 0x{initcode_hash.hex()}")

    return {
        "size_kb": size_kb,
        "address": initcode_address,
        "hash": "0x" + initcode_hash.hex(),
        "bytecode_size": len(initcode_bytes)
    }

def main():
    """Deploy all initcode contracts for different sizes."""
    import argparse

    parser = argparse.ArgumentParser(description='Deploy initcode contracts for multiple sizes')
    parser.add_argument('--rpc-url', default='http://127.0.0.1:8545', help='RPC URL')
    parser.add_argument('--sizes', nargs='+', type=float,
                        help='Contract sizes in KB (default: 0.5 1 2 5 10 24)')
    args = parser.parse_args()

    # Use custom sizes if provided
    sizes = args.sizes if args.sizes else CONTRACT_SIZES_KB

    # Connect to local geth instance
    w3 = Web3(Web3.HTTPProvider(args.rpc_url))
    if not w3.is_connected():
        print(f"❌ Failed to connect to {args.rpc_url}")
        sys.exit(1)

    print(f"Connected to: {args.rpc_url}")
    print(f"Account: {w3.eth.accounts[0]}")

    # Deploy initcode for each size
    results = {}
    for size_kb in sizes:
        result = deploy_initcode(w3, size_kb)
        if result:
            # Use string key for JSON compatibility
            key = f"{size_kb}kb".replace(".", "_")
            results[key] = result

    # Save all results to file
    if results:
        output_file = "initcode_addresses.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ All initcode addresses saved to {output_file}")

        # Print summary
        print("\n=== Summary ===")
        for key, info in results.items():
            print(f"{info['size_kb']}KB: {info['address']} (hash: {info['hash'][:10]}...)")
    else:
        print("\n❌ No initcode contracts deployed successfully")
        sys.exit(1)

if __name__ == "__main__":
    main()