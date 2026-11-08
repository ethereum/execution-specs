"""
Names and build plans of the docker images for the hive simulators.

The repository publishes four kinds of images to ghcr.io, described in
`docs/running_tests/hive/images/`: the repository image
(`ghcr.io/ethereum/execution-specs`), one fixture image per fixture format
(`.../fixtures/<format>`), the tests image holding the test sources of a
release (`.../tests`), and one ready-to-run image per hive simulator
(`.../hive/<simulator>`).

Simulator tags select the tests. Release tags are immutable: the release run
builds them once. Release tags omit the mainnet `tests@` prefix or the devnet
`tests-` prefix and replace `@` with `-`. Channel tags pair the highest
release of a branch with its head and move with it: `latest` for the default
branch and `<name>-devnet-<n>` for a devnet branch. `nightly` names the most
recent nightly fill, with tests and framework from the fill commit. The
fixture and tests images carry only release tags and `nightly`, the
repository image only `sha-<commit>`: they are building blocks of the
simulator images, not a stable interface. This module holds the naming rules
in one place and computes what a publishing run has to build. The
`eest images` command exposes it to the publishing workflow, which consumes
the plan as JSON.
"""

import os
import re
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

import requests
import yaml

DEFAULT_REPOSITORY = "ethereum/execution-specs"
"""GitHub repository the images are published from, as `owner/name`."""
REGISTRY = "ghcr.io"
MAIN_LINE_SERIES = "tests"
"""Release series of the main line, `tests@vX.Y.Z`: the mainnet releases."""
SERIES_PREFIX = "tests-"
"""Prefix of every other release series, e.g. `tests-glamsterdam-devnet`."""
DEVNET_SUFFIX = "-devnet"
"""Suffix of a devnet series name; its major version is the devnet number."""
FIXTURES_IMAGE = "fixtures"
"""Image path of the fixture images below the repository, before the format."""
TESTS_IMAGE = "tests"
"""Image path of the tests image below the repository."""
LATEST = "latest"
NIGHTLY = "nightly"
LEGACY_SUFFIX = "-legacy"
"""Suffix of the deprecated build arguments variant of `latest`."""
FIXTURES_ASSET_RE = re.compile(r"^fixtures(_.*)?\.tar\.gz$")
VERSION_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:-(.+))?$")
TAG_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$")
"""What docker accepts as an image tag."""
DEVNET_BRANCH_RE = re.compile(r"^devnets/([^/]+)/(\d+)$")
FEATURE_CONFIG = ".github/configs/feature.yaml"
"""Release workflow config: each feature's `fill-params` name its forks."""
SHARED_DEVNET_FEATURE = "devnet"
"""Entry of `FEATURE_CONFIG` shared by every `<name>-devnet` feature."""


@dataclass(frozen=True)
class Image:
    """A published, ready-to-run image."""

    name: str
    """Image name; for hive simulators the hive simulator directory name."""
    family: str
    """Registry namespace; also the `docker/<family>` directory building it."""
    fixture_format: str | None = None
    """Fixture format the image carries: a consume simulator."""
    tests: bool = False
    """Whether the image carries a release's test sources: execute."""

    @property
    def path(self) -> str:
        """Image path below the repository, e.g. `hive/consume-engine`."""
        return f"{self.family}/{self.name}"

    @property
    def kind(self) -> str:
        """Return `consume` for an image with fixtures, else `execute`."""
        return "consume" if self.fixture_format else "execute"

    @property
    def content_path(self) -> str:
        """
        Return the image path of the test content the image is built from.

        The fixture image of its format for a consume simulator, e.g.
        `fixtures/blockchain_tests_engine`, else the tests image.
        """
        if self.fixture_format:
            return f"{FIXTURES_IMAGE}/{self.fixture_format}"
        return TESTS_IMAGE


