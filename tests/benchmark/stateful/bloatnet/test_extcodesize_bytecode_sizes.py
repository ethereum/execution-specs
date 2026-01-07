r"""
Test EXTCODESIZE with parametrized bytecode sizes using CREATE2 factory.

This benchmark measures the performance impact of `EXTCODESIZE` operations
on contracts of varying sizes (0.5KB to 24KB).
It stresses client state loading by maximizing **cold** EXTCODESIZE calls.

Designed for execute mode only - contracts must be pre-deployed.

## Gas-Based Loop Strategy

The attack contract uses a gas-based loop exit (per Jochem's suggestion):
1. Reads current salt from storage slot 0
2. Loops while gas > 50K, calling EXTCODESIZE on CREATE2 addresses
3. Saves final salt to storage slot 0 when exiting
4. Next TX automatically resumes from where previous left off

This eliminates manual gas calculations - the contract self-regulates.

## Test Block Structure

┌───────────────────────────────────────────────────────────────┐
│                        Test Block                             │
├───────────────────────────────────────────────────────────────┤
│  TX1: Verification (~30K gas)                                 │
│    └─> Calls EXTCODESIZE on salt 0, stores result             │
│                                                               │
│  TX2: Attack (~16M gas)                                       │
│    └─> Loops EXTCODESIZE until gas < 50K, saves salt          │
│                                                               │
│  TX3: Attack (~16M gas)                                       │
│    └─> Resumes from TX2's salt, continues looping             │
│                                                               │
│  TX4: Attack (~16M gas)                                       │
│    └─> Resumes from TX3's salt, continues looping             │
└───────────────────────────────────────────────────────────────┘

### Execute a Single Size

```bash
uv run execute remote \\
  --fork Osaka \\
  --rpc-endpoint http://127.0.0.1:8545 \\
  --rpc-seed-key <SEED_KEY> \\
  --rpc-chain-id 1337 \\
  --address-stubs tests/benchmark/stateful/bloatnet/stubs.json \\
  -- -m stateful --gas-benchmark-values 60 \\
  tests/benchmark/stateful/bloatnet/test_extcodesize_bytecode_sizes.py \\
  -k '24KB' -v
```

### Execute All Sizes

```bash
uv run execute remote \\
  --fork Osaka \\
  --rpc-endpoint http://127.0.0.1:8545 \\
  --rpc-seed-key <SEED_KEY> \\
  --rpc-chain-id 1337 \\
  --address-stubs tests/benchmark/stateful/bloatnet/stubs.json \\
  -- -m stateful --gas-benchmark-values 60 \\
  tests/benchmark/stateful/bloatnet/test_extcodesize_bytecode_sizes.py -v
```
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Conditional,
    Fork,
    Op,
    Transaction,
    While,
)
from execution_testing.forks.gas_costs import GasCosts

REFERENCE_SPEC_GIT_PATH = "DUMMY/bloatnet.md"
REFERENCE_SPEC_VERSION = "1.0"


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


def build_attack_contract(factory_address: Address) -> Bytecode:
    """
    Build an attack contract that maximizes EXTCODESIZE calls.

    Uses a gas-based loop exit strategy (per Jochem's suggestion):
    1. Reads current salt from storage slot 0 (resumes from previous TX)
    2. Calls factory.getConfig() to get (num_deployed, init_code_hash)
    3. Loops while gas > GAS_RESERVE, calling EXTCODESIZE on each address
    4. Saves final salt to storage slot 0 for next TX to resume
    5. Saves last EXTCODESIZE result to storage slot 1 for verification

    Storage layout:
    - Slot 0: Current/final salt (used for resuming across TXs)
    - Slot 1: Last EXTCODESIZE result (used for verification)

    This eliminates manual gas calculations - the contract self-regulates.
    Each TX automatically continues from where the previous one left off.
    """
    # Gas reserve for 2x SSTORE + cleanup
    # - Slot 0: warm (after SLOAD), ~5K worst case
    # - Slot 1: cold on first TX (~22K), warm after (~3K)
    # - 50K provides safe margin for both cases
    gas_reserve = 50_000

    return (
        # === Step 0: Load current salt from storage slot 0 ===
        Op.SLOAD(0)  # Stack: [current_salt]
        # === Step 1: Get factory configuration ===
        # Call factory.getConfig() -> (num_deployed, init_code_hash)
        + Op.STATICCALL(
            gas=Op.GAS,
            address=factory_address,
            args_offset=0,
            args_size=0,
            ret_offset=96,  # Store result at memory[96]
            ret_size=64,  # 64 bytes for 2 uint256s
        )
        # Check if call succeeded (STATICCALL returns 1 on success)
        # Stack: [current_salt, success]
        + Conditional(
            condition=Op.ISZERO,  # If call failed (success=0)
            if_true=Op.REVERT(0, 0),  # Revert with no data
        )
        # Stack: [current_salt]
        # Load results from memory
        # Memory[96:128] = num_deployed_contracts
        # Memory[128:160] = init_code_hash
        + Op.MLOAD(96)  # Stack: [current_salt, num_deployed]
        + Op.MLOAD(128)  # Stack: [current_salt, num_deployed, init_code_hash]
        # === Step 2: Setup CREATE2 address generation in memory ===
        # Memory layout at offset 0:
        # [0x00-0x0A]: padding (11 bytes)
        # [0x0B]: 0xFF marker (1 byte)
        # [0x0C-0x1F]: factory address right-aligned (20 bytes)
        # [0x20-0x3F]: salt (32 bytes)
        # [0x40-0x5F]: init_code_hash (32 bytes)
        # Total CREATE2 input: 85 bytes from offset 0x0B
        # Store factory address at memory[0] (right-aligned, at bytes 12-31)
        + Op.MSTORE(0, factory_address)
        # Store 0xFF marker at position 11 (before the address)
        + Op.MSTORE8(11, 0xFF)
        # Store init_code_hash at memory[64]
        # Stack: [current_salt, num_deployed, init_code_hash]
        + Op.PUSH1(64)
        + Op.MSTORE  # Stores init_code_hash at memory[64]
        # Stack: [current_salt, num_deployed]
        # Store current salt at memory[32]
        + Op.SWAP1  # Stack: [num_deployed, current_salt]
        + Op.DUP1  # Stack: [num_deployed, current_salt, current_salt]
        + Op.PUSH1(32)
        + Op.MSTORE  # Store current_salt at memory[32]
        # Stack: [num_deployed, current_salt]
        + Op.POP  # Stack: [num_deployed]
        # Initialize last_size at memory[160] to 0
        + Op.PUSH1(0)
        + Op.PUSH2(160)
        + Op.MSTORE  # memory[160] = 0 (last_size)
        # === Step 3: Main loop - gas-based exit ===
        # Loop while gas > gas_reserve AND salt < num_deployed
        + While(
            body=(
                # Stack: [num_deployed]
                # CREATE2 address: keccak256(0xFF ++ factory ++ salt ++ hash)
                Op.SHA3(11, 85)  # 85 bytes from offset 11
                # Hash result - EVM auto-truncates to 20-byte address
                # Call EXTCODESIZE and store result in memory[160]
                + Op.EXTCODESIZE
                + Op.PUSH2(160)
                + Op.MSTORE  # Store size at memory[160] for verification
                # Increment salt for next iteration
                + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1))
            ),
            # Continue while: gas > gas_reserve AND salt < num_deployed
            condition=(
                # Check gas > gas_reserve
                Op.GAS
                + Op.PUSH3(gas_reserve)
                + Op.GT  # gas > gas_reserve
                # Check salt < num_deployed (num_deployed > salt)
                + Op.DUP2  # Stack: [..., (gas>reserve), num_deployed]
                + Op.MLOAD(32)  # Stack: [..., (gas>res), num_deployed, salt]
                + Op.GT  # Stack: [..., (gas>reserve), (num_deployed > salt)]
                # Both conditions must be true
                + Op.AND  # (gas > reserve) AND (salt < num_deployed)
            ),
        )
        # === Step 4: Save state to storage for next TX and verification ===
        # Stack: [num_deployed]
        + Op.POP  # Clean up stack
        # Save final salt to slot 0
        + Op.MLOAD(32)  # Load final salt from memory
        + Op.PUSH1(0)
        + Op.SSTORE  # SSTORE(0, final_salt)
        # Save last EXTCODESIZE result to slot 1 for verification
        + Op.MLOAD(160)  # Load last_size from memory
        + Op.PUSH1(1)
        + Op.SSTORE  # SSTORE(1, last_size)
        + Op.STOP
    )


def calculate_verification_gas(gas_costs: GasCosts, intrinsic_gas: int) -> int:
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
        # Note: No masking needed - EVM auto-truncates to 20 bytes
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


def build_verification_contract(
    factory_address: Address, verification_salt: int
) -> Bytecode:
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
        # Result is 32-byte hash - EVM auto-truncates to 20-byte address
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
    Execute EXTCODESIZE benchmark against pre-deployed contracts.

    Uses a gas-based loop exit strategy (per Jochem's suggestion):
    1. Attack contract reads/writes salt from storage slot 0
    2. Loop exits when gas < 50K, saves salt for next TX
    3. Each TX automatically resumes from where previous left off
    4. No manual gas calculations needed - contract self-regulates

    Verification TX checks that contracts exist by calling EXTCODESIZE
    on salt 0 (first contract) and storing the result.
    """
    gas_costs = fork.gas_costs()
    # Use fork's TX gas limit cap, or 16M fallback for pre-Osaka forks
    tx_gas_limit = fork.transaction_gas_limit_cap() or 16_000_000
    expected_size_bytes = int(bytecode_size_kb * 1024)

    # Calculate intrinsic transaction cost (no calldata needed)
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(calldata=b"")

    # Get factory stub name for this size
    factory_stub = get_factory_stub_name(bytecode_size_kb)

    # Deploy factory stub (address comes from stub file)
    factory_address = pre.deploy_contract(
        code=Bytecode(),  # Empty bytecode - address from stub
        stub=factory_stub,
    )

    # Build and deploy the attack contract with storage initialized
    attack_code = build_attack_contract(factory_address)
    attack_address = pre.deploy_contract(
        code=attack_code,
        storage={0: 0},  # Initialize salt counter to 0
    )

    # Calculate how many transactions we need to fill the block
    num_attack_txs = gas_benchmark_value // tx_gas_limit
    if num_attack_txs == 0:
        num_attack_txs = 1

    # Verification: check salt 0 (first contract, always accessed)
    verification_salt = 0

    # Build and deploy verification contract
    verification_code = build_verification_contract(
        factory_address, verification_salt
    )
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

    # Attack transactions: all identical, no calldata needed
    # Each TX reads salt from storage, loops until gas low, saves salt back
    for _ in range(num_attack_txs):
        attack_tx = Transaction(
            gas_limit=tx_gas_limit,
            to=attack_address,
            sender=sender,
            data=b"",  # No calldata - salt comes from storage
            value=0,
        )
        txs.append(attack_tx)

    # Log test configuration
    print(f"\n{'=' * 60}")
    print(f"EXTCODESIZE Benchmark: {bytecode_size_kb}KB contracts")
    print(f"{'=' * 60}")
    print(f"Block gas budget: {gas_benchmark_value:,}")
    print(f"TX gas limit: {tx_gas_limit:,}")
    print(f"Number of attack txs: {num_attack_txs}")
    print(f"Verification tx gas: {verification_gas:,}")
    print(f"Expected contract size: {expected_size_bytes} bytes")
    print("Note: Using gas-based loop - each TX auto-resumes from storage")
    print(f"{'=' * 60}\n")

    # Create block with all transactions
    block = Block(txs=txs)

    # Post-state verification:
    # 1. Verify that verification contract stored expected size (salt 0)
    # 2. Verify attack contract's last EXTCODESIZE returns expected size
    #    (proves the gas-based loop ran and accessed real contracts)
    post = {
        verification_address: Account(
            storage={
                0: expected_size_bytes,  # EXTCODESIZE on salt 0
            }
        ),
        attack_address: Account(
            storage={
                # Slot 1: last EXTCODESIZE result should match expected size
                1: expected_size_bytes,
            }
        ),
    }

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[block],
    )
