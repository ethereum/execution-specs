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

The builders return *unsigned* type-2 transaction dictionaries — signing is the
caller's responsibility. `rpc_client` is invoked with `(method, params)` and
must return the *unwrapped* JSON-RPC `result` (not the full envelope).

```python
from eels_spamoor_builders import build_eoatx_transactions


def rpc_client(method, params):
    if method == "eth_getTransactionCount":
        return "0x0"  # nonce hex
    if method == "eth_feeHistory":
        return {
            "oldestBlock": "0x0",
            "baseFeePerGas": ["0x1", "0x1"],
            "gasUsedRatio": [0.5],
            "reward": [],
        }
    raise NotImplementedError(method)


txs = build_eoatx_transactions(
    count=10,
    throughput=1.0,
    from_addr="0x1111111111111111111111111111111111111111",
    private_key="0x" + "11" * 32,
    rpc_client=rpc_client,
)
# txs is a list of unsigned tx dicts; sign them downstream.
```

The 12 builders are:
`build_blob_combined_transactions`, `build_calltx_transactions`,
`build_deploytx_transactions`, `build_eoatx_transactions`,
`build_erc20_bloater_transactions`, `build_erc20tx_transactions`,
`build_evm_fuzz_transactions`, `build_factorydeploytx_transactions`,
`build_gasburnertx_transactions`, `build_storagerefundtx_transactions`,
`build_storagespam_transactions`, `build_uniswap_swaps_transactions`.

The `spamoor_signer_context` and `broadcast_and_assert_receipts` helpers in
`helpers.py` are *not* re-exported. They import `pytest` and
`execution_testing.test_types` lazily — neither is a hard dependency of this
package. If you need them, install both manually
(`pip install pytest "ethereum-execution @ git+https://github.com/ethereum/execution-specs.git#subdirectory=src/ethereum_spec_tools"` — adjust to whichever package ships `execution_testing` in your tree)
and import them from `eels_spamoor_builders.helpers`.

## Layout

This directory is dual-purpose:

- a *pytest test package* under the execution-specs test tree (`tests/benchmark/spamoor`);
- a *pip-installable package* via this `pyproject.toml` (`pip install` maps the directory to the `eels_spamoor_builders` package name).

The same source files satisfy both consumers.
