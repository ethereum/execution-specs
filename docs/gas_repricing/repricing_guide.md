# Gas Repricing Guide

## What is Gas Repricing?

Gas repricing allows you to override the default gas cost constants for any fork
without modifying source code. This is useful for:

- Experimenting with alternative gas schedules
- Testing the impact of proposed EIP gas changes
- Running "what-if" analyses on existing test suites

## JSON Config Format

Create a JSON file mapping fork names to `GasCosts` field overrides:

```json
{
  "Osaka": {
    "VERY_LOW": 4,
    "COLD_STORAGE_ACCESS": 2200
  },
  "Prague": {
    "WARM_SLOAD": 150
  }
}
```

Each key is a fork name (e.g., `Osaka`, `Prague`, `Cancun`). Each value is an
object mapping `GasCosts` field names to their new integer values. Only the
fields you want to change need to be specified; all others retain their
defaults.

## Activation

Set the `EELS_GAS_REPRICING_CONFIG` environment variable to the path of your
JSON config file:

```bash
export EELS_GAS_REPRICING_CONFIG=./my_gas_repricing.json
uv run fill tests/osaka/
```

The repricing config is loaded once (cached) and applied transparently whenever
`gas_costs()` is called on a fork.

## Finding the Right Field Names

The `GasCosts` dataclass has ~90 fields. To find which field controls a
particular opcode's gas cost, use the `gas-map` CLI tool:

```bash
# Show full mapping for a fork
uv run gas-map --fork Osaka

# Look up a specific opcode
uv run gas-map --opcode SLOAD
```

See [GasCosts Reference](reference.md) for a static reference table.

## Example Workflow

1. Identify the opcodes you want to reprice:

    ```bash
    uv run gas-map --opcode SLOAD
    ```

    Output shows `WARM_SLOAD` and `COLD_STORAGE_ACCESS` are the relevant fields.

2. Create a repricing config:

    ```json
    {
      "Osaka": {
        "WARM_SLOAD": 150,
        "COLD_STORAGE_ACCESS": 2500
      }
    }
    ```

3. Run tests with the new gas schedule:

    ```bash
    EELS_GAS_REPRICING_CONFIG=./reprice.json uv run fill tests/osaka/
    ```

4. Compare results against the baseline to see which tests break or change
   behavior under the new gas schedule.

## Regenerating Fixtures Under a New Schedule

A repricing config changes gas costs, so existing fixtures — which encode the
default schedule — will fail once it is active. That is expected, not a bug.
How you regenerate depends on your intent.

!!! warning "Protect the canonical fixtures"
    - Never run `fill --clean` over the canonical `fixtures/` directory with a
      config active: it replaces mainnet-correct fixtures with "what-if" ones.
      Always fill experiments into a separate `--output` directory.
    - Unset `EELS_GAS_REPRICING_CONFIG` before normal test or fill runs, or
      every run silently reprices.

### What-if comparison (the intended use)

Fill into a scratch directory with the config active, then diff against a
baseline fill to see how gas usage shifts:

```bash
# Repriced
EELS_GAS_REPRICING_CONFIG=./reprice.json \
    uv run fill tests/amsterdam/ --fork Amsterdam --output /tmp/fx_repriced --clean

# Baseline (config unset)
uv run fill tests/amsterdam/ --fork Amsterdam --output /tmp/fx_baseline --clean

diff -r /tmp/fx_baseline /tmp/fx_repriced
```

Differences in `cumulativeGasUsed`, balances, and state/block hashes confirm the
new schedule took effect. Nothing here is committed.

### Adopting the schedule permanently

The config is for iteration, not a source of truth. To make a schedule
permanent, bake the values into the spec (`src/ethereum/forks/<fork>/vm/gas.py`)
and the testing framework (`forks/forks.py`), remove the config, then fill the
canonical `fixtures/` directory without any config set.

### Quick sanity check

To confirm the pipeline works under repricing, scope a fill to a few
gas-sensitive tests into a scratch directory:

```bash
EELS_GAS_REPRICING_CONFIG=./reprice.json uv run fill \
    tests/berlin/eip2929_gas_cost_increases/test_warm_status_revert.py \
    --fork Amsterdam --output /tmp/fx_check --clean
```
