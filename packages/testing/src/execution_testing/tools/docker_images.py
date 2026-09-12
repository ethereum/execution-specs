"""
Names and build plans of the docker images for the hive simulators.

The repository publishes four kinds of images to ghcr.io, described in
`docs/running_tests/hive/images/`: the repository image
(`ghcr.io/ethereum/execution-specs`), one fixture image per fixture format
(`.../fixtures/<format>`), the tests image holding the test sources of a
release (`.../tests`), and one ready-to-run image per hive simulator
(`.../hive/<simulator>`).

Simulator tags select the tests. Current releases receive framework updates;
older releases retain their last build, and nightlies use the fill commit.
Release tags omit the mainnet `tests@` prefix or the devnet `tests-` prefix
and replace `@` with `-`; channel tags name the
current state of a line: `latest` for the default branch, `<name>-devnet-<n>`
for a devnet branch, `<name>-devnet-latest` for a devnet series, and `nightly`
for the nightly fill. This module holds the naming rules in one place and
computes what a publishing run has to build. The `eest images` command exposes
it to the publishing workflow, which consumes the plan as JSON.
"""

import os
import re
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any

import requests

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
FIXTURES_ASSET_RE = re.compile(r"^fixtures(_.*)?\.tar\.gz$")
VERSION_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:-(.+))?$")
TAG_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$")
"""What docker accepts as an image tag."""
DEVNET_BRANCH_RE = re.compile(r"^devnets/([^/]+)/(\d+)$")


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


IMAGES: tuple[Image, ...] = (
    Image("consume-rlp", "hive", "blockchain_tests"),
    Image("consume-engine", "hive", "blockchain_tests_engine"),
    Image("consume-enginex", "hive", "blockchain_tests_engine_x"),
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


def series_alias(series: str) -> str:
    """
    Return the channel tag following the highest release of a series.

    `latest` for the main line, `<name>-latest` otherwise: what
    `consume --input tests@latest` and `consume --input <name>@latest` resolve.
    """
    if series == MAIN_LINE_SERIES:
        return LATEST
    return f"{series_name(series)}-{LATEST}"


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
    Return the tags naming the test content of a release.

    First the tag naming the release exactly, then the channel tags the
    release holds: its branch's channel (`latest`, `<name>-devnet-<n>`)
    when it is the highest release of the branch, and its series' channel
    (`latest`, `<name>-devnet-latest`) when it is the highest release of the
    series. Channels follow the highest version, never the newest
    publication. An ineligible release holds nothing but its own tag.
    """
    tags = [release.slug]
    version = release.version
    if not release.eligible or version is None:
        return tags
    peers = [r for r in releases if r.tag != release.tag]
    peers.append(release)
    branch = branch_for_release(release.tag, default_branch)
    if branch is not None:
        owner = channel_owner(peers, branch, default_branch)
        channel = branch_channel(branch, default_branch)
        if owner is release and channel and channel not in tags:
            tags.append(channel)
    series_peers = [
        r.version
        for r in peers
        if r.eligible and r.series == release.series and r.version
    ]
    if version >= max(series_peers):
        alias = series_alias(release.series)
        if alias not in tags:
            tags.append(alias)
    return tags


def base_tags(short_sha: str, branch: str, default_branch: str) -> list[str]:
    """
    Return the tags of the repository image for a commit of a branch.

    Always the commit, `sha-<7>`; `latest` on the default branch and the
    branch tag on a devnet branch. The default branch has no branch-named
    tag, because it is renamed at every fork.
    """
    tags = [f"sha-{short_sha}"]
    if branch == default_branch:
        tags.append(LATEST)
    elif DEVNET_BRANCH_RE.match(branch):
        tags.append(branch_tag(branch))
    return tags


def nightly_slug(short_sha: str) -> str:
    """Return the tag naming a nightly fill exactly, by the commit it built."""
    return f"{NIGHTLY}-{short_sha}"


def nightly_tags(short_sha: str) -> list[str]:
    """Return the tags of a nightly fill: its own tag, then `nightly`."""
    return [nightly_slug(short_sha), NIGHTLY]


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
) -> dict[str, Any]:
    """
    Return what a publishing run builds and how it tags it.

    Three modes. A push (`branch` and `sha`, nothing else): the repository
    image of the head and the simulator images of the branch's channel
    owner, its highest release, so that the channel tag follows the head. A
    release (`release_tag`): the fixture images, the tests image and the
    simulator images of that release, paired with the head `sha` of the
    branch it was cut from, which is inferred from the tag and must agree
    with `branch` when given. A nightly (`nightly`, `sha` the fill commit):
    every image at that commit under the nightly tags.

    `release_repository` names the repository holding the releases when it
    differs from the publishing one, as on a fork; `releases` replaces the
    GitHub lookup, for tests. `resolve_commit` maps a release tag to its
    commit when the listing does not know it, `git_tag_commit` in the
    publisher.
    """
    registry = registry_repository(repository)
    release_repository = release_repository or repository
    short_sha = sha[:7]
    fixtures: dict[str, Any] | None = None
    tests: dict[str, Any] | None = None
    images: list[dict[str, Any]] = []

    def commit_of(release: Release) -> str:
        if release.commit:
            return release.commit
        if resolve_commit is not None:
            return resolve_commit(release.tag) or ""
        return ""

    def image_entries(
        release: str, slug: str, commit: str, tags: list[str]
    ) -> list[dict[str, Any]]:
        return [
            {
                "name": image.name,
                "family": image.family,
                "kind": image.kind,
                "image": f"{registry}/{image.path}",
                "release": release,
                "slug": slug,
                "commit": commit,
                "tags": list(tags),
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
        slug = nightly_slug(short_sha)
        tags = nightly_tags(short_sha)
        fixtures = {
            "release": slug,
            "slug": slug,
            "commit": sha,
            "url": None,
            "artifact": f"fixtures_{short_sha}",
            "image": f"{registry}/{FIXTURES_IMAGE}",
            "formats": fixture_formats(),
            "tags": list(tags),
        }
        tests = {
            "release": slug,
            "slug": slug,
            "commit": sha,
            "image": f"{registry}/{TESTS_IMAGE}",
            "tags": list(tags),
        }
        images = image_entries(slug, slug, sha, tags)
        base = [f"sha-{short_sha}", NIGHTLY]
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
                "tags": list(tags),
            }
            tests = {
                "release": release.tag,
                "slug": release.slug,
                "commit": commit,
                "image": f"{registry}/{TESTS_IMAGE}",
                "tags": list(tags),
            }
            images = image_entries(release.tag, release.slug, commit, tags)
        else:
            mode = "push"
            if branch is None:
                raise ValueError("a push run needs the branch")
            owner = channel_owner(releases, branch, default_branch)
            if owner is not None:
                tags = release_tags(owner, releases, default_branch)
                images = image_entries(
                    owner.tag, owner.slug, commit_of(owner), tags
                )
        base = base_tags(short_sha, branch, default_branch)

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
