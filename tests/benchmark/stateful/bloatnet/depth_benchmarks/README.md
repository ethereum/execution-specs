# Depth Benchmark Tests

This directory contains tests for worst-case depth attacks on Ethereum state and account tries.

## Scenario Description

These benchmarks test the worst-case scenario for Ethereum clients when dealing with extremely deep state and account tries. The attack involves:

1. **Pre-deployed contracts** with deep storage tries that maximize trie traversal costs
2. **CREATE2-based addressing** for deterministic contract addresses across test runs
3. **Optimized batched attacks** using an AttackOrchestrator contract that can execute up to 2,510 attacks per transaction (8.3x improvement over previous implementation)
4. **Account trie depth** increased by funding auxiliary accounts that make the path deeper

The test measures the performance impact of state root recomputation and IO when modifying deep storage slots across thousands of contracts, simulating the maximum theoretical load on the state trie.

For complete deployment setup and instructions, see the gist: https://gist.github.com/CPerezz/44d521c0f9e6adf7d84187a4f2c11978

## Prerequisites

- Python with `uv` package manager
- Anvil (Ethereum node implementation)
- Solc (Solidity compiler)
- Nick's factory deployed at `0x4e59b44847b379578588920ca78fbf26c0b4956c`

## Workflow

### Step 1: Generate Artifacts

Use [worst_case_miner](https://github.com/CPerezz/worst_case_miner) to generate the necessary artifacts:

```bash
# Clone and build worst_case_miner
git clone https://github.com/CPerezz/worst_case_miner
cd worst_case_miner
cargo build --release

# Generate artifacts (example for depth 9, account depth 3)
./target/release/worst_case_miner --storage-depth 9 --account-depth 3 --output s9_acc3.json
```

This generates:
- `depth_9.sol` - Solidity contract with deep storage trie
- `s9_acc3.json` - Pre-computed CREATE2 addresses and auxiliary accounts

### Step 2: Start the Node (Anvil in this example)

```bash
# Start Anvil with high gas limit and auto-mining
anvil --hardfork prague --block-time 6 --steps-tracing --gas-limit 500000000 --balance 99999999999999 --port 8545
```

### Step 3: Deploy Contracts

Deploy contracts using the provided script with batched transactions:

```bash
# Deploy 1,000 contracts (recommended for testing)
uv run python deploy_worst_case_contracts.py \
  --rpc-url http://localhost:8546 \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  --storage-depth 9 \
  --account-depth 3 \
  --num-contracts 1000 \
  --output deployed_contracts.json


The script:
- Funds auxiliary accounts in batches (3 accounts per contract)
- Deploys contracts via CREATE2 for deterministic addresses
- Dynamically calculates batch sizes based on network gas limit

### Step 4: Run Attack Test

Execute the worst-case depth attack test:

```bash
# Update NUM_CONTRACTS in deep_branch_testing.py to match deployed count (1000 or 15000)

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

## Configuration

Adjust `NUM_CONTRACTS` in `deep_branch_testing.py` to match your deployment:
