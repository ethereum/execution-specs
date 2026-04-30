# eels-spamoor-builders

Standalone Ethereum transaction builders extracted from the execution-specs
Spamoor benchmark scenarios.

## Why this exists

The 12 `build_*_transactions` helpers in `helpers.py` are useful as a
self-contained library for any tooling that wants to drive a node through
the same transaction shapes that the Spamoor pytest scenarios use, without
inheriting the rest of execution-specs (~250 MB of test fixtures + the
Python EVM).

## Install

```bash
pip install git+https://github.com/ethereum/execution-specs.git#subdirectory=tests/benchmark/spamoor
```

## Use

```python
from eels_spamoor_builders import build_eoatx_transactions

txs = build_eoatx_transactions(
    count=10,
    throughput=1.0,
    from_addr="0x1111…",
    private_key="0x" + "11" * 32,
    rpc_client=lambda method, params: {"jsonrpc": "2.0", "result": "0x0"},
)
```

The 12 builders are:
`build_blob_combined_transactions`, `build_calltx_transactions`,
`build_deploytx_transactions`, `build_eoatx_transactions`,
`build_erc20_bloater_transactions`, `build_erc20tx_transactions`,
`build_evm_fuzz_transactions`, `build_factorydeploytx_transactions`,
`build_gasburnertx_transactions`, `build_storagerefundtx_transactions`,
`build_storagespam_transactions`, `build_uniswap_swaps_transactions`.

The `spamoor_signer_context` and `broadcast_and_assert_receipts` helpers in
`helpers.py` are *not* re-exported because they import `pytest` and
`execution_testing.test_types` lazily; install the `test` extra
(`pip install eels-spamoor-builders[test]`) and import them from
`eels_spamoor_builders.helpers` if you need them.

## Layout

This directory is dual-purpose:

- a *pytest test package* under the execution-specs test tree (`tests/benchmark/spamoor`);
- a *pip-installable package* via this `pyproject.toml` (`pip install` maps the directory to the `eels_spamoor_builders` package name).

The same source files satisfy both consumers.
