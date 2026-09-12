# Why the Simulators Run from Images

## Building in hive was slow and fragile

Until the images existed, every hive run built each eels simulator from a Dockerfile that installed git, cloned execution-specs, ran `uv sync`, downloaded a fixture release and extracted it. Two things made this a poor fit for continuous integration. GitHub rate-limits anonymous clones per source address since May 2025, and shared runners hit the limit often enough that builds failed before any test ran. And the hive dashboards run on ephemeral runners that install Docker fresh for every job, so none of that work is ever cached: the only cache available across jobs is the registry. The design goal followed from that: one pull per simulator, nothing built and nothing extracted afterwards.

## Tests and framework versions

A hive run has two inputs that change at different rates: the tests, which change when a release is cut, and the simulator and framework code, which changes on every push and must be able to change without a release, because the per-client exception mappings live there and clients ship fixes between releases. The dashboards have always pinned the first and followed the second.

A simulator tag selects the tests. The branch's current release, behind `latest` or a devnet branch channel, receives framework updates on pushes. Older releases retain their last framework build. For consume simulators, the tests are generated fixtures. For execute simulators, they are the Python sources from the release commit, snapshotted into the image. This lets both kinds of simulator select the same release even when its framework has moved on. Nightly images take tests and framework from the fill commit together.

The price of snapshotting sources rather than fixtures is that sources import the framework. A framework change can make an older test tree fail to load, which a fixture never does. Two things keep that in check. Every execute image is verified before it is pushed by collecting the release's tests under the head framework, so an incompatible pair fails the build and the moving tag stays where it was. And releases are frequent: the mainnet line releases about every two weeks and devnets far more often, so the window between a release and the framework that runs it is short, and the next release closes it.

## Two data primitives and a code primitive

The code is published as the repository image when a push is still current when its queued run starts. Superseded pushes skip building. The test content is published once per release: fixture images, one per format, and a tests image with the source tree. All three are small to rebuild and every combination can be assembled from them, which is also the fallback for a pair that was never published.

They are not what hive runs, though. A `FROM` reuses the source image layers; a `COPY --from` creates a new layer containing the copied files. The classic builder that Hive uses pays that copy cost during the build. Copying the 3.8 GB of `blockchain_tests` into the simulator image took 107 s on a fast machine, and an ephemeral runner would pay that on every job. So the combination is assembled once, in the publishing workflow, as a per-simulator image that hive only pulls. Hive's own build of the simulator image is then a `FROM` and a few metadata layers and took about a second in the local measurement, excluding image pulls and test execution.

For a consume image the fixture image is the base layer and the repository filesystem is copied on top. The fixture layer is the large one, and as the base layer it is shared by digest between every simulator image built from the same release and uploaded once. Rebuilding after a push copies the 700 MB repository filesystem, about 20 s, instead of the fixtures. For an execute image the repository image is the base and the tests tree, a few tens of megabytes, replaces its own.

## Names

The registry names follow the repository and the runner. The repository image sits at the repository's own address, `ghcr.io/ethereum/execution-specs`, which is where anyone looks for the image of a repository. Below it, a namespace per runner holds the ready-to-run images, `hive/<simulator>` today, with room for further families such as direct test runners; `fixtures/<format>` and `tests` hold the data. Hive image leaves are the simulator directory names in ethereum/hive, so the two never need translating.

Release tags use the familiar release names: mainnet tags omit `tests@`; devnet tags omit `tests-` and replace `@` with `-`. The [reference](reference.md#tags) gives the exact mapping. The `latest` channel selects the highest mainnet release. There are only two other kinds of tag, both named after things EEST itself has no name for. Channel tags name the current state of a line: `latest` and `glamsterdam-devnet-8` pair a branch's highest release with its head, and `glamsterdam-devnet-latest` follows the newest devnet of a series. The dashboards follow the first kind, one devnet at a time; the second is for anyone who wants whatever is newest. `nightly` names the nightly fill, which has no release, by the commit it built. Version-prefix aliases in the Docker style, `v20`, `v20.0`, were considered and left out: nothing consumes them, and every alias is a promise to keep. No tag is named after a fork: the default branch is renamed at every fork, so the mainnet line is `latest`, and a name like `amsterdam` would also misdescribe a release that is not yet filled for that fork.

The rules live in one module, `execution_testing.tools.docker_images`, with tests, and the publishing workflow computes every name from it in a single planning step. Adding an image is a catalogue entry and, for a new family, a directory.

## Reproducibility

A run is reproducible when it names what ran. Every simulator image carries the release and the framework commit as labels and as environment variables, and the simulators print them in their log headers: `fixtures release` and `consume ref`, or `tests release`, `tests ref` and `execute ref`. That pair of sources can be assembled from the published components. Consume simulators can also select it with `Dockerfile.git`; execute source builds run the branch's tests, so reproducing a release snapshot under a newer framework requires the tests image. Tags deliberately stop there: a tag names sources, and the same sources are pushed again under the same tag when the branch moves or a run is repeated, so no tag is promised to be immutable. Byte-exact identity is what registries already provide, the digest, which the publishing run records for every tag it pushes and hive accepts as `tag=<tag>@sha256:<digest>`.

## What it costs

A job pulls one simulator image: about 550 MB compressed for `consume-rlp`, less for the others, unpacked to about 4.5 GB on disk during the pull. That unpacking is the floor for any design, because `consume` reads plain JSON files. Publishing costs a build of every simulator image for a current push, for the branch's current release, five jobs measured locally at about 30 s each, and a build per simulator on each release and each nightly fill plus the fixture and tests images. Registry storage is shared through the fixture layers. Every push leaves the previous image of a channel tag untagged but stored; a scheduled cleanup that removes untagged versions after a retention period is planned and not yet part of the workflow.

## Alternatives that were considered

- Authenticating the clone with a token would have fixed the rate limit and nothing else. Every job would still build and extract, and the token would have to be kept out of build arguments, logs and results.
- Combining the primitives at hive build time works and needs nothing from hive, but costs the 107 s copy on every job without a cache.
- Keeping the fixtures compressed in the image and extracting at container start relocates the extraction step rather than removing it.
- Letting execute images run the branch head's tests would have been simpler to build, but a release tag would then have meant different tests on execute and consume images. The nightly channel offers that coherent build under a name of its own: `nightly` is tests, sources and framework from one commit.
- Mounting the fixture image into the simulator container at run time, with Docker's image mounts, starts a container over the 3.8 GB fixture set in about a second and would remove the baked layer again. It needs hive to grow a mount option and to require Docker 28, and Docker still marks image mounts experimental. It remains the natural next step once those conditions are met.
