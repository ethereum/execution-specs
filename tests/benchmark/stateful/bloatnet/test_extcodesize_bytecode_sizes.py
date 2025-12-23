"""
Test EXTCODESIZE with parametrized bytecode sizes using CREATE2 factory pattern.

This test executes against pre-deployed contracts via factories, measuring the
performance impact of different contract sizes on EXTCODESIZE operations.
Designed for execute mode only - contracts must be pre-deployed.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Op,
    Transaction,
)

# Hardcoded init code hashes for each contract size
# These are deterministic based on our initcode generation in deploy_initcode_multi.py
INIT_CODE_HASHES = {
    0.5: 0xaa03809400f3a470a717403a9600140150129b24180fbaab4a4f58334fc5e5a8,
    1.0: 0x62b07e407cbb2f5bf8d706444fe89b0b40331a14efb0081ba02534ca4f6438ee,
    5.0: 0xdfcaab76f37cb182d0a9e24827c65057c0540c5b736085e3465b99eecd4502c1,
    10.0: 0xc39b2c8f715e341c46b43fda72209e073fe08f9845a586cc5b16ed9cb8a1c5a8,
    24.0: 0xd570c69a8b04a4e65932da40d0f5b2b7f11aaa72d8b8ca3a714fa43077197172,
}


def get_factory_stub_name(size_kb: float) -> str:
    """Generate stub name for factory based on size."""
    if size_kb == 0.5:
        return "factory_0_5kb"
    elif size_kb == 1.0:
        return "factory_1kb"
    elif size_kb == 5.0:
        return "factory_5kb"
    elif size_kb == 10.0:
        return "factory_10kb"
    elif size_kb == 24.0:
        return "factory_24kb"
    else:
        raise ValueError(f"Unsupported size: {size_kb}KB")


@pytest.mark.parametrize(
    "bytecode_size_kb",
    [0.5, 1.0, 5.0, 10.0, 24.0],
    ids=lambda size: f"{size}KB",
)
@pytest.mark.valid_from("Prague")
def test_extcodesize_bytecode_sizes(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    bytecode_size_kb: float,
    gas_benchmark_value: int,
) -> None:
    """
    Execute EXTCODESIZE attack against pre-deployed contracts.

    This test:
    1. Uses factory addresses passed via stubs (one factory per size)
    2. Reads factory state to get number of deployed contracts
    3. Generates CREATE2 addresses dynamically during execution
    4. Calls EXTCODESIZE on as many contracts as gas allows
    5. Aims to consume all available gas to measure maximum attack capacity
    """
    gas_costs = fork.gas_costs()

    # Calculate gas costs for operations
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(calldata=b"")

    # Get factory stub name and init code hash for this size
    factory_stub = get_factory_stub_name(bytecode_size_kb)
    init_code_hash = INIT_CODE_HASHES[bytecode_size_kb]

    # Deploy factory stub (address comes from stub file)
    factory_address = pre.deploy_contract(
        code=Bytecode(),  # Empty bytecode - address from stub
        stub=factory_stub,
    )

    # Create attack contract that maximizes EXTCODESIZE calls
    # The attack will:
    # 1. Call factory.getConfig() to get (num_deployed, init_code_hash)
    # 2. Generate CREATE2 addresses for all deployed contracts
    # 3. Call EXTCODESIZE on each until gas runs out

    # First, call factory to get config
    attack_code = (
        # Call factory.getConfig() - returns (uint256 num_deployed, bytes32 init_code_hash)
        Op.PUSH1(0x40)  # retSize (64 bytes for 2 uint256s)
        + Op.PUSH1(0x60)  # retOffset
        + Op.PUSH1(0)  # argSize
        + Op.PUSH1(0)  # argOffset
        + Op.PUSH20(factory_address)  # Factory address
        + Op.GAS  # Use all available gas
        + Op.STATICCALL

        # Check if call succeeded
        + Op.ISZERO
        + Op.PUSH2(0x1000)  # Jump to end if failed
        + Op.JUMPI

        # Load num_deployed and init_code_hash from memory
        + Op.PUSH1(0x60)
        + Op.MLOAD  # num_deployed at memory[96]
        + Op.PUSH1(0x80)
        + Op.MLOAD  # init_code_hash at memory[128]

        # Prepare for CREATE2 address generation loop
        # Memory layout for CREATE2 hash:
        # [0x00-0x0A]: padding (11 bytes)
        # [0x0B]: 0xFF (1 byte)
        # [0x0C-0x1F]: factory address (20 bytes)
        # [0x20-0x3F]: salt (32 bytes)
        # [0x40-0x5F]: init_code_hash (32 bytes)

        # Store factory address at correct position
        + Op.PUSH20(factory_address)
        + Op.PUSH1(0)
        + Op.MSTORE  # Store at 0x00 (will be at 0x0C after 12 byte offset)

        # Store 0xFF marker
        + Op.PUSH1(0xFF)
        + Op.PUSH1(0x0B)
        + Op.MSTORE8

        # Store init_code_hash
        + Op.DUP2  # init_code_hash
        + Op.PUSH1(0x40)
        + Op.MSTORE

        # Initialize salt counter (starts at 0)
        + Op.PUSH1(0)
        + Op.PUSH1(0x20)
        + Op.MSTORE

        # Main loop: generate addresses and call EXTCODESIZE
        # Stack: [num_deployed, init_code_hash]
        + Op.SWAP1
        + Op.POP  # Remove init_code_hash, keep num_deployed

        # Loop start
        + Op.JUMPDEST  # Loop label at PC ~100

        # Check if we've processed all contracts
        + Op.DUP1  # Duplicate num_deployed
        + Op.PUSH1(0x20)
        + Op.MLOAD  # Load current salt
        + Op.GT  # num_deployed > salt?
        + Op.ISZERO
        + Op.PUSH2(0x1000)  # Jump to end if done
        + Op.JUMPI

        # Generate CREATE2 address
        # Hash the CREATE2 input (0xFF + factory + salt + init_code_hash)
        + Op.PUSH1(0x55)  # Size: 1 + 20 + 32 + 32 = 85 bytes
        + Op.PUSH1(0x0B)  # Offset: start from 0xFF marker
        + Op.SHA3

        # The address is the last 20 bytes of the hash
        # Call EXTCODESIZE on this address
        + Op.EXTCODESIZE
        + Op.POP  # Discard the result

        # Increment salt
        + Op.PUSH1(0x20)
        + Op.MLOAD  # Load current salt
        + Op.PUSH1(1)
        + Op.ADD
        + Op.PUSH1(0x20)
        + Op.MSTORE  # Store updated salt

        # Continue loop
        + Op.PUSH1(100)  # Jump back to loop start (approximate PC)
        + Op.JUMP

        # End of execution
        + Op.JUMPDEST  # End label at PC 0x1000
    )

    # Deploy the attack contract
    attack_address = pre.deploy_contract(code=attack_code)

    # Fund the sender
    # G_BASE is 21000 for transaction intrinsic cost
    # Fusaka transaction gas limit (16M gas)
    FUSAKA_TX_GAS_LIMIT = 16_000_000

    # Calculate how many transactions we need for the total gas
    total_gas_needed = gas_benchmark_value
    num_txs = (total_gas_needed + FUSAKA_TX_GAS_LIMIT - 1) // FUSAKA_TX_GAS_LIMIT  # Ceiling division

    print(f"EXTCODESIZE Attack Configuration:")
    print(f"  Total gas budget: {total_gas_needed:,}")
    print(f"  Fusaka TX limit: {FUSAKA_TX_GAS_LIMIT:,}")
    print(f"  Number of transactions: {num_txs}")
    print(f"  Contracts to attack: {38000:,}")

    # Fund the sender with enough for all transactions
    sender = pre.fund_eoa(total_gas_needed * 21000 * 2)

    # Create multiple transactions to fill the block
    txs = []
    remaining_gas = total_gas_needed

    for i in range(num_txs):
        # Each transaction uses up to FUSAKA_TX_GAS_LIMIT
        tx_gas = min(remaining_gas, FUSAKA_TX_GAS_LIMIT)

        tx = Transaction(
            gas_limit=tx_gas,
            to=attack_address,
            sender=sender,
            data=b"",  # No calldata needed
            value=0,
            nonce=i,  # Increment nonce for each transaction
        )
        txs.append(tx)
        remaining_gas -= tx_gas

    # Create block with all attack transactions
    # In execute mode, this will run against real deployed contracts
    block = Block(
        txs=txs,
        exception=None,  # Transactions should succeed and use most/all gas
    )

    # No post-state verification needed in execute mode
    # The test passes if it executes without error and consumes gas
    post = {}

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[block],
    )