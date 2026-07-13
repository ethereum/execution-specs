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
- an `evm` override that is not a key in `.github/configs/evm.yaml`;
- a bare `devnet` feature name (must carry a `<feat>-` prefix, e.g. `bal-devnet`);
- a `<feat>-devnet-<n>` feature name — the devnet index belongs in the `version` major, not
  the feature name (so `feature=bal-devnet-7` is rejected in favour of
  `feature=bal-devnet version=v7.0.0`);
- a `*-devnet` release missing a `branch`, a `branch` outside the `devnets/<feat>/<n>` shape
  (e.g. `devnets/bal/7`), or a `version` major that does not equal the devnet number `<n>` in
  the branch (so `feature=bal-devnet branch=devnets/bal/7` must use `version=v7.*.*`).

## Devnet releases

Devnet releases must use a `<feat>-devnet` feature name (e.g. `feature=bal-devnet`) and must
specify the branch to release from. Devnet branches follow the `devnets/<feat>/<n>` scheme
(e.g. `devnets/bal/7`), and the `version` major must match the devnet number `<n>` in the
branch:

```bash
gh workflow run release_fixtures.yaml -f feature=bal-devnet -f version=v7.0.0 -f branch=devnets/bal/7
```

## What the workflow produces

On success the workflow:

1. Builds `fixtures_<feature>.tar.gz` (the `tests` feature builds `fixtures.tar.gz`) for the
   resolved feature (per its `evm-type` and `fill-params` in `feature.yaml`).
2. Creates the git tag `tests-<feature>@vX.Y.Z` (the `tests` feature tags as `tests@vX.Y.Z`,
   no doubled prefix) on the released commit (the SHA resolved once from the `branch` HEAD when
   given, otherwise the dispatch commit).
3. Publishes a **draft pre-release** to
   [`ethereum/execution-specs`](https://github.com/ethereum/execution-specs/releases), titled
   the same as the git tag, with the fixture tarball(s) attached.

| Example dispatch | Git tag | Release title | Artifact |
| ---------------- | ------- | ------------- | -------- |
| `feature=tests version=v24.0.0` | `tests@v24.0.0` | `tests@v24.0.0` | `fixtures.tar.gz` |
| `feature=bal-devnet version=v7.0.0 branch=devnets/bal/7` | `tests-bal-devnet@v7.0.0` | `tests-bal-devnet@v7.0.0` | `fixtures_bal-devnet.tar.gz` |

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
   gh workflow run release_fixtures.yaml -f feature=bal-devnet -f version=v7.0.0 -f branch=devnets/bal/7
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

## Nightly fill

The same workflow also runs on a nightly schedule (02:00 UTC) as a release rehearsal: it fills the `nightly` feature (all tests, slow included, all fixture formats, up to the dev fork) through the exact release pipeline, but stops after `combine`, so no tag or release is created. Each run uploads a `fixtures_nightly.tar.gz` workflow artifact with a 5-day retention. A scheduled run skips itself when there are no new commits since the last successful nightly fill; a failed nightly keeps re-running until it goes green, so no commit slips through unfilled. A quiet stretch without commits still re-fills once the last successful nightly is four days old, so a live artifact always exists within the five-day retention.
