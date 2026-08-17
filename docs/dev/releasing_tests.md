# Releasing Test Fixtures

This page covers the mechanics of cutting a test fixture release. For the release types, their versioning, and consumption guidance, see [EELS Fixture Releases](../running_tests/releases.md).

Fixture releases are produced by manually dispatching the [`release_fixtures.yaml`](https://github.com/ethereum/execution-specs/blob/master/.github/workflows/release_fixtures.yaml) workflow. There is no tag to push by hand. The workflow builds the fixtures and, only on success, drafts the GitHub release; publishing the draft creates the tag.

```bash
gh workflow run release_fixtures.yaml -f feature=<feature> -f version=vX.Y.Z [-f branch=<branch>]
```

## Inputs

| Input      | Required          | Description                                                                                          |
| ---------- | ----------------- | ---------------------------------------------------------------------------------------------------- |
| `feature`  | yes               | Feature name, for example `tests`, `benchmark`, `zkevm-benchmark`, or a `<feat>-devnet` name.          |
| `version`  | yes               | Release version `vX.Y.Z` (validated against `^v[0-9]+\.[0-9]+\.[0-9]+$`). Tagged as `tests-<feature>@<version>` (the `tests` feature tags as `tests@<version>`). |
| `branch`   | feature-dependent | Branch or source tag to release from. Devnet and zkEVM benchmark releases require this input.         |
| `evm`      | no                | Override the evm impl (e.g. `geth`, `evmone`). Defaults to the feature's `evm-type` in `feature.yaml`. |
| `evm_repo` | no                | Override the t8n tool repo (e.g. `ethereum/go-ethereum`).                                              |
| `evm_ref`  | no                | Override the t8n tool branch / tag / commit.                                                          |
| `cached`   | no                | Draft from the newest nightly artifact instead of refilling (`tests` only): `build` and `combine` are skipped and the tag targets the nightly's commit. See [Cached releases](#cached-releases). |
| `commit`   | no                | Release the nightly built at this commit (7+ hex chars) instead of the newest one; implies `cached`. |

`<feature>` must be a key in [`.github/configs/feature.yaml`](https://github.com/ethereum/execution-specs/blob/master/.github/configs/feature.yaml) (e.g. `tests`, `benchmark`), or a `<feat>-devnet` name that resolves to the shared `devnet` feature.

Input validation runs in [`generate_build_matrix.py`](https://github.com/ethereum/execution-specs/blob/master/.github/scripts/generate_build_matrix.py) (unit-tested) before any fixtures are built, and fails fast on:

- an empty `feature` or a `version` that is not `vX.Y.Z`;
- an `evm` override that is not a key in `.github/configs/evm.yaml`;
- a bare `devnet` feature name (must carry a `<feat>-` prefix, e.g. `bal-devnet`);
- a `<feat>-devnet-<n>` feature name — the devnet index belongs in the `version` major, not the feature name (so `feature=bal-devnet-7` is rejected in favour of `feature=bal-devnet version=v7.0.0`);
- a `*-devnet` release missing a `branch`, a `branch` outside the `devnets/<feat>/<n>` shape (e.g. `devnets/bal/7`), or a `version` major that does not equal the devnet number `<n>` in the branch (so `feature=bal-devnet branch=devnets/bal/7` must use `version=v7.*.*`).

## Devnet releases

Devnet releases must use a `<feat>-devnet` feature name (e.g. `feature=bal-devnet`) and must specify the branch to release from. Devnet branches follow the `devnets/<feat>/<n>` scheme (e.g. `devnets/bal/7`), and the `version` major must match the devnet number `<n>` in the branch:

```bash
gh workflow run release_fixtures.yaml -f feature=bal-devnet -f version=v7.0.0 -f branch=devnets/bal/7
```

## zkEVM benchmark releases

Publish the source `tests-zkevm@vX.Y.Z` release before you make its benchmark release. The benchmark version must match the source version.

```bash
gh workflow run release_fixtures.yaml \
  --ref 'tests-zkevm@vX.Y.Z' \
  -f feature=zkevm-benchmark \
  -f version=vX.Y.Z \
  -f branch='tests-zkevm@vX.Y.Z'
```

The workflow uses the Geth repository and commit in `evm.yaml` by default. A releaser can use the existing `evm`, `evm_repo`, and `evm_ref` inputs to override that configuration.

The workflow fills Amsterdam compute benchmarks at 10M, 30M, and 60M gas. It produces only `blockchain_test` fixtures.

Before upload, the workflow checks the stateless data in each fixture. It also checks the source version and the destination release.

## What the workflow produces

On success the workflow:

1. Builds `fixtures_<feature>.tar.gz` (the `tests` feature builds `fixtures.tar.gz`) for the resolved feature (per its `evm-type` and `fill-params` in `feature.yaml`).
2. Drafts a **pre-release** to [`ethereum/execution-specs`](https://github.com/ethereum/execution-specs/releases) with the fixture tarball(s) attached, titled and tagged `tests-<feature>@vX.Y.Z` (the `tests` feature tags as `tests@vX.Y.Z`, no doubled prefix).
3. Targets the tag at the released commit (the SHA resolved once from the `branch` HEAD when given, otherwise the dispatch commit). The tag name and target are stored as draft metadata; the git tag itself is only created when the draft is published, so an unpublished draft can be edited or deleted without leaving a tag behind.

| Example dispatch | Git tag | Release title | Artifact |
| ---------------- | ------- | ------------- | -------- |
| `feature=tests version=v24.0.0` | `tests@v24.0.0` | `tests@v24.0.0` | `fixtures.tar.gz` |
| `feature=bal-devnet version=v7.0.0 branch=devnets/bal/7` | `tests-bal-devnet@v7.0.0` | `tests-bal-devnet@v7.0.0` | `fixtures_bal-devnet.tar.gz` |
| `feature=zkevm-benchmark version=v0.9.0 branch=tests-zkevm@v0.9.0` | `tests-zkevm-benchmark@v0.9.0` | `tests-zkevm-benchmark@v0.9.0` | `fixtures_zkevm-benchmark.tar.gz` |

The release is created as a draft; review and publish it from the GitHub releases page.

## Cutting a release

1. **Pick the next version** per the [Versioning Scheme](../running_tests/releases.md#versioning-scheme) for the feature you're releasing (e.g. the next `tests` release after `tests@v24.1.0` is `tests@v24.1.1` for a non-breaking/new-tests bump, or `tests@v24.2.0` for a consensus-breaking spec change).
2. **Dispatch the workflow** from the [Actions tab](https://github.com/ethereum/execution-specs/actions/workflows/release_fixtures.yaml) or via the CLI:

   ```bash
   gh workflow run release_fixtures.yaml -f feature=tests -f version=v24.1.1
   # devnet releases additionally require the branch (major must match its number):
   gh workflow run release_fixtures.yaml -f feature=bal-devnet -f version=v7.0.0 -f branch=devnets/bal/7
   ```

3. **Wait for the build to succeed.** On success the workflow drafts the GitHub release with the fixture tarball attached. If any job fails, no release is drafted: fix the cause and re-dispatch.
4. **Review and publish the draft.** Open the draft on the [releases page](https://github.com/ethereum/execution-specs/releases), check the auto-generated notes (anchored at the prior release on the same feature via `--notes-start-tag`), and click *Publish release* when ready. Publishing creates the `tests-<feature>@vX.Y.Z` tag on the target commit; until then a mispicked version can be fixed by editing the draft, with no stray tag to delete.

!!! tip "Release features opt into all fixture formats via `feature.yaml`"
    Tarball output (`.tar.gz`) does not by itself include the pre-allocation group formats (`BlockchainEngineXFixture`, `BlockchainEngineStatefulFixture`). A release feature requests them by adding `--generate-all-formats` to its `fill-params` in `.github/configs/feature.yaml`:
    ```console
    # .tar.gz no longer auto-enables all formats (changed in #2702); request
    # them explicitly with --generate-all-formats
    uv run fill --generate-all-formats --output=fixtures.tar.gz tests/
    ```

## Nightly fill

The same workflow also runs on a nightly schedule (02:00 UTC) as a release rehearsal: it fills the mainnet `tests` feature (all tests, slow included, all fixture formats, up to the latest mainnet fork — dev forks are not included) through the exact release pipeline, but stops after `combine`, so no tag or release is created. Each run uploads a `fixtures_<commit>` workflow artifact (short hash of the built commit, containing `fixtures.tar.gz`) with a 5-day retention: a rotating, always-available build of the mainnet fixtures, effectively a `tests@` release candidate on demand. A scheduled run skips itself when there are no new commits since the last nightly that actually filled — a skipped or failed nightly never advances that baseline, so no commit slips through unfilled. A quiet stretch without commits still re-fills once the last fill is four days old, or its artifact is gone, so a live artifact always exists within the five-day retention.

## Cached releases

A `tests@` release can reuse the newest nightly artifact instead of refilling: tick the `cached` checkbox in the dispatch UI, or pass the flag on the CLI:

```bash
gh workflow run release_fixtures.yaml -f feature=tests -f version=vX.Y.Z -f cached=true
# or release the nightly built at a specific commit (implies cached):
gh workflow run release_fixtures.yaml -f feature=tests -f version=vX.Y.Z -f commit=<hash>
```

The `build` and `combine` jobs are skipped; the `release` job downloads the `fixtures_<commit>` artifact from the newest nightly run that actually filled — or, with the `commit` input, from the nightly built at that commit — and drafts the same release a fresh fill would produce, targeted at the exact commit the nightly built, so publishing it creates the `tests@vX.Y.Z` tag on that commit. The whole run takes minutes on a hosted runner. Review and publish the draft exactly as in [Cutting a release](#cutting-a-release).

The cached path's validation (unit-tested in [`resolve_cached_release.py`](https://github.com/ethereum/execution-specs/blob/master/.github/scripts/resolve_cached_release.py)) fails fast when:

- the `feature` is not `tests`, or a `branch` is given (the nightly fills the default branch);
- the `version` is not `vX.Y.Z` or does not exceed the newest existing `tests@` tag;
- no nightly run with a live `fixtures_<commit>` artifact exists — or none matching the `commit` input; the error lists the reusable nightlies (artifacts are retained for five days: past that, dispatch a fresh fill);
- the resolved nightly does not contain the newest existing `tests@` release (a cached release must never regress content; re-releasing the identical commit is allowed);
- the nightly's commit is not an ancestor of the current default branch head.

A cached release contains exactly what the resolved nightly filled: commits that landed after it are **not** included, and the run's step summary lists them so the releaser can decide between the cached artifact and a fresh fill.
