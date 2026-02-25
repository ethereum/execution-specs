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
    "GAS_VERY_LOW": 4,
    "GAS_COLD_SLOAD": 2200
  },
  "Prague": {
    "GAS_WARM_SLOAD": 150
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

    Output shows `GAS_WARM_SLOAD` and `GAS_COLD_SLOAD` are the relevant fields.

2. Create a repricing config:

    ```json
    {
      "Osaka": {
        "GAS_WARM_SLOAD": 150,
        "GAS_COLD_SLOAD": 2500
      }
    }
    ```

3. Run tests with the new gas schedule:

    ```bash
    EELS_GAS_REPRICING_CONFIG=./reprice.json uv run fill tests/osaka/
    ```

4. Compare results against the baseline to see which tests break or change
   behavior under the new gas schedule.
