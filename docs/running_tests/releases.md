# EEST Fixture Releases

## Formats and Release Layout

@ethereum/execution-spec-tests releases contain JSON test fixtures in various formats. Note that transaction type tests are executed directly from Python source using the [`execute`](./execute/index.md) command.

| Format                                                               | Consumed by the client                                                                                                                                                                                                                                                                    | Location in `.tar.gz` release                                       |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| [State Tests](./test_formats/state_test.md)                         | - directly via a `statetest`-like command<br/> (e.g., [go-ethereum/cmd/evm/staterunner.go](https://github.com/ethereum/go-ethereum/blob/4bb097b7ffc32256791e55ff16ca50ef83c4609b/cmd/evm/staterunner.go))                                                                                 | `./fixtures/state_tests/`                                           |
| [Blockchain Tests](./test_formats/blockchain_test.md)               | - directly via a `blocktest`-like command<br/> (e.g., [go-ethereum/cmd/evm/blockrunner.go](https://github.com/ethereum/go-ethereum/blob/4bb097b7ffc32256791e55ff16ca50ef83c4609b/cmd/evm/blockrunner.go))</br>- using the [eels/consume-rlp Simulator](./running.md#rlp) via block import | `./fixtures/blockchain_tests/`                                      |
| [Blockchain Engine Tests](./test_formats/blockchain_test_engine.md) | - using the [eels/consume-engine Simulator](./running.md#engine) and the Engine API                                                                                                                                                                                                          | `./fixtures/blockchain_tests_engine/`                               |
| [Transaction Tests](./test_formats/transaction_test.md)             | - using a new simulator coming soon                                                                                                                                                                                                                                                       | None; executed directly from Python source,</br>using a release tag |
| Blob Transaction Tests                                               | - using the [eels/execute-blobs Simulator](./execute/hive.md#the-eelsexecute-blobs-simulator) and                                                                                                                                                                                                                         | None; executed directly from Python source,</br>using a release tag |

## Fixture Output Directory Structure

Inside each format directory, fixtures are grouped by **target fork**.

The top-level subdirectory identifies the fork **under test**. Below it,
fixtures mirror the `./tests/` source layout: each directory corresponds
to the fork where the functionality was originally introduced. Because
tests declare `valid_from`, a single target fork directory contains
fixtures from every prior fork whose tests are still valid at that fork.

### Consensus fixture layout

```text
fixtures/
└── blockchain_tests/
    ├── for_prague/                   # filled targeting Prague
    │   ├── istanbul/                 # tests introduced in Istanbul
    │   │   └── eip1344_chainid/...
    │   ├── cancun/                   # tests introduced in Cancun
    │   │   └── eip4844_blobs/...
    │   └── prague/                   # tests introduced in Prague
    │       └── eip7702_set_code_tx/...
    └── for_osaka/                    # filled targeting Osaka
        ├── istanbul/
        │   └── eip1344_chainid/...
        ├── cancun/
        │   └── eip4844_blobs/...
        ├── prague/
        │   └── eip7702_set_code_tx/...
        └── osaka/                    # tests introduced in Osaka
            └── eip7692_eof_v1/...
```

Other format directories (`state_tests/`, `blockchain_tests_engine/`)
follow the same layout.

### Benchmark fixture layout

When filling with `--gas-benchmark-values`, benchmark tests additionally
include the gas limit in the subdirectory name (`for_{fork}_at_{gas}M`,
where `{gas}` is in millions, zero-padded to four digits), with one
subdirectory per gas value:

```text
fixtures/
└── blockchain_tests/
    ├── for_osaka_at_0001M/           # 1M gas benchmark
    │   └── benchmark/compute/...
    └── for_osaka_at_0002M/           # 2M gas benchmark
        └── benchmark/compute/...
```

When filling with `--fixed-opcode-count`, the opcode count replaces the
gas limit in the subdirectory name (`for_{fork}_at_opcount_{N}K`, where
`{N}` is in thousands and may include decimals):

```text
fixtures/
└── blockchain_tests/
    ├── for_osaka_at_opcount_10K/     # 10K opcodes
    │   └── benchmark/compute/...
    └── for_osaka_at_opcount_20K/     # 20K opcodes
        └── benchmark/compute/...
```

## Release URLs and Tarballs

### Versioning Scheme

EEST framework and test sources and fixture releases are tagged use a semantic versioning scheme, `<optional:<pre_release_name@>>v<MAJOR>.<MINOR>.<PATCH>` as following:

- `<MAJOR>`: An existing fixture format has changed (potentially breaking change). Action must be taken by client teams to ensure smooth upgrade to the new format.
- `<MINOR>`: Additional coverage (new tests, or a new format) have been added to the release.
- `<PATCH>`: A bug-fix release; an error in the tests or framework has been patched.

Please see below for an explanation of the optional `<pre_release_name>` that is used in pre-releases.

### Standard Releases

Releases are published on the @ethereum/execution-spec-tests [releases](https://github.com/ethereum/execution-spec-tests/releases) page. Standard releases are tagged using the format `vX.Y.Z` (they don't have a `<pre_release_name>`).

For standard releases, two tarballs are available:

| Release Artifact          | Fork/feature scope                                                      |
| ------------------------- | ----------------------------------------------------------------------- |
| `fixtures_stable.tar.gz`  | Tests for all forks up to and including the last deployed ("stable") mainnet fork ("must pass") |
| `fixtures_develop.tar.gz` | Tests for all forks up to and including the last development fork                               |

I.e., `fixtures_develop` are a superset of `fixtures_stable`.

!!! tip "Generating tarballs directly via `--output` includes all fixture formats"
    When generating fixtures for release, specifying tarball output automatically enables all fixture formats:
    ```console
    # Automatically enables --generate-all-formats due to .tar.gz output
    uv run fill --output=fixtures_stable.tar.gz tests/
    ```
    This ensures that all fixture formats are included in the tarball release.

### Pre-Release and Devnet Releases

Intermediate releases that target specific subsets of features or tests under active development are published at @ethereum/execution-spec-tests [releases](https://github.com/ethereum/execution-spec-tests/releases).

These releases are tagged using the format `<pre_release_name>@vX.Y.Z`.

Examples:

- [`fusaka-devnet-1@v1.0.0`](https://github.com/ethereum/execution-spec-tests/releases/tag/fusaka-devnet-1%40v1.0.0) - this fixture release contains tests adhering to the [Fusaka Devnet 1 spec](https://notes.ethereum.org/@ethpandaops/fusaka-devnet-1).
- [`benchmark@v0.0.3`](https://github.com/ethereum/execution-spec-tests/releases/tag/benchmark%40v0.0.3) - this fixture release contains tests specifically aimed at benchmarking EVMs.

Devnet releases should be treated as WIP and may not yet contain full test coverage (or even coverage for all EIPs). The coverage provided by these releases is detailed in the corresponding release notes.

### Help Downloading Releases

The [`consume cache`](./consume/cache.md) command can be used to resolve EEST release and pre-release tags to release URLs and download them.