IMAGES: tuple[Image, ...] = (
    Image("consume-rlp", "hive", "blockchain_tests"),
    Image("consume-engine", "hive", "blockchain_tests_engine"),
    Image("consume-enginex", "hive", "blockchain_tests_engine_x"),
    Image("consume-wirex", "hive", "blockchain_tests_engine_x"),
    Image("consume-sync", "hive", "blockchain_tests_sync"),
    Image("execute-blobs", "hive", tests=True),
)
"""Every published image; adding one here adds it to the publishing plan."""


def fixture_formats() -> list[str]:
    """Return the fixture formats some image carries, sorted."""
    return sorted({i.fixture_format for i in IMAGES if i.fixture_format})


def check_tag(tag: str) -> str:
    """Return `tag` if docker accepts it as an image tag, else raise."""
    if not TAG_RE.match(tag):
        raise ValueError(f"{tag!r} is not a valid docker image tag")
    return tag


def branch_tag(branch: str) -> str:
    """
    Return the image tag naming a branch on the repository image.

    `devnets/glamsterdam/8` becomes `glamsterdam-devnet-8`, the name the
    ecosystem uses for the devnet; any other branch has `/` replaced by `-`.
    Raise if the result is not a valid docker tag, as for a branch name with
    characters outside ASCII.
    """
    match = DEVNET_BRANCH_RE.match(branch)
    if match:
        name, number = match.groups()
        return check_tag(f"{name}{DEVNET_SUFFIX}-{number}")
    return check_tag(branch.replace("/", "-"))


def release_series(tag: str) -> str:
    """Return the series of a release tag, the part before the `@`."""
    return tag.partition("@")[0]


def series_name(series: str) -> str:
    """Return the friendly series name, `tests-x-devnet` as `x-devnet`."""
    return series.removeprefix(SERIES_PREFIX)


def release_slug(tag: str) -> str:
    """
    Return the image tag naming a release exactly.

    `tests@v20.0.2` gives `v20.0.2`; `tests-glamsterdam-devnet@v8.1.4` gives
    `glamsterdam-devnet-v8.1.4`. These are EEST's friendly release names with
    `@`, which docker tags forbid, replaced by `-`.
    """
    series, _, version = tag.partition("@")
    if series == MAIN_LINE_SERIES:
        return version
    return f"{series_name(series)}-{version}"


def branch_for_release(tag: str, default_branch: str) -> str | None:
    """
    Return the branch a release was cut from, or None if the series has none.

    The main line releases from the default branch. A devnet series
    `tests-<name>-devnet` releases `v<n>.Y.Z` from `devnets/<name>/<n>`.
    Other series, such as benchmark releases, are not tied to a branch.
    """
    series, _, version = tag.partition("@")
    if series == MAIN_LINE_SERIES:
        return default_branch
    name = series_name(series)
    parsed = Version.parse(version)
    if name.endswith(DEVNET_SUFFIX) and parsed is not None:
        return f"devnets/{name.removesuffix(DEVNET_SUFFIX)}/{parsed.major}"
    return None


def branch_channel(branch: str, default_branch: str) -> str | None:
    """
    Return the channel tag of a branch on the test-carrying images.

    `latest` for the default branch and `<name>-devnet-<n>` for a devnet
    branch: the branch's highest release with the branch's head. It is to
    the branch what `latest` is to the default branch. None for any other
    branch, which publishes no test-carrying image.
    """
    if branch == default_branch:
        return LATEST
    if DEVNET_BRANCH_RE.match(branch):
        return branch_tag(branch)
    return None


@dataclass(frozen=True, order=True)
class Version:
    """A release version `vX.Y.Z`, optionally with a pre-release suffix."""

    major: int
    minor: int
    patch: int
    final: bool
    """False for a pre-release suffix; a final release orders above it."""
    pre: str = ""

    @classmethod
    def parse(cls, version: str) -> "Version | None":
        """Parse `vX.Y.Z` or `vX.Y.Z-<suffix>`; return None for other forms."""
        match = VERSION_RE.match(version)
        if match is None:
            return None
        major, minor, patch, pre = match.groups()
        return cls(int(major), int(minor), int(patch), pre is None, pre or "")


