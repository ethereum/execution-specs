"""
Test EXTCODESIZE with parametrized bytecode sizes using CREATE2 factory pattern.

This test executes EXTCODESIZE operations against pre-deployed contracts via factories,
measuring the performance impact of different contract sizes on EXTCODESIZE operations.
Designed for execute mode only - contracts must be pre-deployed.

The test maximizes cold EXTCODESIZE calls to stress client state loading by:
1. Using CREATE2 address derivation to access many unique contracts
2. Filling block gas with transactions as close to FUSAKA_TX_GAS_LIMIT (16M) as possible
3. Verifying contracts exist by checking the last accessed contract's size
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
    While,
)

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"

# Fusaka transaction gas limit (16M gas)
FUSAKA_TX_GAS_LIMIT = 16_000_000


def get_factory_stub_name(size_kb: float) -> str:
    """Generate stub name for factory based on size."""
    if size_kb == 0.5:
        return "bloatnet_factory_0_5kb"
    elif size_kb == 1.0:
        return "bloatnet_factory_1kb"
    elif size_kb == 2.0:
        return "bloatnet_factory_2kb"
    elif size_kb == 5.0:
        return "bloatnet_factory_5kb"
    elif size_kb == 10.0:
        return "bloatnet_factory_10kb"
    elif size_kb == 24.0:
        return "bloatnet_factory_24kb"
    else:
        raise ValueError(f"Unsupported size: {size_kb}KB")


def calculate_gas_per_iteration(gas_costs) -> int:
    """
    Calculate gas cost per EXTCODESIZE loop iteration.

    Each iteration:
    1. Generate CREATE2 address via SHA3
    2. Cold EXTCODESIZE access
    3. Increment salt and loop overhead
    """
    return (
        # SHA3 for CREATE2 address generation (85 bytes = 3 words)
        gas_costs.G_KECCAK_256  # Static cost (30)
        + gas_costs.G_KECCAK_256_WORD * 3  # Dynamic cost (3 * 6 = 18)
        # EXTCODESIZE cold access
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # 2600
        # Stack and memory operations for address extraction
        + gas_costs.G_VERY_LOW * 2  # PUSH20 + AND for address extraction (6)
        # Loop overhead: increment salt, decrement counter, check condition
        + gas_costs.G_LOW  # MLOAD salt (3)
        + gas_costs.G_VERY_LOW  # ADD (3)
        + gas_costs.G_LOW  # MSTORE salt (3)
        + gas_costs.G_VERY_LOW * 3  # Counter decrement ops (9)
        + gas_costs.G_BASE * 2  # ISZERO checks (4)
        + gas_costs.G_MID  # JUMPI (8)
        + gas_costs.G_JUMPDEST  # Loop start (1)
        # POP the EXTCODESIZE result
        + gas_costs.G_BASE  # POP (2)
    )


def build_attack_contract(factory_address) -> Bytecode:
    """
    Build an attack contract that maximizes EXTCODESIZE calls.

    The contract reads a starting salt from calldata (32 bytes) and:
    1. Calls factory.getConfig() to get (num_deployed, init_code_hash)
    2. Sets up memory for CREATE2 address derivation
    3. Loops through salts starting_salt..starting_salt+N calling EXTCODESIZE
    4. Does NOT write to storage (pure computation for maximum efficiency)

    Calldata format: 32 bytes representing the starting salt (big-endian uint256)
    """
    return (
        # === Step 0: Load starting salt from calldata ===
        # CALLDATALOAD(0) reads 32 bytes from calldata offset 0
        Op.CALLDATALOAD(0)  # Stack: [starting_salt]
        # === Step 1: Get factory configuration ===
        # Call factory.getConfig() - returns (uint256 num_deployed, bytes32 init_code_hash)
        + Op.STATICCALL(
            gas=Op.GAS,
            address=factory_address,
            args_offset=0,
            args_size=0,
            ret_offset=96,  # Store result at memory[96]
            ret_size=64,  # 64 bytes for 2 uint256s
        )
        # Check if call succeeded (STATICCALL returns 1 on success)
        # Stack: [starting_salt, success]
        + Op.ISZERO
        + Op.PUSH2(0x1000)  # Jump to end if failed
        + Op.JUMPI
        # Stack: [starting_salt]
        # Load results from memory
        # Memory[96:128] = num_deployed_contracts
        # Memory[128:160] = init_code_hash
        + Op.MLOAD(96)  # Stack: [starting_salt, num_deployed]
        + Op.MLOAD(128)  # Stack: [starting_salt, num_deployed, init_code_hash]
        # === Step 2: Setup CREATE2 address generation in memory ===
        # Memory layout at offset 0:
        # [0x00-0x0A]: padding (11 bytes)
        # [0x0B]: 0xFF marker (1 byte)
        # [0x0C-0x1F]: factory address right-aligned in 32-byte word (20 bytes used)
        # [0x20-0x3F]: salt (32 bytes)
        # [0x40-0x5F]: init_code_hash (32 bytes)
        # Total CREATE2 input: 85 bytes starting at offset 0x0B
        # Store factory address at memory[0] (will be right-aligned, address at bytes 12-31)
        + Op.MSTORE(0, factory_address)
        # Store 0xFF marker at position 11 (just before the address)
        + Op.MSTORE8(11, 0xFF)
        # Store init_code_hash at memory[64]
        # Stack: [starting_salt, num_deployed, init_code_hash]
        + Op.PUSH1(64)
        + Op.MSTORE  # Stores init_code_hash at memory[64]
        # Stack: [starting_salt, num_deployed]
        # Store starting salt at memory[32]
        + Op.SWAP1  # Stack: [num_deployed, starting_salt]
        + Op.DUP1  # Stack: [num_deployed, starting_salt, starting_salt]
        + Op.PUSH1(32)
        + Op.MSTORE  # Store starting_salt at memory[32]
        # Stack: [num_deployed, starting_salt]
        + Op.POP  # Stack: [num_deployed]
        # === Step 3: Main loop - EXTCODESIZE operations ===
        + While(
            body=(
                # Generate CREATE2 address: keccak256(0xFF ++ factory ++ salt ++ hash)
                # Input is 85 bytes starting at offset 11
                Op.SHA3(11, 85)
                # Result is 32-byte hash, address is last 20 bytes (low bits)
                # AND with address mask to extract address from hash
                + Op.PUSH20(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
                + Op.AND
                # Call EXTCODESIZE and discard result (no storage writes!)
                + Op.EXTCODESIZE
                + Op.POP
                # Increment salt for next iteration
                + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1))
            ),
            # Continue while counter > 0
            # Decrement counter and check if non-zero
            condition=(
                Op.PUSH1(1)
                + Op.SWAP1
                + Op.SUB
                + Op.DUP1
                + Op.ISZERO
                + Op.ISZERO  # Convert to boolean: 1 if counter > 0
            ),
        )
        + Op.POP  # Clean up remaining counter
        # === End ===
        + Op.JUMPDEST  # 0x1000 - error/end handler
        + Op.STOP
    )


def calculate_verification_gas(gas_costs, intrinsic_gas: int) -> int:
    """
    Calculate the minimum gas needed for the verification transaction.

    The verification contract:
    1. STATICCALL to factory.getConfig() - cold access
    2. Memory operations for CREATE2 setup
    3. SHA3 for address derivation
    4. EXTCODESIZE on target contract - cold access
    5. SSTORE to save result - cold, zero-to-nonzero
    """
    verification_execution_gas = (
        # STATICCALL to factory (cold access)
        gas_costs.G_COLD_ACCOUNT_ACCESS  # 2600
        + 100  # STATICCALL base cost
        # Memory operations (MSTORE, MSTORE8, MLOAD)
        + gas_costs.G_LOW * 5  # 5 memory ops (3 * 5 = 15)
        + gas_costs.G_VERY_LOW  # MSTORE8 (3)
        # SHA3 for CREATE2 address (85 bytes = 3 words)
        + gas_costs.G_KECCAK_256  # 30
        + gas_costs.G_KECCAK_256_WORD * 3  # 18
        # SHR for address extraction
        + gas_costs.G_VERY_LOW  # 3
        # EXTCODESIZE (cold access to target contract)
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # 2600
        # SSTORE (cold slot, zero-to-nonzero)
        + gas_costs.G_STORAGE_SET  # 20000
        + gas_costs.G_COLD_SLOAD  # 2100 (cold access)
        # STOP
        + 0
    )
    # Add intrinsic gas + 10% buffer for safety
    total = intrinsic_gas + verification_execution_gas
    return int(total * 1.1)


def build_verification_contract(factory_address, verification_salt: int) -> Bytecode:
    """
    Build a verification contract that stores EXTCODESIZE result.

    The contract:
    1. Calls factory.getConfig() to get init_code_hash
    2. Computes CREATE2 address for the given salt
    3. Calls EXTCODESIZE on that address
    4. Stores the result in storage slot 0
    """
    return (
        # Call factory.getConfig() to get init_code_hash
        Op.STATICCALL(
            gas=Op.GAS,
            address=factory_address,
            args_offset=0,
            args_size=0,
            ret_offset=96,
            ret_size=64,
        )
        + Op.POP  # Discard success flag (assume it works)
        # Setup CREATE2 address generation (same layout as attack contract)
        + Op.MSTORE(0, factory_address)
        + Op.MSTORE8(11, 0xFF)
        + Op.MSTORE(32, verification_salt)  # Use the target salt
        # Load init_code_hash from memory[128] and store at memory[64]
        + Op.MLOAD(128)
        + Op.PUSH1(64)
        + Op.MSTORE
        # Generate CREATE2 address
        + Op.SHA3(11, 85)
        # Address is last 20 bytes (low bits) of hash
        + Op.PUSH20(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.AND
        # Call EXTCODESIZE
        + Op.EXTCODESIZE
        # Store result in storage slot 0
        + Op.PUSH1(0)
        + Op.SSTORE
        + Op.STOP
    )


@pytest.mark.parametrize(
    "bytecode_size_kb",
    [0.5, 1.0, 2.0, 5.0, 10.0, 24.0],
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
    Execute EXTCODESIZE benchmark against pre-deployed contracts of various sizes.

    This test:
    1. Uses factory addresses passed via stubs (one factory per size)
    2. Reads factory state to get number of deployed contracts and init code hash
    3. Generates CREATE2 addresses dynamically during execution
    4. Calls EXTCODESIZE on as many contracts as gas allows (cold access each time)
    5. Fills the block with transactions close to FUSAKA_TX_GAS_LIMIT (16M gas)
    6. Verifies that contracts exist by checking a sample contract's size
    """
    gas_costs = fork.gas_costs()
    expected_size_bytes = int(bytecode_size_kb * 1024)

    # Calculate intrinsic transaction cost
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(calldata=b"")

    # Calculate gas per EXTCODESIZE iteration
    gas_per_iteration = calculate_gas_per_iteration(gas_costs)

    # Get factory stub name for this size
    factory_stub = get_factory_stub_name(bytecode_size_kb)

    # Deploy factory stub (address comes from stub file)
    factory_address = pre.deploy_contract(
        code=Bytecode(),  # Empty bytecode - address from stub
        stub=factory_stub,
    )

    # Build and deploy the attack contract
    attack_code = build_attack_contract(factory_address)
    attack_address = pre.deploy_contract(code=attack_code)

    # Calculate intrinsic cost with 32 bytes of calldata (starting salt)
    calldata_for_attack = b"\x00" * 32  # 32 zero bytes for salt
    intrinsic_gas_with_calldata = fork.transaction_intrinsic_cost_calculator()(
        calldata=calldata_for_attack
    )

    # Calculate how many iterations fit in one transaction
    # Reserve gas for: intrinsic cost + setup (getConfig call, memory setup) + cleanup
    setup_gas = 5000  # Approximate gas for factory call and memory setup
    cleanup_gas = 1000  # Reserve for loop exit and cleanup
    available_gas_per_tx = (
        FUSAKA_TX_GAS_LIMIT - intrinsic_gas_with_calldata - setup_gas - cleanup_gas
    )
    iterations_per_tx = available_gas_per_tx // gas_per_iteration

    # Calculate how many transactions we need to fill the block
    # gas_benchmark_value is the total block gas budget
    num_attack_txs = gas_benchmark_value // FUSAKA_TX_GAS_LIMIT
    if num_attack_txs == 0:
        num_attack_txs = 1

    # Total iterations across all transactions (each tx accesses unique contracts)
    total_iterations = iterations_per_tx * num_attack_txs

    # For verification, check the last contract accessed by the last attack tx
    # Last tx starts at salt (num_attack_txs - 1) * iterations_per_tx
    # and ends at salt (num_attack_txs * iterations_per_tx - 1)
    verification_salt = total_iterations - 1 if total_iterations > 0 else 0

    # Build and deploy verification contract
    verification_code = build_verification_contract(factory_address, verification_salt)
    verification_address = pre.deploy_contract(code=verification_code)

    # Calculate minimum gas needed for verification tx
    verification_gas = calculate_verification_gas(gas_costs, intrinsic_gas)

    # Fund the sender
    sender = pre.fund_eoa()

    # Build transactions
    txs = []

    # First transaction: verification (runs first, uses minimal gas)
    verification_tx = Transaction(
        gas_limit=verification_gas,
        to=verification_address,
        sender=sender,
        data=b"",
        value=0,
    )
    txs.append(verification_tx)

    # Attack transactions: fill remaining block gas with ~16M gas txs
    # Each transaction gets a different starting salt to access unique contracts
    for tx_index in range(num_attack_txs):
        starting_salt = tx_index * iterations_per_tx
        # Encode starting salt as 32-byte big-endian
        salt_calldata = starting_salt.to_bytes(32, "big")
        attack_tx = Transaction(
            gas_limit=FUSAKA_TX_GAS_LIMIT,
            to=attack_address,
            sender=sender,
            data=salt_calldata,
            value=0,
        )
        txs.append(attack_tx)

    # Log test configuration
    print(f"\n{'='*60}")
    print(f"EXTCODESIZE Benchmark: {bytecode_size_kb}KB contracts")
    print(f"{'='*60}")
    print(f"Block gas budget: {gas_benchmark_value:,}")
    print(f"Gas per iteration: ~{gas_per_iteration}")
    print(f"Iterations per tx (16M gas): ~{iterations_per_tx:,}")
    print(f"Number of attack txs: {num_attack_txs}")
    print(f"Total unique EXTCODESIZE calls: ~{total_iterations:,}")
    print(f"Salt ranges per tx:")
    for i in range(num_attack_txs):
        start = i * iterations_per_tx
        end = (i + 1) * iterations_per_tx - 1
        print(f"  TX{i+1}: salts {start:,} - {end:,}")
    print(f"Verification tx gas: {verification_gas:,}")
    print(f"Verification salt: {verification_salt:,} (last contract accessed)")
    print(f"Expected contract size: {expected_size_bytes} bytes")
    print(f"Contracts required: {total_iterations:,}")
    print(f"{'='*60}\n")

    # Create block with all transactions
    block = Block(txs=txs)

    # Post-state verification:
    # Verify that the verification contract stored the expected size
    post = {
        verification_address: Account(
            storage={
                0: expected_size_bytes,  # EXTCODESIZE should return the expected size
            }
        ),
    }

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[block],
    )
