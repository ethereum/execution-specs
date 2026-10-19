"""Tests for the names and build plans of the hive simulator docker images."""

import pytest

from execution_testing.tools import docker_images
from execution_testing.tools.docker_images import (
    IMAGES,
    Release,
    Version,
    base_tags,
    branch_channel,
    branch_for_release,
    branch_tag,
    channel_owner,
    fill_fork,
    fixture_formats,
    nightly_release,
    plan,
    release_series,
    release_slug,
    release_tags,
    releases_for_branch,
)

DEFAULT_BRANCH = "forks/amsterdam"
MAINNET_ASSET = {"fixtures.tar.gz": "u/tests"}
GLAM_ASSET = {"fixtures_glamsterdam-devnet.tar.gz": "u/glamsterdam"}
# Newest publication first, as the GitHub API lists them. Two patches on
# the 19.1 line were published after 20.0.2.
RELEASES = [
    Release("tests@v19.1.2", assets=MAINNET_ASSET),
    Release("tests@v19.1.1", assets=MAINNET_ASSET),
    Release(
        "tests-glamsterdam-devnet@v8.1.4", prerelease=True, assets=GLAM_ASSET
    ),
    Release("tests@v0.0.916", draft=True, assets=MAINNET_ASSET),
    Release("tests@v20.0.2", commit="c20002", assets=MAINNET_ASSET),
    Release(
        "tests-glamsterdam-devnet@v8.1.3", prerelease=True, assets=GLAM_ASSET
    ),
    Release("tests@v20.0.1", assets=MAINNET_ASSET),
    Release(
        "tests-zkevm@v0.8.4",
        prerelease=True,
        assets={"fixtures_zkevm.tar.gz": "u"},
    ),
    Release(
        "tests-glamsterdam-devnet@v7.2.1", prerelease=True, assets=GLAM_ASSET
    ),
    Release("tests@v20.0.0", assets=MAINNET_ASSET),
]


def release(tag: str) -> Release:
    """Return the sample release with the given tag."""
    return next(r for r in RELEASES if r.tag == tag)


@pytest.mark.parametrize(
    "branch,expected",
    [
        ("devnets/glamsterdam/8", "glamsterdam-devnet-8"),
        ("devnets/focil/0", "focil-devnet-0"),
        ("forks/amsterdam", "forks-amsterdam"),
        ("feature/x", "feature-x"),
    ],
)
def test_branch_tag(branch: str, expected: str) -> None:
    """Branches map to the tag names the ecosystem uses."""
    assert branch_tag(branch) == expected


def test_branch_tag_rejects_invalid_docker_tags() -> None:
    """A branch name docker cannot tag fails loudly instead of at push time."""
    with pytest.raises(ValueError):
        branch_tag("devnets/snøbal/4")


def test_release_names() -> None:
    """Release slugs are EEST's friendly names with `@` replaced by `-`."""
    assert release_slug("tests@v20.0.2") == "v20.0.2"
    assert (
        release_slug("tests-glamsterdam-devnet@v8.1.4")
        == "glamsterdam-devnet-v8.1.4"
    )
    assert release_series("tests-glamsterdam-devnet@v8.1.4") == (
        "tests-glamsterdam-devnet"
    )


def test_branches_and_channels() -> None:
    """A release maps to its branch and a branch to its channel tag."""
    assert (
        branch_for_release("tests@v20.0.2", DEFAULT_BRANCH) == DEFAULT_BRANCH
    )
    assert (
        branch_for_release("tests-glamsterdam-devnet@v8.1.4", DEFAULT_BRANCH)
        == "devnets/glamsterdam/8"
    )
    assert branch_for_release("tests-zkevm@v0.8.4", DEFAULT_BRANCH) is None
    assert branch_channel(DEFAULT_BRANCH, DEFAULT_BRANCH) == "latest"
    assert (
        branch_channel("devnets/glamsterdam/8", DEFAULT_BRANCH)
        == "glamsterdam-devnet-8"
    )
    assert branch_channel("forks/osaka", DEFAULT_BRANCH) is None
    assert branch_channel("feature/x", DEFAULT_BRANCH) is None


def test_version_ordering() -> None:
    """Versions order numerically, and a final release above its candidates."""
    assert Version.parse("v8.1.4") == Version(8, 1, 4, True)
    assert Version.parse("v21.0.0-rc1") == Version(21, 0, 0, False, "rc1")
    assert Version.parse("main") is None
    v = Version.parse
    assert v("v8.1.4") > v("v8.1.3") > v("v8.0.9") > v("v7.9.9")  # type: ignore[operator]
    assert v("v21.0.0") > v("v21.0.0-rc1") > v("v20.0.2")  # type: ignore[operator]


