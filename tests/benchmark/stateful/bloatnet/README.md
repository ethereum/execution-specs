# BloatNet Single-Opcode Benchmarks

This directory contains benchmarks for testing single EVM opcodes (SLOAD, SSTORE) under state-heavy conditions using pre-deployed contracts.

## Test Setup

### Prerequisites

1. Pre-deployed ERC20 contracts on the target network
2. A JSON file containing contract addresses (stubs)

### Address Stubs Format

Create a JSON file (`stubs.json`) mapping test-specific stub names to deployed contract addresses:

```json
{
  "test_sload_empty_erc20_balanceof_USDT": "0x1234567890123456789012345678901234567890",
  "test_sload_empty_erc20_balanceof_USDC": "0x2345678901234567890123456789012345678901",
  "test_sload_empty_erc20_balanceof_DAI": "0x3456789012345678901234567890123456789012",
  "test_sload_empty_erc20_balanceof_WETH": "0x4567890123456789012345678901234567890123",
  "test_sload_empty_erc20_balanceof_WBTC": "0x5678901234567890123456789012345678901234",

  "test_sstore_erc20_approve_USDT": "0x1234567890123456789012345678901234567890",
  "test_sstore_erc20_approve_USDC": "0x2345678901234567890123456789012345678901",
  "test_sstore_erc20_approve_DAI": "0x3456789012345678901234567890123456789012",
  "test_sstore_erc20_approve_WETH": "0x4567890123456789012345678901234567890123",
  "test_sstore_erc20_approve_WBTC": "0x5678901234567890123456789012345678901234",

  "test_mixed_sload_sstore_USDT": "0x1234567890123456789012345678901234567890",
  "test_mixed_sload_sstore_USDC": "0x2345678901234567890123456789012345678901",
  "test_mixed_sload_sstore_DAI": "0x3456789012345678901234567890123456789012",
  "test_mixed_sload_sstore_WETH": "0x4567890123456789012345678901234567890123",
  "test_mixed_sload_sstore_WBTC": "0x5678901234567890123456789012345678901234"
}
```

**Naming Convention:**
- Stub names MUST start with the test function name
- Format: `{test_function_name}_{identifier}`
- Example: `test_sload_empty_erc20_balanceof_USDT`


### Running the Tests

#### Execute Mode (Against Live Network)

```bash
# Run with specific number of contracts (e.g., only the 5-contract variant)
uv run execute remote \
  --rpc-endpoint http://localhost:8545 \
  --rpc-seed-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  --rpc-chain-id 1337 \
  --address-stubs geth_stubs.json \
  --fork Prague \
  tests/benchmark/stateful/bloatnet/test_single_opcode.py::test_sload_empty_erc20_balanceof \
  -k "[5]" \



## Test Parametrization

Both single-opcode tests are parametrized with `num_contracts = [1, 5, 10, 20, 100]`, generating 5 test variants each:

- **1 contract**: Baseline single-contract performance
- **5 contracts**: Small-scale multi-contract scenario
- **10 contracts**: Medium-scale multi-contract scenario
- **20 contracts**: Large-scale multi-contract scenario
- **100 contracts**: Very large-scale multi-contract stress test

The mixed SLOAD/SSTORE test additionally parametrizes operation ratios:

- **50-50**: Equal mix of SLOAD and SSTORE operations
- **70-30**: 70% SLOAD, 30% SSTORE operations
- **90-10**: 90% SLOAD, 10% SSTORE operations

### How Stub Filtering Works

1. Test extracts its function name (e.g., `test_sload_empty_erc20_balanceof`)
2. Filters stubs starting with that name from `stubs.json`
3. Selects the **first N** matching stubs based on `num_contracts` parameter
4. Errors if insufficient matching stubs found


## Benchmark Descriptions

### test_sload_empty_erc20_balanceof
Tests SLOAD operations by calling `balanceOf()` on ERC20 contracts with random addresses, forcing cold storage reads of likely-empty slots.

### test_sstore_erc20_approve
Tests SSTORE operations by calling `approve()` on ERC20 contracts with incrementing spender addresses, forcing cold storage writes to new allowance slots.

### test_mixed_sload_sstore
Tests mixed SLOAD/SSTORE workloads with configurable ratios, simulating realistic DeFi application patterns with combined read/write operations.