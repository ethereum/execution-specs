# Publishing Simulator Images

The workflow `.github/workflows/docker-images.yaml` publishes the images described in [Simulator Images](../running_tests/hive/images/index.md) to `ghcr.io/ethereum/execution-specs`. This page covers when it runs, what each job does, and how to operate it.

## When it runs

| Run | Trigger | Builds |
| --- | --- | --- |
| push | a push to a `forks/**` or `devnets/**` branch that is still current when its run starts | the repository image of the head, and the simulator images of the branch's current release, its highest one, rebuilt with the head so that the branch's channel tag (`latest`, `glamsterdam-devnet-8`) follows it |
| release | a fixture release is published (`release: published`) | the fixture images and the tests image of the release, and the simulator images pairing it with the head of the branch it was cut from |
| nightly | the scheduled fill in `release_fixtures.yaml` completes, which calls this workflow | every image at the fill commit, from the fill's `fixtures_<sha>` artifact; test-carrying images get `nightly` and `nightly-<sha>`, the repository image gets `nightly` and `sha-<sha>` |
| by hand | the Actions tab or `gh workflow run` | any of the above, and testing on a fork |

The branch a release belongs to is inferred from its tag, `tests@` for the default branch and `tests-<name>-devnet@v<n>.` for `devnets/<name>/<n>`, so the release trigger needs no input. A release whose series is not tied to a branch, such as a benchmark release, is rejected by the planner.

The workflow authenticates to ghcr with the job token and needs no secrets. Publishing requires `packages: write`, which the workflow requests; the nightly call additionally needs `actions: read` to download the fill's artifact.

## Ordering

Runs share two publication queues: mainnet (including nightly publication) and devnets. Runs in a queue do not overlap because they can write the same tags. `queue: max` retains up to 100 pending runs; `cancel-in-progress: false` lets the running one finish. A release run is never discarded merely because another push arrives. GitHub cancels additional runs if the queue is full, so check for overflow before relying on a very large backfill.

A push checks its commit against the branch head before installing dependencies or building images. If superseded, the plan job succeeds and the image jobs are skipped. For five pushes A–E during A's build, B–D therefore pass through this check without building, and E builds if it is still current. A release always proceeds because later pushes depend on its fixture and tests images. Independent devnet updates stay queued too.

If the branch moves during a build, the simulator publication step checks again: a push skips publishing its simulator images, and a release publishes only its release tag. The repository image may already have been published. These skips exit successfully. Actual build, check or registry errors still fail the run.

Nightly publication uses the mainnet queue because it also writes repository images under `sha-<commit>`. The scheduled fill itself remains serialized by the release workflow. Manual nightly publication joins the same image queue.

The five simulator images are pushed by independent jobs, so a channel tag can point at the new release on four of them and the old one on the fifth while a job is failing. The step summary of every run lists each pushed tag with its digest, commit and release, and the `digests-*` artifacts hold the same as JSON, so what a tag pointed to at any time can be traced.

## Jobs

| Job | Runs | Does |
| --- | --- | --- |
| `plan` | always | Skips superseded pushes, resolves a manual nightly artifact, then installs the testing package and runs `eest images plan`, which computes every name, tag and build of the run from `execution_testing.tools.docker_images`. The other jobs only consume its JSON output and check out the commit it planned. |
| `base` | when a plan is produced | Builds `packages/testing/docker/base/Dockerfile` at the planned commit and pushes it as `ghcr.io/ethereum/execution-specs:sha-<7 hex>`, plus `latest` on the default branch, the branch tag on a devnet branch, or `nightly` for a fill. |
| `fixtures` | release and nightly runs | Takes the release tarball, or the fill's artifact, once per fixture format, builds `packages/testing/docker/fixtures/Dockerfile` and pushes `fixtures/<format>` under the release tag and every channel tag the release holds. |
| `tests` | release and nightly runs | Checks out the release tag, or the fill commit, beside the planned commit and builds `packages/testing/docker/tests/Dockerfile` from its `tests/` directory, pushed as `tests` under the same tags as the fixture images. |
| `images` | per planned simulator | Builds the simulator with `packages/testing/docker/hive/build.sh` from the repository image at the planned commit and the fixture or tests image, verifies it with `check.sh`, confirms the branch has not moved, and pushes the release tag and the channel tags. |

The check in the `images` job is what makes the execute images safe to publish: it collects the release's tests under the branch-head framework, so that a source tree the framework can no longer load fails the job instead of every hive run that pulls the tag. For a consume image it verifies that the fixture index is non-empty, covers only the image's format, and points only at files present in the image. A failed check leaves that simulator image's tags unchanged. The repository, fixture and tests images may already have been published, and other simulator jobs can still advance.

To see what a run would do without running it, run the planner locally; it needs network access to list the releases:

