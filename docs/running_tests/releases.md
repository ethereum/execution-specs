# EELS Fixture Releases

Test fixtures are published as **feature-scoped releases** on the
[`ethereum/execution-specs`](https://github.com/ethereum/execution-specs/releases)
repository — `tests@vX.Y.Z`, `<feat>-devnet@vX.Y.Z`, and `benchmark@vX.Y.Z`. Each is a
self-contained `.tar.gz` of JSON fixtures that execution clients consume in CI.

This page describes the release types, their versioning, the fixture formats they contain,
and how to consume them. For the release *mechanics* — how to cut a new release — see
[Releasing Test Fixtures](../dev/releasing_tests.md).

!!! note "Fixture releases vs. the spec-package `vX.Y.Z` tags"
    `ethereum/execution-specs` also publishes Python *spec package* releases tagged
    `vX.Y.Z` (e.g. [`v2.20.0`](https://github.com/ethereum/execution-specs/releases/tag/v2.20.0)).
    Those contain **no test fixtures** — they are the executable specification package only.
    Fixture releases are the feature-scoped tags described on this page and are never
    attached to the `vX.Y.Z` package tags.

## Test Release Types

Fixtures are released as independent types. Each type has its own tag namespace, artifact,
and cadence.

| Type      | Tag                    | Artifact                        | Scope                                                                          | Built from              |
| --------- | ---------------------- | ------------------------------- | ------------------------------------------------------------------------------ | ----------------------- |
| Tests     | `tests@vX.Y.Z`         | `fixtures.tar.gz`               | All forks, all tests (eventually including `ethereum/tests` state tests)        | latest `forks/*` branch |
| Devnet    | `<feat>-devnet@vX.Y.Z` | `fixtures_<feat>-devnet.tar.gz` | All forks, all tests, for an upcoming-fork feature under active devnet testing   | the devnet branch       |
| Benchmark | `benchmark@vX.Y.Z`     | `fixtures_benchmark.tar.gz`     | EVM benchmarking tests                                                          | latest `forks/*` branch |

- **Tests** releases track clients' production branches and are tagged frequently (roughly
  once or twice a week). They are the "must pass" release for mainnet CI, and supersede the
  old `fixtures_stable` / `fixtures_develop` artifacts.
- **Devnet** releases target a specific feature under active development (e.g. `bal-devnet`).
  They are advisory/non-blocking and may not yet cover every EIP; see the corresponding
  release notes for the coverage provided.
- **Benchmark** (and, in future, zkEVM) releases are produced separately for their
  specialized consumers.

## Versioning Scheme

Release tags use the form `<feature>@v<X>.<Y>.<Z>`. The underlying git tag is prefixed with
`tests-` to namespace it apart from the spec-package `vX.Y.Z` tags (e.g.
`tests-bal-devnet@v7.0.0`), except the default `tests` feature, which tags as
`tests@v<X>.<Y>.<Z>` directly (no doubled prefix). The GitHub release title always omits the
`tests-` prefix (`bal-devnet@v7.0.0`).

`X` identifies the fork or devnet a release targets; `Y` and `Z` order changes within that
target:

| Component | Tests                                               | Devnet                                               | Benchmark                       |
| --------- | --------------------------------------------------- | ---------------------------------------------------- | ------------------------------- |
| `X`       | Fork number                                         | Devnet number                                        | Fork number (mirrors target)    |
| `Y`       | Consensus-breaking spec change targeting fork `X`   | Consensus-breaking spec change targeting devnet `X`  | Mirrors the targeted feature    |
| `Z`       | Non-breaking change (refactor), new/modified tests  | Non-breaking change (refactor), new/modified tests   | Moves freely at its own pace    |

A client targeting fork/devnet `X` should take the release with **major == `X`**, the latest
**minor**, and ideally the latest **patch**. The major alone tells you whether a release is
relevant to you, and a bump in `Y` (e.g. `v7.0.0` → `v7.1.0`) signals a consensus-breaking
spec change in *your* target — read the release notes before adopting it.

This also lets two devnets of the same feature be maintained in parallel — e.g. `v3.0.1`
alongside `v7.0.0` — without ambiguity, the same way `2.x` and `3.x` coexist under semver.

## Fixture Formats

Fixture releases contain JSON test fixtures in various formats. Note that transaction type
tests are executed directly from Python source using the [`execute`](./execute/index.md)
command.

| Format                                                               | Consumed by the client                                                                                                                                                                                                                                                                    | Location in `.tar.gz` release                                       |
| -------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| [State Tests](./test_formats/state_test.md)                         | - directly via a `statetest`-like command<br/> (e.g., [go-ethereum/cmd/evm/staterunner.go](https://github.com/ethereum/go-ethereum/blob/4bb097b7ffc32256791e55ff16ca50ef83c4609b/cmd/evm/staterunner.go))                                                                                 | `./fixtures/state_tests/`                                           |
| [Blockchain Tests](./test_formats/blockchain_test.md)               | - directly via a `blocktest`-like command<br/> (e.g., [go-ethereum/cmd/evm/blockrunner.go](https://github.com/ethereum/go-ethereum/blob/4bb097b7ffc32256791e55ff16ca50ef83c4609b/cmd/evm/blockrunner.go))</br>- using the [eels/consume-rlp Simulator](./running.md#rlp) via block import | `./fixtures/blockchain_tests/`                                      |
| [Blockchain Engine Tests](./test_formats/blockchain_test_engine.md) | - using the [eels/consume-engine Simulator](./running.md#engine) and the Engine API                                                                                                                                                                                                          | `./fixtures/blockchain_tests_engine/`                               |
| [Transaction Tests](./test_formats/transaction_test.md)             | - using a new simulator coming soon                                                                                                                                                                                                                                                       | None; executed directly from Python source,</br>using a release tag |
| Blob Transaction Tests                                               | - using the [eels/execute-blobs Simulator](./execute/hive.md#the-eelsexecute-blobs-simulator)                                                                                                                                                                                                                         | None; executed directly from Python source,</br>using a release tag |

## Pinning Guidance

Mapped to a typical client CI setup:

- **Blocking gate (current + past forks).** Pin a specific `tests@vX.Y.Z` for reproducible,
  no-rug-pull CI on your `master`/production branch, or follow the latest `tests` release if
  a moving target is acceptable. This supersedes the old `fixtures_develop` / `fixtures_stable`
  artifacts.
- **Non-blocking gate (next fork).** Use the current `<feat>-devnet@vX.Y.Z` release for the
  upcoming fork's active devnet (e.g. `bal-devnet@vX.Y.Z`). Treat it as advisory — devnet
  coverage changes rapidly and should not block merges.

!!! note "Devnet vs. tests overlap"
    Devnet releases are filled for all forks/tests, so they overlap with the `tests` release.
    If your blocking gate already runs a `tests` release, the devnet gate re-runs that shared
    coverage. Deduplicating that overlap is a consumer-side concern handled when
    resolving/consuming releases.

## Downloading Releases

The [`consume cache`](./consume/cache.md) command resolves EELS release and pre-release tags
to release URLs and downloads them — for example:

```bash
uv run consume cache --input=tests@latest
uv run consume cache --input=bal-devnet@v7.0.0
```

Raw tarballs can also be fetched directly with the GitHub CLI:

```bash
gh release download tests-bal-devnet@v7.0.0 --repo ethereum/execution-specs --pattern '*.tar.gz'
```

To create a release, see [Releasing Test Fixtures](../dev/releasing_tests.md).
