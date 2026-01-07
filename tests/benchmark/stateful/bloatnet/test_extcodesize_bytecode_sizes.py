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
    Storage,
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
    Benchmark EXTCODESIZE calls with gas-based loop exit.

    Storage Layout:
     - Slot 0: current salt (persists across transactions)
     - Slot 1: last EXTCODESIZE result (for verification)

    CREATE2 Memory Layout (85 bytes from offset 11):
     - MEM[11]    = 0xFF prefix
     - MEM[12-31] = factory address (20 bytes)
     - MEM[32-63] = salt (32 bytes)
     - MEM[64-95] = init_code_hash (32 bytes)
    """
    gas_reserve = 50_000  # Reserve for 2x SSTORE + cleanup

    return (
        # Call factory.getConfig() -> (num_deployed, init_code_hash)
        Conditional(
            condition=Op.STATICCALL(
                gas=Op.GAS,
                address=factory_address,
                args_offset=0,
                args_size=0,
                ret_offset=96,  # MEM[96]=num_deployed, MEM[128]=init_code_hash
                ret_size=64,
            ),
            if_false=Op.REVERT(0, 0),
        )
        # Setup CREATE2 memory: keccak256(0xFF ++ factory ++ salt ++ hash)
        + Op.MSTORE(0, factory_address)
        + Op.MSTORE8(11, 0xFF)
        + Op.MSTORE(32, Op.SLOAD(0))  # Load salt directly to memory
        + Op.MSTORE(64, Op.MLOAD(128))  # init_code_hash
        + Op.MSTORE(160, 0)  # Initialize last_size
        + While(
            body=(
                Op.MSTORE(160, Op.EXTCODESIZE(Op.SHA3(11, 85)))
                + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1))
            ),
            condition=(
                Op.AND(
                    Op.GT(Op.GAS, gas_reserve),
                    Op.GT(Op.MLOAD(96), Op.MLOAD(32)),  # num_deployed > salt
                )
            ),
        )
        + Op.SSTORE(0, Op.MLOAD(32))  # Save final salt
        + Op.SSTORE(1, Op.MLOAD(160))  # Save last result
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
    Verify EXTCODESIZE result for a specific salt by storing it in slot 0.

    CREATE2 Memory Layout (same as attack contract):
     - MEM[11]    = 0xFF prefix
     - MEM[12-31] = factory address
     - MEM[32-63] = salt
     - MEM[64-95] = init_code_hash
    """
    return (
        # Call factory.getConfig() -> (num_deployed, init_code_hash)
        Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=factory_address,
                args_offset=0,
                args_size=0,
                ret_offset=96,  # MEM[96]=num_deployed, MEM[128]=init_code_hash
                ret_size=64,
            )
        )
        # Setup CREATE2 memory
        + Op.MSTORE(0, factory_address)
        + Op.MSTORE8(11, 0xFF)
        + Op.MSTORE(32, verification_salt)
        + Op.MSTORE(64, Op.MLOAD(128))
        # EXTCODESIZE on CREATE2 address, store result
        + Op.SSTORE(0, Op.EXTCODESIZE(Op.SHA3(11, 85)))
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
    tx_gas_limit: int,
) -> None:
    """
    Execute EXTCODESIZE benchmark against pre-deployed contracts.

    Uses a gas-based loop exit strategy:
    1. Attack contract reads/writes salt from storage slot 0
    2. Loop exits when gas < 50K, saves salt for next TX
    3. Each TX automatically resumes from where previous left off

    Verification TX checks that contracts exist by calling EXTCODESIZE
    on salt 0 (first contract) and storing the result.
    """
    gas_costs = fork.gas_costs()
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

    # Build and deploy the attack contract
    attack_code = build_attack_contract(factory_address)
    attack_address = pre.deploy_contract(code=attack_code)

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
    )
    txs.append(verification_tx)

    # Attack transactions: all identical, no calldata needed
    for _ in range(num_attack_txs):
        attack_tx = Transaction(
            gas_limit=tx_gas_limit,
            to=attack_address,
            sender=sender,
        )
        txs.append(attack_tx)

    # Create block with all transactions
    block = Block(txs=txs)

    # Post-state verification:
    # - Verification contract: slot 0 = expected size
    # - Attack contract: slot 1 = expected size, slot 0 = any (final salt)
    attack_storage = Storage({1: expected_size_bytes})  # type: ignore[dict-item]
    attack_storage.set_expect_any(0)

    post = {
        verification_address: Account(storage={0: expected_size_bytes}),
        attack_address: Account(storage=attack_storage),
    }

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[block],
    )