```bash
uv run eest images plan --branch devnets/glamsterdam/8 --sha "$(git rev-parse HEAD)" --default-branch forks/amsterdam | jq .
uv run eest images plan --release tests@v20.0.2 --sha "$(git rev-parse origin/forks/amsterdam)" --default-branch forks/amsterdam | jq .
```

## Running it by hand

Publish the images for an existing release; the branch is inferred:

```bash
gh workflow run docker-images.yaml --ref forks/amsterdam -f release_tag=tests-glamsterdam-devnet@v8.1.4
```

Rebuild a branch's simulator images for its current release without a new release:

```bash
gh workflow run docker-images.yaml --ref forks/amsterdam -f branch=devnets/glamsterdam/8
```

Publish a nightly fill whose artifact is still live, by the commit it built:

```bash
gh workflow run docker-images.yaml --ref forks/amsterdam -f nightly_sha=<commit>
```

`nightly_sha` accepts 7–40 lowercase hex characters. The helper `.github/scripts/resolve_image_nightly.py` expands it to a full commit SHA and finds a completed scheduled fill in the publishing repository with a live `fixtures_<sha7>` artifact. It can reuse the artifact even if that fill's later image publication failed. The download uses that run's ID and the job token; an expired or missing artifact fails before any image is built. The scheduled workflow call already knows its run ID and does not need this lookup.

`--ref` selects the workflow file to run; the inputs select what is built. A manual nightly run republishes `nightly` at the requested fill, so choosing an older fill deliberately moves that channel back.

## First rollout

Simulator images need the fixture images and the tests image of the release they pair with. As each branch adopts image publishing, publish them for that branch's current release by hand before relying on push builds. Rollout is gradual; consumer instructions should name only tags that have already been published. From then on, published releases and nightly fills keep them current. The planner prints a branch's current release in the `images` entries of a push plan.

## Testing on a fork

1. Push the branch with the workflow to the fork. A manual run requires the workflow file on the fork's default branch, so either add the branch to the `push` trigger temporarily or make it the fork's default branch for the duration of the test.
2. Releases are not forked. Pass `release_repo=ethereum/execution-specs` to a manual run so that the planner lists upstream releases and the fixtures job downloads the tarball from upstream; the tests job checks the release tag out of that repository too.
3. Packages created by the job token are private at first. Make them public in the package settings, or log in to ghcr locally and run hive with `--docker.auth`.
4. Point hive at the fork's namespace with `--sim.buildarg image=ghcr.io/<user>/execution-specs/hive/consume-engine`.

The images are linked to the repository through the `org.opencontainers.image.source` label, which the workflow sets to the publishing repository, so later pushes from the same repository keep write access to the packages.

Local regression checks run with `just test-ci-scripts` (including `.github/scripts/tests/test_image_workflow.py`) and the catalogue tests in `packages/testing/src/execution_testing/tools/tests/test_docker_images.py`. They exercise the publishing guards and artifact lookup without contacting GitHub.

Before the first upstream publish, verify these cases on the fork:

| Case | Expected result |
| --- | --- |
| Five pushes during a build | Intermediate pushes skip their builds successfully; the current push publishes. |
| A release queued between pushes | The release publishes its fixture and tests images; later simulator builds can pull them. |
| Updates to two devnet branches | Both branches publish; one cannot replace the other's pending run. |
| A simulator check fails | That simulator's tags stay unchanged; its job fails. |
| A release has no fixture tarball | Planning fails before image builds. |
| A release is paired with the wrong branch in `eest images plan` | The planner rejects the pair. |
| A manual nightly uses an earlier successful fill | The exact artifact, tests and framework commit are used. |
| A fill succeeded but its image publication failed | A manual nightly can reuse its live artifact. |
| A nightly artifact expired or is missing | Resolution fails before image builds. |
| A completed run is rerun | Tags and digests are recorded again; superseded push runs skip. |

## Adding an image

Add an entry to `IMAGES` in `execution_testing.tools.docker_images` with the image name, its family, and either the fixture format it carries or `tests=True` for an execute simulator; add the entry point case in `packages/testing/docker/hive/entrypoint.sh` and the format or collection paths in `build.sh` and `check.sh`; and add the family's Dockerfiles under `packages/testing/docker/<family>/` if the family is new. The tests in `tools/tests/test_docker_images.py` pin the naming rules; extend them with the new image.

## Registry housekeeping

No image retention period is defined yet, and the workflow does not delete old images.

Layers are content-addressed and deduplicated, so a push uploads only what changed, and public packages carry no storage cost. Manifests accumulate though: every push of a channel tag leaves the previous image stored without a tag, and a digest recorded for a run is only useful while its manifest exists. Add a scheduled cleanup, for example with `actions/delete-package-versions`, that deletes untagged versions older than a stated retention period and document that period next to the digest guidance in the how-to. This is not part of the workflow yet.

## Before merging

- Confirm that the organisation's package settings allow Actions to create public packages under `ghcr.io/ethereum`.
- Publish the current releases by hand (first rollout above) before the hive PR that makes the simulators pull the images is merged.
