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

- **AttackOrchestrator.sol** and **Verifier.sol**: https://gist.github.com/CPerezz/8686da933fa5c045fbdf7c31e20e6c71
- **Pre-mined assets** (depth_*.sol, s*_acc*.json): https://github.com/CPerezz/worst_case_miner/tree/master/mined_assets

For complete deployment setup and instructions, see the gist: https://gist.github.com/CPerezz/44d521c0f9e6adf7d84187a4f2c11978

## Prerequisites

- Python with `uv` package manager
- Anvil (Ethereum node implementation) or another EVM client
- Nick's factory deployed at `0x4e59b44847b379578588920ca78fbf26c0b4956c`

## Workflow

### Step 1: Start the Node (Anvil in this example)

```bash
# Start Anvil with high gas limit and auto-mining
anvil --hardfork prague --block-time 6 --steps-tracing --gas-limit 500000000 --balance 99999999999999 --port 8545
```

### Step 2: Deploy Contracts

Deploy contracts using the provided script with batched transactions:

```bash
# Deploy contracts (example for depth 10, account depth 6)
uv run python deploy_deep_branches.py \
  --rpc-url http://localhost:8546 \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  --storage-depth 10 \
  --account-depth 6 \
  --num-contracts 1000 \
  --output deployed_contracts.json
```

The script:
- Funds auxiliary accounts in batches
- Deploys contracts via CREATE2 for deterministic addresses
- Dynamically calculates batch sizes based on network gas limit

### Step 3: Run Attack Test

Execute the worst-case depth attack test:

```bash
# Run the attack test
uv run execute remote \
  --rpc-endpoint=http://localhost:8546 \
  --rpc-seed-key=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  --rpc-chain-id=31337 \
  --gas-benchmark-values 60 \
  --fork Prague \
  -m stateful \
  deep_branch_testing.py::test_worst_depth_stateroot_recomp
```

## Asset Downloads

The test automatically downloads required assets from GitHub:
- `s{storage_depth}_acc{account_depth}.json` - Pre-mined CREATE2 addresses and auxiliary accounts
- `depth_{storage_depth}.sol` - Solidity contract source (used to extract deep storage slot)

Downloaded assets are cached locally in `.cache/` directory.

## Available Configurations

Currently available pre-mined assets from [worst_case_miner](https://github.com/CPerezz/worst_case_miner/tree/master/mined_assets):

| Storage Depth | Account Depth | File |
|--------------|---------------|------|
| 10 | 6 | s10_acc6.json |
| 10 | 7 | s10_acc7.json |
| 11 | 6 | s11_acc6.json |
| 11 | 7 | s11_acc7.json |

To generate new configurations, use [worst_case_miner](https://github.com/CPerezz/worst_case_miner).