def test_eligibility() -> None:
    """Eligible is what EEST resolves: published, versioned, with a tarball."""
    assert release("tests@v20.0.2").eligible
    assert release("tests-glamsterdam-devnet@v8.1.4").eligible, (
        "prerelease flag is ignored"
    )
    assert not release("tests@v0.0.916").eligible, "draft"
    assert not Release("tests@v21.0.0", assets={"checksums.txt": "u"}).eligible
    assert not Release("tests@main", assets=MAINNET_ASSET).eligible


def test_releases_for_branch() -> None:
    """Branches own their releases in version order; others own none."""
    tags = [
        r.tag
        for r in releases_for_branch(RELEASES, DEFAULT_BRANCH, DEFAULT_BRANCH)
    ]
    assert tags == [
        "tests@v20.0.2",
        "tests@v20.0.1",
        "tests@v20.0.0",
        "tests@v19.1.2",
        "tests@v19.1.1",
    ]
    assert channel_owner(RELEASES, DEFAULT_BRANCH, DEFAULT_BRANCH) is release(
        "tests@v20.0.2"
    )
    tags = [
        r.tag
        for r in releases_for_branch(
            RELEASES, "devnets/glamsterdam/8", DEFAULT_BRANCH
        )
    ]
    assert tags == [
        "tests-glamsterdam-devnet@v8.1.4",
        "tests-glamsterdam-devnet@v8.1.3",
    ]
    # Only the default branch owns the main line.
    assert releases_for_branch(RELEASES, "forks/osaka", DEFAULT_BRANCH) == []
    assert (
        releases_for_branch(RELEASES, "devnets/glamsterdam/9", DEFAULT_BRANCH)
        == []
    )
    assert releases_for_branch(RELEASES, "feature/x", DEFAULT_BRANCH) == []


def test_release_tags_main_line() -> None:
    """The highest main-line release holds `latest`; others only their tag."""
    assert release_tags(
        release("tests@v20.0.2"), RELEASES, DEFAULT_BRANCH
    ) == [
        "v20.0.2",
        "latest",
    ]
    assert release_tags(
        release("tests@v20.0.1"), RELEASES, DEFAULT_BRANCH
    ) == ["v20.0.1"]
    assert release_tags(
        release("tests@v19.1.2"), RELEASES, DEFAULT_BRANCH
    ) == ["v19.1.2"]
    assert release_tags(
        release("tests@v0.0.916"), RELEASES, DEFAULT_BRANCH
    ) == ["v0.0.916"]
    # As for `consume --input tests@latest`, the pre-release flag is ignored.
    flagged = Release("tests@v20.0.3", prerelease=True, assets=MAINNET_ASSET)
    assert release_tags(flagged, [*RELEASES, flagged], DEFAULT_BRANCH) == [
        "v20.0.3",
        "latest",
    ]
    # Without a tarball EEST would not resolve it, so it holds nothing.
    bare = Release("tests@v20.0.4")
    assert release_tags(bare, [*RELEASES, bare], DEFAULT_BRANCH) == ["v20.0.4"]


def test_release_tags_devnet() -> None:
    """A devnet release holds its branch channel while it is the highest."""
    assert release_tags(
        release("tests-glamsterdam-devnet@v8.1.4"), RELEASES, DEFAULT_BRANCH
    ) == [
        "glamsterdam-devnet-v8.1.4",
        "glamsterdam-devnet-8",
    ]
    assert release_tags(
        release("tests-glamsterdam-devnet@v8.1.3"), RELEASES, DEFAULT_BRANCH
    ) == ["glamsterdam-devnet-v8.1.3"]
    assert release_tags(
        release("tests-glamsterdam-devnet@v7.2.1"), RELEASES, DEFAULT_BRANCH
    ) == ["glamsterdam-devnet-v7.2.1", "glamsterdam-devnet-7"]
    # A newer devnet has its own channel; devnet 8 keeps its own.
    nine = Release(
        "tests-glamsterdam-devnet@v9.0.0", prerelease=True, assets=GLAM_ASSET
    )
    assert release_tags(
        release("tests-glamsterdam-devnet@v8.1.4"),
        [*RELEASES, nine],
        DEFAULT_BRANCH,
    ) == ["glamsterdam-devnet-v8.1.4", "glamsterdam-devnet-8"]
    assert release_tags(nine, [*RELEASES, nine], DEFAULT_BRANCH) == [
        "glamsterdam-devnet-v9.0.0",
        "glamsterdam-devnet-9",
    ]
    # A late patch on devnet 8 moves only devnet 8's channel.
    patch = Release(
        "tests-glamsterdam-devnet@v8.1.5", prerelease=True, assets=GLAM_ASSET
    )
    assert release_tags(patch, [*RELEASES, nine, patch], DEFAULT_BRANCH) == [
        "glamsterdam-devnet-v8.1.5",
        "glamsterdam-devnet-8",
    ]