@dataclass(frozen=True)
class Release:
    """A GitHub release, reduced to what the image names need."""

    tag: str
    draft: bool = False
    prerelease: bool = False
    commit: str | None = None
    """Commit the release was built from, when known."""
    assets: dict[str, str] = field(default_factory=dict)
    """Asset name to download URL."""

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "Release":
        """
        Build a release from a release object of the GitHub REST API.

        `target_commitish` may be a branch name rather than a commit, so
        the commit is left for the publisher to resolve from the tag.
        """
        return cls(
            tag=data["tag_name"],
            draft=bool(data.get("draft", False)),
            prerelease=bool(data.get("prerelease", False)),
            assets={
                asset["name"]: asset["browser_download_url"]
                for asset in data.get("assets", [])
            },
        )

    @property
    def series(self) -> str:
        """Return the release series."""
        return release_series(self.tag)

    @property
    def slug(self) -> str:
        """Return the image tag naming this release exactly."""
        return release_slug(self.tag)

    @property
    def version(self) -> Version | None:
        """Return the parsed version, or None if it is not `vX.Y.Z`."""
        return Version.parse(self.tag.partition("@")[2])

    @property
    def fixtures_url(self) -> str | None:
        """Return the download URL of the fixtures tarball, if any."""
        for name, url in self.assets.items():
            if FIXTURES_ASSET_RE.match(name):
                return url
        return None

    @property
    def eligible(self) -> bool:
        """
        Return whether the release can carry or move tags.

        What EEST's release resolver accepts: published, not a draft, a
        `vX.Y.Z` version and a fixtures tarball. The GitHub pre-release
        flag does not matter, as it does not to `consume --input`.
        """
        return (
            not self.draft
            and self.version is not None
            and self.fixtures_url is not None
        )


def _github_headers(token: str | None) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    token = (
        token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    )
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_releases(
    repository: str = DEFAULT_REPOSITORY,
    token: str | None = None,
    pages: int = 2,
) -> list[Release]:
    """
    Fetch the most recent releases of a repository from GitHub, newest first.

    Follow the pagination for up to `pages` pages of 100 releases.
    Authenticate with `token`, or with `GITHUB_TOKEN` or `GH_TOKEN` from the
    environment when set.
    """
    headers = _github_headers(token)
    url: str | None = (
        f"https://api.github.com/repos/{repository}/releases?per_page=100"
    )
    releases: list[Release] = []
    while url and pages > 0:
        pages -= 1
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        releases.extend(Release.from_api(data) for data in response.json())
        url = response.links.get("next", {}).get("url")
    return releases


