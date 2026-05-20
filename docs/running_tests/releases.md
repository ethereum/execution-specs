# EEST Fixture Releases

!!! warning "Two repositories — do not confuse them"
    - **`ethereum/execution-specs`** publishes Python *spec package* releases tagged `vX.Y.Z` (e.g. [`v2.20.0`](https://github.com/ethereum/execution-specs/releases/tag/v2.20.0)). **These contain no test fixtures** — they are the executable specification package only.
    - **Test fixtures** are published as **feature-scoped releases** on the same repository — `consensus@vX.Y.Z`, `<feat>-devnet@vX.Y.Z`, `benchmark@vX.Y.Z` — and are *not* attached to the `vX.Y.Z` package tags.
    - The legacy `fixtures_stable.tar.gz` / `fixtures_develop.tar.gz` artifacts (previously on `ethereum/execution-spec-tests`) are being retired in favour of the feature-scoped releases described here.

## Formats and Release Layout

Fixture releases contain JSON test fixtures in various formats. Note that transaction type tests are executed directly from Python source using the [`execute`](./execute/index.md) command.

| Format                                                               | Consumed by the client                                                                                                                                                                                                                                                                    | Location in `.tar.gz` release                                       |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| [State Tests](./test_formats/state_test.md)                         | - directly via a `statetest`-like command<br/> (e.g., [go-ethereum/cmd/evm/staterunner.go](https://github.com/ethereum/go-ethereum/blob/4bb097b7ffc32256791e55ff16ca50ef83c4609b/cmd/evm/staterunner.go))                                                                                 | `./fixtures/state_tests/`                                           |
| [Blockchain Tests](./test_formats/blockchain_test.md)               | - directly via a `blocktest`-like command<br/> (e.g., [go-ethereum/cmd/evm/blockrunner.go](https://github.com/ethereum/go-ethereum/blob/4bb097b7ffc32256791e55ff16ca50ef83c4609b/cmd/evm/blockrunner.go))</br>- using the [eels/consume-rlp Simulator](./running.md#rlp) via block import | `./fixtures/blockchain_tests/`                                      |
| [Blockchain Engine Tests](./test_formats/blockchain_test_engine.md) | - using the [eels/consume-engine Simulator](./running.md#engine) and the Engine API                                                                                                                                                                                                          | `./fixtures/blockchain_tests_engine/`                               |
| [Transaction Tests](./test_formats/transaction_test.md)             | - using a new simulator coming soon                                                                                                                                                                                                                                                       | None; executed directly from Python source,</br>using a release tag |
| Blob Transaction Tests                                               | - using the [eels/execute-blobs Simulator](./execute/hive.md#the-eelsexecute-blobs-simulator) and                                                                                                                                                                                                                         | None; executed directly from Python source,</br>using a release tag |

## Release Tracks

Fixtures are released on independent tracks. Each track has its own tag namespace, artifact, and cadence.

| Track     | Tag                  | Artifact                        | Scope                                                              | Built from        |
| --------- | -------------------- | ------------------------------- | ------------------------------------------------------------------ | ----------------- |
| Consensus | `consensus@vX.Y.Z`   | `fixtures_consensus.tar.gz`     | All forks, all tests (including legacy tests)                       | `main`/`master`   |
| Devnet    | `<feat>-devnet@vX.Y.Z` | `fixtures_<feat>-devnet.tar.gz` | All forks, all tests, for an upcoming-fork feature under active devnet testing | the devnet branch |
| Benchmark | `benchmark@vX.Y.Z`   | `fixtures_benchmark.tar.gz`     | EVM benchmarking tests                                             | `main`/`master`   |

- **Consensus** releases track clients' production branches and are tagged frequently (roughly once or twice a week). They are the "must pass" release for mainnet CI.
- **Devnet** releases target a specific feature under active development (e.g. `bal-devnet`). They are still WIP and may not contain full coverage for all EIPs; see the corresponding release notes for the coverage provided.
- **Benchmark** (and, in future, zkEVM) releases are produced separately for their specialized consumers.

## Versioning Scheme

Tags use the form `<track>@v<X>.<Y>.<Z>`. The underlying git tag is prefixed with `tests-` (e.g. `tests-consensus@v1.2.3`); the GitHub release title omits the prefix (`consensus@v1.2.3`).

The meaning of `X.Y.Z` depends on the track:

| Component | Consensus track             | Devnet track                |
| --------- | --------------------------- | --------------------------- |
| `X`       | Fork number                 | Devnet version              |
| `Y`       | Spec/test change → a change in behaviour |  Spec/test change → a change in behaviour |
| `Z`       | New tests only (no behaviour change) | New tests only (no behaviour change) |

This keeps the version purely ordered within a track: a higher `X.Y.Z` on the same track is always the newer release.

## Pinning Guidance

Mapped to a typical client CI setup:

- **Blocking gate (current + past forks).** Pin a specific `consensus@vX.Y.Z` for reproducible, no-rug-pull CI on your `master`/production branch, or follow the latest consensus release if a moving target is acceptable. This supersedes the old `fixtures_develop`/`fixtures_stable` artifacts.
- **Non-blocking gate (next fork).** Use the current `<feat>-devnet@vX.Y.Z` release for the upcoming fork's active devnet (e.g. `bal-devnet@vX.Y.Z`). Treat it as advisory — devnet coverage changes rapidly and should not block merges.

!!! note "Devnet vs. consensus overlap"
    Devnet releases are filled for all forks/tests, so they overlap with the consensus release. If your blocking gate already runs a consensus release, the devnet gate re-runs that shared coverage. Deduplicating that overlap is consumer-side concern handled when resolving/consuming releases.

## Creating a Fixture Release

Fixture releases are produced by manually dispatching the [`release_fixtures.yaml`](https://github.com/ethereum/execution-specs/blob/master/.github/workflows/release_fixtures.yaml) workflow. There is no tag to push by hand: the workflow builds the fixtures and, only on success, creates the tag and the (draft) GitHub release.

```bash
gh workflow run release_fixtures.yaml -f feature=<feature>@vX.Y.Z [-f branch=<branch>]
```

### Inputs

| Input     | Required          | Description                                                                                          |
| --------- | ----------------- | ---------------------------------------------------------------------------------------------------- |
| `feature` | yes               | `<feature>@vX.Y.Z` (the `tests-` prefix is optional and is added automatically to the tag).           |
| `branch`  | for `*-devnet`    | Branch to build and release from. Optional for non-devnet features; **required** for devnet releases. |

`<feature>` must be a key in [`.github/configs/feature.yaml`](https://github.com/ethereum/execution-specs/blob/master/.github/configs/feature.yaml) (e.g. `consensus`, `benchmark`), or a `<feat>-devnet` name that resolves to the shared `devnet` feature.

### Devnet releases

Devnet releases must be named `<feat>-devnet@vX.Y.Z` (e.g. `bal-devnet@v1.0.0`) and must specify the branch to release from:

```bash
gh workflow run release_fixtures.yaml -f feature=bal-devnet@v1.0.0 -f branch=bal-devnet-7
```

A bare `devnet@vX.Y.Z` (no `<feat>-` prefix), or a `*-devnet` release without a `branch`, fails fast in the first job before any fixtures are built.

### What the workflow produces

On success the workflow:

1. Builds `fixtures_<feature>.tar.gz` for the resolved feature (per its `evm-type` and `fill-params` in `feature.yaml`).
2. Creates the git tag `tests-<feature>@vX.Y.Z` on the released commit (the `branch` HEAD when given, otherwise the dispatch commit).
3. Publishes a **draft pre-release** to [`ethereum/execution-specs`](https://github.com/ethereum/execution-specs/releases), titled `<feature>@vX.Y.Z` (no `tests-` prefix), with the fixture tarball(s) attached.

| Example dispatch | Git tag | Release title | Artifact |
| ---------------- | ------- | ------------- | -------- |
| `feature=consensus@v1.2.3` | `tests-consensus@v1.2.3` | `consensus@v1.2.3` | `fixtures_consensus.tar.gz` |
| `feature=bal-devnet@v1.0.0 branch=bal-devnet-7` | `tests-bal-devnet@v1.0.0` | `bal-devnet@v1.0.0` | `fixtures_bal-devnet.tar.gz` |

The release is created as a draft; review and publish it from the GitHub releases page.

!!! tip "Release features opt into all fixture formats via `feature.yaml`"
    Tarball output (`.tar.gz`) does not by itself include the pre-allocation group formats (`BlockchainEngineXFixture`, `BlockchainEngineStatefulFixture`). A release feature requests them by adding `--generate-all-formats` to its `fill-params` in `.github/configs/feature.yaml`:
    ```console
    # Automatically enables --generate-all-formats due to .tar.gz output
    uv run fill --output=fixtures_consensus.tar.gz tests/
    ```

## Help Downloading Releases

The [`consume cache`](./consume/cache.md) command can be used to resolve EEST release and pre-release tags to release URLs and download them.
