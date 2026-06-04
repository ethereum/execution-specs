# Releasing Test Fixtures

This page covers the mechanics of cutting a test fixture release. For the release types,
their versioning, and consumption guidance, see
[EELS Fixture Releases](../running_tests/releases.md).

Fixture releases are produced by manually dispatching the
[`release_fixtures.yaml`](https://github.com/ethereum/execution-specs/blob/master/.github/workflows/release_fixtures.yaml)
workflow. There is no tag to push by hand. The workflow builds the fixtures and, only on
success, creates the tag and the (draft) GitHub release.

```bash
gh workflow run release_fixtures.yaml -f feature=<feature> -f version=vX.Y.Z [-f branch=<branch>]
```

## Inputs

| Input      | Required          | Description                                                                                          |
| ---------- | ----------------- | ---------------------------------------------------------------------------------------------------- |
| `feature`  | yes               | Feature name, e.g. `tests`, `benchmark`, or a `<feat>-devnet` name.                                   |
| `version`  | yes               | Release version `vX.Y.Z` (validated against `^v[0-9]+\.[0-9]+\.[0-9]+$`). Tagged as `tests-<feature>@<version>` (the `tests` feature tags as `tests@<version>`). |
| `branch`   | devnet only       | Branch to build and release from. Optional for non-devnet features; **required** for devnet releases. |
| `evm`      | no                | Override the evm impl (e.g. `geth`, `evmone`). Defaults to the feature's `evm-type` in `feature.yaml`. |
| `evm_repo` | no                | Override the t8n tool repo (e.g. `ethereum/go-ethereum`).                                              |
| `evm_ref`  | no                | Override the t8n tool branch / tag / commit.                                                          |

`<feature>` must be a key in
[`.github/configs/feature.yaml`](https://github.com/ethereum/execution-specs/blob/master/.github/configs/feature.yaml)
(e.g. `tests`, `benchmark`), or a `<feat>-devnet` name that resolves to the shared `devnet`
feature.

Input validation runs in
[`generate_build_matrix.py`](https://github.com/ethereum/execution-specs/blob/master/.github/scripts/generate_build_matrix.py)
(unit-tested) before any fixtures are built, and fails fast on:

- an empty `feature` or a `version` that is not `vX.Y.Z`;
- a bare `devnet` feature name (must carry a `<feat>-` prefix, e.g. `bal-devnet`);
- a `<feat>-devnet-<n>` feature name — the devnet index belongs in the `version` major, not
  the feature name (so `feature=bal-devnet-7` is rejected in favour of
  `feature=bal-devnet version=v7.0.0`);
- a `*-devnet` release missing a `branch`, or whose `version` major does not equal the devnet
  number in the branch (so `feature=bal-devnet branch=bal-devnet-7` must use `version=v7.*.*`).

## Devnet releases

Devnet releases must use a `<feat>-devnet` feature name (e.g. `feature=bal-devnet`) and must
specify the branch to release from. The `version` major must match the devnet number in the
branch:

```bash
gh workflow run release_fixtures.yaml -f feature=bal-devnet -f version=v7.0.0 -f branch=bal-devnet-7
```

## What the workflow produces

On success the workflow:

1. Builds `fixtures_<feature>.tar.gz` for the resolved feature (per its `evm-type` and
   `fill-params` in `feature.yaml`).
2. Creates the git tag `tests-<feature>@vX.Y.Z` (the `tests` feature tags as `tests@vX.Y.Z`,
   no doubled prefix) on the released commit (the SHA resolved once from the `branch` HEAD when
   given, otherwise the dispatch commit).
3. Publishes a **draft pre-release** to
   [`ethereum/execution-specs`](https://github.com/ethereum/execution-specs/releases), titled
   `<feature>@vX.Y.Z` (no `tests-` prefix), with the fixture tarball(s) attached.

| Example dispatch | Git tag | Release title | Artifact |
| ---------------- | ------- | ------------- | -------- |
| `feature=tests version=v24.0.0` | `tests@v24.0.0` | `tests@v24.0.0` | `fixtures.tar.gz` |
| `feature=bal-devnet version=v7.0.0 branch=bal-devnet-7` | `tests-bal-devnet@v7.0.0` | `bal-devnet@v7.0.0` | `fixtures_bal-devnet.tar.gz` |

The release is created as a draft; review and publish it from the GitHub releases page.

## Cutting a release

1. **Pick the next version** per the
   [Versioning Scheme](../running_tests/releases.md#versioning-scheme) for the feature you're
   releasing (e.g. the next `tests` release after `tests@v24.1.0` is `tests@v24.1.1` for a
   non-breaking/new-tests bump, or `tests@v24.2.0` for a consensus-breaking spec change).
2. **Dispatch the workflow** from the
   [Actions tab](https://github.com/ethereum/execution-specs/actions/workflows/release_fixtures.yaml)
   or via the CLI:

   ```bash
   gh workflow run release_fixtures.yaml -f feature=tests -f version=v24.1.1
   # devnet releases additionally require the branch (major must match its number):
   gh workflow run release_fixtures.yaml -f feature=bal-devnet -f version=v7.0.0 -f branch=bal-devnet-7
   ```

3. **Wait for the build to succeed.** On success the workflow creates the
   `tests-<feature>@vX.Y.Z` tag on the target commit and drafts the GitHub release with the
   fixture tarball attached. If any job fails, no tag or release is created — fix the cause
   and re-dispatch.
4. **Review and publish the draft.** Open the draft on the
   [releases page](https://github.com/ethereum/execution-specs/releases), check the
   auto-generated notes (anchored at the prior release on the same feature via
   `--notes-start-tag`), and click *Publish release* when ready.

!!! tip "Release features opt into all fixture formats via `feature.yaml`"
    Tarball output (`.tar.gz`) does not by itself include the pre-allocation group formats
    (`BlockchainEngineXFixture`, `BlockchainEngineStatefulFixture`). A release feature
    requests them by adding `--generate-all-formats` to its `fill-params` in
    `.github/configs/feature.yaml`:
    ```console
    # .tar.gz no longer auto-enables all formats (changed in #2702); request
    # them explicitly with --generate-all-formats
    uv run fill --generate-all-formats --output=fixtures.tar.gz tests/
    ```
