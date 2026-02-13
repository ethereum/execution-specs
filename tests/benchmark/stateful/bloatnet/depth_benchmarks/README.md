# Depth Benchmark Tests

This directory contains tests for worst-case depth attacks on Ethereum state and account tries.

## Scenario Description

These benchmarks test the worst-case scenario for Ethereum clients when dealing with extremely deep state and account tries. The attack involves:

1. **Pre-deployed contracts** with deep storage tries that maximize trie traversal costs
2. **CREATE2-based addressing** for deterministic contract addresses across test runs
3. **Optimized batched attacks** using an AttackOrchestrator contract that can execute up to 1,980 attacks per transaction
4. **Account trie depth** increased by funding auxiliary accounts that make the path deeper

The test measures the performance impact of state root recomputation and IO when modifying deep storage slots across thousands of contracts, simulating the maximum theoretical load on the state trie.

## Contract Sources

- **Pre-mined assets** (depth\__.sol, s_\_acc\*.json): https://github.com/CPerezz/worst_case_miner/tree/master/mined_assets

For complete deployment setup and instructions, see the gist: https://gist.github.com/CPerezz/44d521c0f9e6adf7d84187a4f2c11978

To update the submodule in this repository to the latest master in `CPerezz/worst_case_miner` run the following command: `git submodule update --remote --merge tests/benchmark/stateful/bloatnet/depth_benchmarks/.worst_case_miner`.

## Prerequisites

- Python with `uv` package manager
- Anvil (Ethereum node implementation) or another EVM client
- Nick's factory deployed at `0x4e59b44847b379578588920ca78fbf26c0b4956c` (automatically deployed by `execute` otherwise)

## Workflow

### Step 1: Start the Node (Anvil in this example)

```bash
# Start Anvil with high gas limit and auto-mining
anvil --hardfork prague --block-time 6 --steps-tracing --gas-limit 500000000 --balance 99999999999999 --port 8545
```

### Step 2: Obtain the mined assets

```bash
git submodule update --init --recursive
```

### Step 3: Run Attack Test

Execute the worst-case depth attack test:

```bash
# Run the attack test
export RPC_ENDPOINT=<RPC endpoint>
export RPC_SEED_KEY=<Account with funds>
export RPC_CHAIN_ID=<RPC chain ID>
uv run execute remote \
  --gas-benchmark-values 60 \
  --fork Prague \
  -m stateful \
  tests/benchmark/stateful/bloatnet/depth_benchmarks/test_deep_branch.py
```

## Available Configurations

Currently available pre-mined assets from [worst_case_miner](https://github.com/CPerezz/worst_case_miner/tree/master/mined_assets):

| Storage Depth | Account Depth | File          |
| ------------- | ------------- | ------------- |
| 10            | 6             | s10_acc6.json |
| 10            | 7             | s10_acc7.json |
| 11            | 6             | s11_acc6.json |
| 11            | 7             | s11_acc7.json |

To generate new configurations, use [worst_case_miner](https://github.com/CPerezz/worst_case_miner).