def test_base_tags() -> None:
    """The repository image is tagged by commit only."""
    assert base_tags("abc1234") == ["sha-abc1234"]
    # A nightly is reported by its commit but tagged `nightly` only.
    assert nightly_release("1a2b3c4") == "nightly-1a2b3c4"


def test_catalogue() -> None:
    """Every image is a consume or an execute simulator with a family."""
    assert {image.kind for image in IMAGES} == {"consume", "execute"}
    assert all(image.family for image in IMAGES)
    assert fixture_formats() == [
        "blockchain_tests",
        "blockchain_tests_engine",
        "blockchain_tests_engine_x",
        "blockchain_tests_sync",
    ]


def test_plan_for_a_push() -> None:
    """A push rebuilds only the branch's channel owner with the new head."""
    result = plan(
        branch="devnets/glamsterdam/8",
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        repository="Ethereum/Execution-Specs",
        releases=RELEASES,
    )
    assert result["mode"] == "push"
    assert result["repository"] == "ghcr.io/ethereum/execution-specs"
    assert result["channel"] == "glamsterdam-devnet-8"
    assert result["fixtures"] is None and result["tests"] is None
    assert result["base"]["tags"] == ["sha-abc1234"]
    images = result["images"]
    assert len(images) == len(IMAGES)
    newest = images[0]
    assert (
        newest["image"] == "ghcr.io/ethereum/execution-specs/hive/consume-rlp"
    )
    assert newest["kind"] == "consume"
    assert newest["requires"] == (
        "ghcr.io/ethereum/execution-specs/fixtures/blockchain_tests"
        ":glamsterdam-devnet-v8.1.4"
    )
    assert newest["release"] == "tests-glamsterdam-devnet@v8.1.4"
    assert newest["slug"] == "glamsterdam-devnet-v8.1.4"
    # Only the channel moves; the release tag stays as the release built it.
    assert newest["tags"] == ["glamsterdam-devnet-8"]
    assert newest["immutable"] == ""
    blobs = images[-1]
    assert blobs["name"] == "execute-blobs" and blobs["kind"] == "execute"
    assert blobs["requires"] == (
        "ghcr.io/ethereum/execution-specs/tests:glamsterdam-devnet-v8.1.4"
    )
    assert blobs["tags"] == newest["tags"]

    # The main line: the channel owner by version, not the newest publication.
    result = plan(
        branch=DEFAULT_BRANCH,
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        releases=RELEASES,
    )
    assert result["base"]["tags"] == ["sha-abc1234"]
    assert {i["release"] for i in result["images"]} == {"tests@v20.0.2"}
    assert result["images"][0]["tags"] == ["latest"]

    # A branch without releases, or without a line, publishes only its code.
    result = plan(
        branch="devnets/glamsterdam/9",
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        releases=RELEASES,
    )
    assert result["images"] == [] and result["base"]["tags"] == ["sha-abc1234"]
    result = plan(
        branch="forks/osaka",
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        releases=RELEASES,
    )
    assert result["images"] == [] and result["base"]["tags"] == ["sha-abc1234"]


