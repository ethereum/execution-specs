# Stateful Environment

Stateful benchmarks run against a client whose state already holds the contracts and accounts they target. Use a perfnet or bloatnet snapshot, or generate the state with [state-actor](https://github.com/ethereum/state-actor).

Every run needs the Arachnid CREATE2 factory at `0x4e59b44847b379578588920cA78FbF26c0B4956C` and a funded seed EOA for `fill-stateful`. Each benchmark needs its own stub accounts on top of that.

## Where the definitions live

- **state-actor configuration**: [`ethpandaops/benchmarkoor-tests`](https://github.com/ethpandaops/benchmarkoor-tests/tree/master/configs/datadirs/state-actor) keeps the versioned config, currently [`v2/builder.yaml`](https://github.com/ethpandaops/benchmarkoor-tests/blob/master/configs/datadirs/state-actor/v2/builder.yaml). A breaking change becomes a new version, so a setup pinned to one keeps working.
- **Stub accounts**: [`tests/benchmark/helper/account_creator.py`](https://github.com/ethereum/execution-specs/blob/forks/bogota/tests/benchmark/helper/account_creator.py) defines the accounts the benchmarks expect.
- **Per-benchmark checks**: a benchmark declares the accounts it needs with `pre.expect_account_state(...)`, and `fill-stateful` verifies them at the start block before running it. For a range, only the first and last accounts are checked unless `--verify-full-accounts` is set.
