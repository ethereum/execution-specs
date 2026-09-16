# Filling Tests for Features under Development

## Requirements

By default, the execution-testing framework only generates fixtures for forks that have been deployed to mainnet. In order to generate fixtures for evm features that are actively under development:

1. A version of the `evm` and `solc` tools that implement the feature must be available (although, typically only a developer version of the `evm` tool is required, usually the latest stable release of `solc` is adequate), and,
2. The development fork to test must be explicitly specified on the command-line:

    === "via the `--fork` flag"

          ```console
          uv run fill -k 4844 --fork=Cancun -v
          ```

    === "via the `--from` flag"

          ```console
          uv run fill -k 4844 --from=Cancun -v
          ```

    === "via the `--until` flag"

          ```console
          uv run fill -k 4844 --until=Cancun -v
          ```

!!! note "Specifying the `evm` binary via `evm-bin`"
     It is possible to explicitly specify the `evm` binary used to generate fixtures via the `--evm-bin` flag, for example,

     ```console
     uv run fill --fork=Cancun --evm-bin=/opt/bin/evm -v
     ```

## Synthetic blob schedules

`BPOIncrease` and `BPODecrease` exercise blob schedule changes under Amsterdam
execution rules. They form the chain `Amsterdam → BPOIncrease → BPODecrease`:
the increased schedule has target/max 21/32 and update fraction 20609697; the
decreased schedule has target/max 14/21 and update fraction 13739630. These are
test scenarios, not scheduled network upgrades.

Select them explicitly, for example:

```console
uv run fill tests/osaka/eip7918_blob_reserve_price/ --from=BPOIncrease --until=BPODecrease
```

Tests marked `valid_for_bpo_forks` can cover either a standalone schedule active
at genesis or a transition. The transitions activate at timestamp 15,000.
`--until=Amsterdam` stops before these scenarios and excludes the historical
parallel BPO3–BPO5 branch. Numbered fork and transition definitions remain
available for older fixtures and genesis files.

Hive needs the descriptive `HIVE_BPO_INCREASE_*` and `HIVE_BPO_DECREASE_*`
mappings. Clients must also permit their BPO3/BPO4 configuration slots to
activate after Amsterdam; mapper aliases alone cannot bypass fork-order checks.
These scenarios are therefore excluded from automatic fixture releases pending
client support. Successful filling does not establish client compatibility.

## Further Help

1. [`geth`/`evm` build documentation](https://geth.ethereum.org/docs/getting-started/installing-geth#build-from-source).
2. [`solc` build documentation](https://docs.soliditylang.org/en/v0.8.20/installing-solidity.html#building-from-source).

!!! note "Verifying `evm` and `solc` versions used"
     The versions used to generate fixtures are displayed in the console output:
     <figure markdown>  <!-- markdownlint-disable MD033 (MD033=no-inline-html) -->
          ![Screenshot of pytest test collection console output](./img/pytest_run_example.png){align=center}
     </figure>