def test_plan_for_a_release() -> None:
    """A release plans its fixture and tests images and its simulators only."""
    result = plan(
        branch=None,
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        release_tag="tests@v20.0.2",
        releases=RELEASES,
    )
    assert result["mode"] == "release"
    assert result["branch"] == DEFAULT_BRANCH, "inferred from the series"
    assert result["fixtures"] == {
        "release": "tests@v20.0.2",
        "slug": "v20.0.2",
        "commit": "c20002",
        "url": "u/tests",
        "artifact": None,
        "image": "ghcr.io/ethereum/execution-specs/fixtures",
        "formats": fixture_formats(),
        "tags": ["v20.0.2"],
        "immutable": "v20.0.2",
    }
    assert result["tests"] == {
        "release": "tests@v20.0.2",
        "slug": "v20.0.2",
        "commit": "c20002",
        "image": "ghcr.io/ethereum/execution-specs/tests",
        "tags": ["v20.0.2"],
        "immutable": "v20.0.2",
    }
    assert [image["release"] for image in result["images"]] == [
        "tests@v20.0.2"
    ] * len(IMAGES)
    assert result["images"][0]["tags"] == ["v20.0.2", "latest"]
    assert result["images"][0]["immutable"] == "v20.0.2"

    # An older release moves nothing.
    older = plan(
        branch=None,
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        release_tag="tests@v20.0.1",
        releases=RELEASES,
    )
    assert older["images"][0]["tags"] == ["v20.0.1"]

    # A devnet release is paired with its own branch, whatever the caller says.
    devnet = plan(
        branch=None,
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        release_tag="tests-glamsterdam-devnet@v8.1.4",
        releases=RELEASES,
    )
    assert devnet["branch"] == "devnets/glamsterdam/8"
    assert devnet["base"]["tags"] == ["sha-abc1234"]
    assert devnet["images"][0]["tags"] == [
        "glamsterdam-devnet-v8.1.4",
        "glamsterdam-devnet-8",
    ]
    with pytest.raises(ValueError, match="cut from devnets/glamsterdam/8"):
        plan(
            branch=DEFAULT_BRANCH,
            sha="abc1234def",
            default_branch=DEFAULT_BRANCH,
            release_tag="tests-glamsterdam-devnet@v8.1.4",
            releases=RELEASES,
        )
    with pytest.raises(ValueError, match="cut from forks/amsterdam"):
        plan(
            branch="devnets/glamsterdam/8",
            sha="abc1234def",
            default_branch=DEFAULT_BRANCH,
            release_tag="tests@v20.0.2",
            releases=RELEASES,
        )
    with pytest.raises(ValueError, match="draft"):
        plan(
            branch=None,
            sha="abc1234def",
            default_branch=DEFAULT_BRANCH,
            release_tag="tests@v0.0.916",
            releases=RELEASES,
        )
    with pytest.raises(ValueError, match="not tied to a branch"):
        plan(
            branch=None,
            sha="abc1234def",
            default_branch=DEFAULT_BRANCH,
            release_tag="tests-zkevm@v0.8.4",
            releases=RELEASES,
        )


def test_plan_resolves_release_commits() -> None:
    """The release commit is resolved from the tag when not listed."""
    result = plan(
        branch=DEFAULT_BRANCH,
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        releases=RELEASES,
        resolve_commit=lambda tag: {"tests@v20.0.2": "c20002full"}.get(tag),
    )
    assert result["images"][0]["commit"] == "c20002", "a known commit is kept"
    unknown = [Release("tests@v20.0.3", assets=MAINNET_ASSET)]
    result = plan(
        branch=DEFAULT_BRANCH,
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        releases=unknown,
        resolve_commit=lambda tag: "c20003"
        if tag == "tests@v20.0.3"
        else None,
    )
    assert result["images"][0]["commit"] == "c20003"
    result = plan(
        branch=None,
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        release_tag="tests@v20.0.3",
        releases=unknown,
        resolve_commit=lambda _: "c20003",
    )
    assert (
        result["fixtures"]["commit"] == "c20003"
        and result["tests"]["commit"] == "c20003"
    )


