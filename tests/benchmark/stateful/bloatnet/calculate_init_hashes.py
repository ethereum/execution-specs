#!/usr/bin/env python3
"""
Calculate init code hashes for all contract sizes.
"""

from execution_testing import Op, While
from eth_utils import keccak

# Maximum contract size in bytes (24 KB)
MAX_CONTRACT_SIZE = 24576

def build_initcode(target_size_kb: float) -> bytes:
    """
    Build initcode that generates contracts of specific size using ADDRESS for randomness.
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

# Calculate hashes for all sizes
sizes = [0.5, 1.0, 5.0, 10.0, 24.0]

print("Init code hashes for each size:")
print("="*60)

for size_kb in sizes:
    initcode = build_initcode(size_kb)
    init_hash = keccak(initcode)
    print(f"{size_kb:4.1f} KB: 0x{init_hash.hex()}")
    print(f"         Initcode size: {len(initcode)} bytes")
    print()