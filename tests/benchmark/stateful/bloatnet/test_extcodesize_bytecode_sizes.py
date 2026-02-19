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
│  TX1: Attack (~16M gas)                                       │
│    └─> Loops EXTCODESIZE until gas < 50K, saves salt          │
│                                                               │
│  TX2: Attack (~16M gas)                                       │
│    └─> Resumes from TX1's salt, continues looping             │
│                                                               │
│  TX3: Attack (~16M gas)                                       │
│    └─> Resumes from TX2's salt, continues looping             │
└───────────────────────────────────────────────────────────────┘

Post-state verification checks attack contract's slot 1 for expected size.

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
    Create2PreimageLayout,
    Op,
    Storage,
    Transaction,
    While,
)

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
    num_deployed_offset = 96
    init_code_hash_offset = num_deployed_offset + 32
    return_size = 64
    return (
        # Call factory.getConfig() -> (num_deployed, init_code_hash)
        Conditional(
            condition=Op.STATICCALL(
                gas=Op.GAS,
                address=factory_address,
                args_offset=0,
                args_size=0,
                # MEM[num_deployed_offset]=num_deployed
                # MEM[num_deployed_offset + 32]=init_code_hash
                ret_offset=num_deployed_offset,
                ret_size=return_size,
            ),
            if_false=Op.REVERT(0, 0),
        )
        + (
            create2_preimage := Create2PreimageLayout(
                factory_address=factory_address,
                salt=Op.SLOAD(0),
                init_code_hash=Op.MLOAD(init_code_hash_offset),
                old_memory_size=num_deployed_offset + return_size,
            )
        )
        + Op.MSTORE(160, 0)  # Initialize last_size
        + While(
            body=(
                Op.MSTORE(160, Op.EXTCODESIZE(create2_preimage.address_op()))
                + create2_preimage.increment_salt_op()
            ),
            condition=(
                Op.AND(
                    Op.GT(Op.GAS, gas_reserve),
                    # num_deployed > salt
                    Op.GT(
                        Op.MLOAD(num_deployed_offset),
                        Op.MLOAD(create2_preimage.salt_offset),
                    ),
                )
            ),
        )
        + Op.SSTORE(0, Op.MLOAD(32))  # Save final salt
        + Op.SSTORE(1, Op.MLOAD(160))  # Save last result
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

    Post-state verifies that the attack contract's slot 1 contains the
    expected bytecode size (last EXTCODESIZE result).
    """
    expected_size_bytes = int(bytecode_size_kb * 1024)

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

    # Fund the sender
    sender = pre.fund_eoa()

    # Build transactions
    txs = []

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
    # Attack contract slot 1 = expected size (last EXTCODESIZE result)
    # Slot 0 can be any value (final salt depends on gas used)
    attack_storage = Storage({1: expected_size_bytes})  # type: ignore[dict-item]
    attack_storage.set_expect_any(0)

    post = {
        attack_address: Account(storage=attack_storage),
    }

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[block],
    )