def test_plan_fetches_a_release_missing_from_the_listing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A release outside the listed window is fetched by tag, or fails."""
    old = Release("tests@v18.0.0", assets=MAINNET_ASSET)
    monkeypatch.setattr(
        docker_images,
        "fetch_release",
        lambda _repo, tag, _token=None: old if tag == old.tag else None,
    )
    result = plan(
        branch=None,
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        release_tag="tests@v18.0.0",
        releases=RELEASES,
    )
    assert result["images"][0]["tags"] == ["v18.0.0"]
    with pytest.raises(ValueError, match="not found"):
        plan(
            branch=None,
            sha="abc1234def",
            default_branch=DEFAULT_BRANCH,
            release_tag="tests@v17.0.0",
            releases=RELEASES,
        )


def test_plan_for_a_nightly() -> None:
    """A nightly plans every image at the fill commit, tagged nightly."""
    result = plan(
        branch=None,
        sha="1a2b3c4d5e",
        default_branch=DEFAULT_BRANCH,
        nightly=True,
        releases=[],
    )
    assert result["mode"] == "nightly"
    assert result["branch"] == DEFAULT_BRANCH
    assert result["base"]["tags"] == ["sha-1a2b3c4"]
    assert result["fixtures"]["artifact"] == "fixtures_1a2b3c4"
    assert result["fixtures"]["url"] is None
    assert result["fixtures"]["release"] == "nightly-1a2b3c4"
    assert result["fixtures"]["tags"] == ["nightly"]
    assert result["tests"]["commit"] == "1a2b3c4d5e"
    assert result["tests"]["tags"] == ["nightly"]
    assert len(result["images"]) == len(IMAGES)
    # Reported by its commit, tagged and built from `nightly` only.
    assert result["images"][0]["release"] == "nightly-1a2b3c4"
    assert result["images"][0]["slug"] == "nightly"
    assert result["images"][0]["requires"].endswith(":nightly")
    assert result["images"][0]["commit"] == "1a2b3c4d5e"
    assert result["images"][0]["tags"] == ["nightly"]
    assert result["images"][0]["immutable"] == ""
    with pytest.raises(ValueError, match="default branch"):
        plan(
            branch="devnets/glamsterdam/8",
            sha="1a2b3c4d5e",
            default_branch=DEFAULT_BRANCH,
            nightly=True,
            releases=[],
        )
    with pytest.raises(ValueError, match="cannot also be a release"):
        plan(
            branch=None,
            sha="1a2b3c4d5e",
            default_branch=DEFAULT_BRANCH,
            nightly=True,
            release_tag="tests@v20.0.2",
            releases=RELEASES,
        )


# Feature configs as the release workflow reads them, by repository and ref.
MAIN_CONFIG = {
    "tests": {"fill-params": "--until=Amsterdam --generate-all-formats"},
    "devnet": {"fill-params": "--until=Amsterdam --generate-all-formats"},
    "benchmark": {"fill-params": "--fork=Amsterdam --gas-benchmark-values 1"},
}
DEVNET_CONFIG = {
    "tests": {"fill-params": "--until=Amsterdam --generate-all-formats"},
    "devnet": {"fill-params": "--until=Bogota --generate-all-formats"},
}


def test_fill_fork() -> None:
    """The fork comes from `--fork`, else `--until`, of the series' entry."""
    assert fill_fork(MAIN_CONFIG, "tests") == "Amsterdam"
    # Every devnet series shares the `devnet` entry, as in the release
    # workflow, and the entry differs per branch.
    assert fill_fork(DEVNET_CONFIG, "tests-bogota-devnet") == "Bogota"
    assert fill_fork(MAIN_CONFIG, "tests-bogota-devnet") == "Amsterdam"
    assert fill_fork(MAIN_CONFIG, "tests-benchmark") == "Amsterdam"
    assert fill_fork({"tests": {"fill-params": "-k foo"}}, "tests") is None
    assert fill_fork({}, "tests") is None
    assert fill_fork({}, "tests-glamsterdam-devnet") is None


def test_plan_default_fork() -> None:
    """Execute images default to the fork the content was filled for."""
    reads: list[tuple[str, str]] = []

    def config_at(repository: str, ref: str) -> dict | None:
        reads.append((repository, ref))
        if ref == "missing":
            return None
        return DEVNET_CONFIG if "devnet" in ref else MAIN_CONFIG

    release = plan(
        branch=None,
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        release_tag="tests-glamsterdam-devnet@v8.1.4",
        releases=RELEASES,
        feature_config=config_at,
    )
    by_name = {i["name"]: i for i in release["images"]}
    assert by_name["execute-blobs"]["default_fork"] == "Bogota"
    assert by_name["consume-engine"]["default_fork"] == ""
    # Read at the release tag, not at the branch head.
    assert reads[-1] == (
        "ethereum/execution-specs",
        "tests-glamsterdam-devnet@v8.1.4",
    )

    push = plan(
        branch=DEFAULT_BRANCH,
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        releases=RELEASES,
        feature_config=config_at,
    )
    assert push["images"][-1]["default_fork"] == "Amsterdam"
    assert reads[-1][1] == "tests@v20.0.2", "the channel owner's tag"

    nightly = plan(
        branch=None,
        sha="1a2b3c4d5e",
        default_branch=DEFAULT_BRANCH,
        nightly=True,
        releases=[],
        feature_config=config_at,
    )
    assert nightly["images"][-1]["default_fork"] == "Amsterdam"
    assert reads[-1][1] == "1a2b3c4d5e", "the fill commit"

    # Without a config, or without a lookup, the default is left empty and
    # the image check fails rather than guessing.
    unknown = plan(
        branch=None,
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        release_tag="tests@v20.0.2",
        releases=RELEASES,
        feature_config=lambda *_: None,
    )
    assert unknown["images"][-1]["default_fork"] == ""
    offline = plan(
        branch=None,
        sha="abc1234def",
        default_branch=DEFAULT_BRANCH,
        release_tag="tests@v20.0.2",
        releases=RELEASES,
    )
    assert offline["images"][-1]["default_fork"] == ""