def fetch_release(
    repository: str, tag: str, token: str | None = None
) -> Release | None:
    """Fetch one release by tag; None if the repository has no such release."""
    response = requests.get(
        f"https://api.github.com/repos/{repository}/releases/tags/{tag}",
        headers=_github_headers(token),
        timeout=30,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return Release.from_api(response.json())


def fetch_feature_config(
    repository: str, ref: str, token: str | None = None
) -> dict[str, Any] | None:
    """
    Fetch the release workflow's feature config at a ref of a repository.

    Read it at the release tag or fill commit, not at a branch head: a
    devnet branch fills its own forks. Return None if the ref has no config.
    """
    headers = _github_headers(token)
    headers["Accept"] = "application/vnd.github.raw"
    response = requests.get(
        f"https://api.github.com/repos/{repository}/contents/{FEATURE_CONFIG}",
        params={"ref": ref},
        headers=headers,
        timeout=30,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()
    config = yaml.safe_load(response.text)
    return config if isinstance(config, dict) else None


def fill_fork(config: dict[str, Any], series: str) -> str | None:
    """
    Return the newest fork a release series is filled for, from its config.

    The series' feature is `tests` for the main line and `<name>-devnet`
    for a devnet, which uses the shared `devnet` entry when there is one,
    as in the release workflow's `generate_build_matrix.py`. Its
    `fill-params` name the fork with `--fork`, or the newest one with
    `--until`. None if the config does not say.
    """
    name = series_name(series)
    if name.endswith(DEVNET_SUFFIX) and SHARED_DEVNET_FEATURE in config:
        name = SHARED_DEVNET_FEATURE
    entry = config.get(name)
    if not isinstance(entry, dict):
        return None
    params = str(entry.get("fill-params", ""))
    match = re.search(r"--fork[=\s]+(\S+)", params) or re.search(
        r"--until[=\s]+(\S+)", params
    )
    return match.group(1) if match else None


def git_tag_commit(repository: str, tag: str) -> str | None:
    """
    Resolve a tag of a GitHub repository to its commit with `git ls-remote`.

    The releases API reports `target_commitish`, which may be a branch name;
    the tag itself is authoritative. An annotated tag is peeled.
    """
    url = f"https://github.com/{repository}.git"
    ref = f"refs/tags/{tag}"
    result = subprocess.run(
        ["git", "ls-remote", "--tags", url, ref, f"{ref}^{{}}"],
        capture_output=True,
        text=True,
        check=True,
    )
    commits: dict[str, str] = {}
    for line in result.stdout.splitlines():
        sha, _, name = line.partition("\t")
        commits[name] = sha
    return commits.get(f"{ref}^{{}}") or commits.get(ref)


def is_release_of(
    branch: str, default_branch: str
) -> Callable[[Release], bool]:
    """
    Return the predicate selecting the eligible releases cut from a branch.

    The default branch owns the main line, `tests@vX.Y.Z`; no other
    `forks/` branch does. A devnet branch `devnets/<name>/<n>` owns
    `tests-<name>-devnet@v<n>.Y.Z`. Any other branch owns nothing.
    """
    if branch == default_branch:
        return lambda r: r.eligible and r.series == MAIN_LINE_SERIES
    match = DEVNET_BRANCH_RE.match(branch)
    if match:
        name, number = match.groups()
        pattern = re.compile(
            rf"^{re.escape(SERIES_PREFIX + name + DEVNET_SUFFIX)}"
            rf"@v{re.escape(number)}\."
        )
        return lambda r: r.eligible and bool(pattern.match(r.tag))
    return lambda _: False


def releases_for_branch(
    releases: Iterable[Release], branch: str, default_branch: str
) -> list[Release]:
    """Return the eligible releases of a branch, highest version first."""
    selected_by = is_release_of(branch, default_branch)
    selected = [r for r in releases if selected_by(r)]
    return sorted(
        selected,
        key=lambda r: r.version or Version(0, 0, 0, False),
        reverse=True,
    )


def channel_owner(
    releases: Iterable[Release], branch: str, default_branch: str
) -> Release | None:
    """Return the release behind a branch's channel: its highest release."""
    selected = releases_for_branch(releases, branch, default_branch)
    return selected[0] if selected else None


def release_tags(
    release: Release, releases: Iterable[Release], default_branch: str
) -> list[str]:
    """
    Return the simulator image tags a release run publishes for a release.

    First the immutable tag naming the release exactly, then its branch's
    channel (`latest`, `<name>-devnet-<n>`) when it is the highest release
    of the branch. Channels follow the highest version, never the newest
    publication. An ineligible release holds nothing but its own tag.
    """
    tags = [release.slug]
    if not release.eligible or release.version is None:
        return tags
    peers = [r for r in releases if r.tag != release.tag]
    peers.append(release)
    branch = branch_for_release(release.tag, default_branch)
    if branch is not None:
        owner = channel_owner(peers, branch, default_branch)
        channel = branch_channel(branch, default_branch)
        if owner is release and channel and channel not in tags:
            tags.append(channel)
    return tags


def base_tags(short_sha: str) -> list[str]:
    """
    Return the tags of the repository image for a commit: `sha-<7>`.

    The repository image is the base of the simulator images, which a run
    references by this tag; it carries no channel tags.
    """
    return [f"sha-{short_sha}"]


def nightly_release(short_sha: str) -> str:
    """
    Return the name a nightly fill reports as its release.

    `nightly-<7>`, by the commit it built. It appears in the image labels
    and the simulator log header; the images are tagged `nightly` only.
    """
    return f"{NIGHTLY}-{short_sha}"


def legacy_variant(tags: list[str]) -> dict[str, str] | None:
    """
    Return the deprecated build arguments variant published beside `latest`.

    hive's default eels Dockerfiles select `latest-legacy` when a caller
    passes the deprecated `fixtures` or `branch` arguments without a `tag`.
    It is `latest` with ONBUILD steps that apply them, so it moves with
    `latest`; other tags have no variant. Removing it ends the deprecation
    window (ethereum/execution-specs#3866).
    """
    if LATEST not in tags:
        return None
    return {"from": LATEST, "tag": f"{LATEST}{LEGACY_SUFFIX}"}


def registry_repository(repository: str) -> str:
    """Return the registry path of a repository: `ghcr.io/<owner>/<name>`."""
    return f"{REGISTRY}/{repository.lower()}"


def plan(
    *,
    branch: str | None,
    sha: str,
    default_branch: str,
    repository: str = DEFAULT_REPOSITORY,
    release_repository: str | None = None,
    release_tag: str | None = None,
    nightly: bool = False,
    releases: Iterable[Release] | None = None,
    resolve_commit: Callable[[str], str | None] | None = None,
    feature_config: (
        Callable[[str, str], dict[str, Any] | None] | None
    ) = None,
) -> dict[str, Any]:
    """
    Return what a publishing run builds and how it tags it.

    Three modes. A push (`branch` and `sha`, nothing else): the repository
    image of the head and the simulator images of the branch's channel
    owner, its highest release, under the channel tag only, so that the
    channel follows the head. A release (`release_tag`): the fixture images,
    the tests image and the simulator images of that release, paired with
    the head `sha` of the branch it was cut from, which is inferred from the
    tag and must agree with `branch` when given. A nightly (`nightly`, `sha`
    the fill commit): every image at that commit under `nightly`.

    Each entry names its `immutable` tag: the release tag in a release run,
    which the publisher must not overwrite once it exists, else empty.

    `release_repository` names the repository holding the releases when it
    differs from the publishing one, as on a fork; `releases` replaces the
    GitHub lookup, for tests. `resolve_commit` maps a release tag to its
    commit when the listing does not know it, `git_tag_commit` in the
    publisher.

    `feature_config` maps a repository and a ref to the feature config at
    that ref, `fetch_feature_config` in the publisher. It gives each execute
    image its `default_fork`, the fork the release or fill was filled for;
    without it, or when the config does not say, `default_fork` is empty and
    the image's check fails unless a fork is given.
    """
    registry = registry_repository(repository)
    release_repository = release_repository or repository
    short_sha = sha[:7]
    fixtures: dict[str, Any] | None = None
    tests: dict[str, Any] | None = None
    images: list[dict[str, Any]] = []

    def default_fork_of(repo: str, ref: str, series: str) -> str:
        if feature_config is None:
            return ""
        config = feature_config(repo, ref)
        return (fill_fork(config, series) or "") if config else ""

    def commit_of(release: Release) -> str:
        if release.commit:
            return release.commit
        if resolve_commit is not None:
            return resolve_commit(release.tag) or ""
        return ""

    def image_entries(
        release: str,
        slug: str,
        commit: str,
        tags: list[str],
        immutable: str = "",
        default_fork: str = "",
    ) -> list[dict[str, Any]]:
        return [
            {
                "name": image.name,
                "family": image.family,
                "kind": image.kind,
                "image": f"{registry}/{image.path}",
                "requires": f"{registry}/{image.content_path}:{slug}",
                "release": release,
                "slug": slug,
                "commit": commit,
                "tags": list(tags),
                "immutable": immutable,
                "default_fork": default_fork if image.tests else "",
                "legacy": legacy_variant(tags),
            }
            for image in IMAGES
        ]

    if nightly:
        if release_tag is not None:
            raise ValueError("a nightly run cannot also be a release run")
        if branch not in (None, default_branch):
            raise ValueError(
                f"the nightly fills the default branch, not {branch!r}"
            )
        mode = "nightly"
        branch = default_branch
        release_name = nightly_release(short_sha)
        slug = NIGHTLY
        tags = [NIGHTLY]
        fixtures = {
            "release": release_name,
            "slug": slug,
            "commit": sha,
            "url": None,
            "artifact": f"fixtures_{short_sha}",
            "image": f"{registry}/{FIXTURES_IMAGE}",
            "formats": fixture_formats(),
            "tags": list(tags),
            "immutable": "",
        }
        tests = {
            "release": release_name,
            "slug": slug,
            "commit": sha,
            "image": f"{registry}/{TESTS_IMAGE}",
            "tags": list(tags),
            "immutable": "",
        }
        images = image_entries(
            release_name,
            slug,
            sha,
            tags,
            default_fork=default_fork_of(repository, sha, MAIN_LINE_SERIES),
        )
        base = base_tags(short_sha)
    else:
        if releases is None:
            releases = fetch_releases(release_repository)
        releases = list(releases)
        if release_tag is not None:
            mode = "release"
            release = next(
                (r for r in releases if r.tag == release_tag), None
            ) or fetch_release(release_repository, release_tag)
            if release is None:
                raise ValueError(
                    f"release {release_tag!r} not found in "
                    f"{release_repository}"
                )
            if release.draft:
                raise ValueError(f"release {release_tag!r} is a draft")
            if release.version is None:
                raise ValueError(
                    f"release {release_tag!r} has no vX.Y.Z version"
                )
            if release.fixtures_url is None:
                raise ValueError(
                    f"release {release_tag!r} has no fixtures tarball"
                )
            cut_from = branch_for_release(release.tag, default_branch)
            if cut_from is None:
                raise ValueError(
                    f"release {release_tag!r} is not tied to a branch"
                )
            if branch is not None and branch != cut_from:
                raise ValueError(
                    f"release {release_tag!r} was cut from {cut_from}, "
                    f"not {branch}"
                )
            branch = cut_from
            if release not in releases:
                releases.append(release)
            tags = release_tags(release, releases, default_branch)
            commit = commit_of(release)
            fixtures = {
                "release": release.tag,
                "slug": release.slug,
                "commit": commit,
                "url": release.fixtures_url,
                "artifact": None,
                "image": f"{registry}/{FIXTURES_IMAGE}",
                "formats": fixture_formats(),
                "tags": [release.slug],
                "immutable": release.slug,
            }
            tests = {
                "release": release.tag,
                "slug": release.slug,
                "commit": commit,
                "image": f"{registry}/{TESTS_IMAGE}",
                "tags": [release.slug],
                "immutable": release.slug,
            }
            images = image_entries(
                release.tag,
                release.slug,
                commit,
                tags,
                release.slug,
                default_fork_of(
                    release_repository, release.tag, release.series
                ),
            )
        else:
            mode = "push"
            if branch is None:
                raise ValueError("a push run needs the branch")
            owner = channel_owner(releases, branch, default_branch)
            channel = branch_channel(branch, default_branch)
            if owner is not None and channel is not None:
                # Only the channel moves; the release tag stays as the
                # release run built it.
                tags = [channel]
                images = image_entries(
                    owner.tag,
                    owner.slug,
                    commit_of(owner),
                    tags,
                    default_fork=default_fork_of(
                        release_repository, owner.tag, owner.series
                    ),
                )
        base = base_tags(short_sha)

    return {
        "mode": mode,
        "repository": registry,
        "release_repository": release_repository,
        "branch": branch,
        "channel": branch_channel(branch, default_branch),
        "default_branch": default_branch,
        "is_default": branch == default_branch,
        "sha": sha,
        "short_sha": short_sha,
        "base": {
            "image": registry,
            "ref": f"{registry}:sha-{short_sha}",
            "tags": base,
        },
        "fixtures": fixtures,
        "tests": tests,
        "images": images,
    }
