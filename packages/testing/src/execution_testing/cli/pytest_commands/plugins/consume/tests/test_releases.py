"""Test release parsing given the github repository release JSON data."""

from os.path import realpath
from pathlib import Path
from typing import List

import pytest

from ..releases import (
    SUPPORTED_REPOS,
    NoSuchReleaseError,
    ReleaseInformation,
    get_release_url_from_release_information,
    is_release_url,
    parse_release_information_from_file,
)

CURRENT_FILE = Path(realpath(__file__))
CURRENT_FOLDER = CURRENT_FILE.parent


@pytest.fixture(scope="session")
def release_information() -> List[ReleaseInformation]:
    """Return the release information from a file."""
    return parse_release_information_from_file(
        CURRENT_FOLDER / "release_information.json"
    )


@pytest.mark.parametrize(
    "release_name,expected_release_download_url",
    [
        # The `tests` feature tags as `tests@vX.Y.Z` and ships a plain
        # `fixtures.tar.gz` asset.
        (
            "tests@v20.0.0",
            "tests%40v20.0.0/fixtures.tar.gz",
        ),
        (
            "tests@latest",
            "tests%40v20.0.0/fixtures.tar.gz",
        ),
        # A bare `latest` or `vX.Y.Z` resolves the mainnet `tests` release.
        (
            "latest",
            "tests%40v20.0.0/fixtures.tar.gz",
        ),
        (
            "v20.0.0",
            "tests%40v20.0.0/fixtures.tar.gz",
        ),
        # Other features tag as `tests-<feature>@vX.Y.Z`; both the friendly
        # feature name and the full tag are accepted.
        (
            "bal@v7.3.1",
            "tests-bal%40v7.3.1/fixtures_bal.tar.gz",
        ),
        (
            "tests-bal@v7.3.2",
            "tests-bal%40v7.3.2/fixtures_bal.tar.gz",
        ),
        (
            "bal@latest",
            "tests-bal%40v7.3.2/fixtures_bal.tar.gz",
        ),
        (
            "bal-devnet@v8.0.0",
            "tests-bal-devnet%40v8.0.0/fixtures_bal-devnet.tar.gz",
        ),
        (
            "benchmark@latest",
            "tests-benchmark%40v0.0.9/fixtures_benchmark.tar.gz",
        ),
        (
            "tests-benchmark@latest",
            "tests-benchmark%40v0.0.9/fixtures_benchmark.tar.gz",
        ),
        (
            "tests-glamsterdam-devnet@v6.1.0",
            "tests-glamsterdam-devnet%40v6.1.0/"
            "fixtures_glamsterdam-devnet.tar.gz",
        ),
        # `latest` resolves the highest version, not the most recently
        # published: v6.0.1 is published after v6.1.0 in the manifest but
        # must not win over the newer v6.1 line.
        (
            "glamsterdam-devnet@latest",
            "tests-glamsterdam-devnet%40v6.1.0/"
            "fixtures_glamsterdam-devnet.tar.gz",
        ),
    ],
)
def test_eels_release_parsing(
    release_name: str,
    expected_release_download_url: str,
    release_information: List[ReleaseInformation],
) -> None:
    """Test parsing of the `tests[-<feature>]@vX.Y.Z` tag scheme."""
    assert (
        "https://github.com/ethereum/execution-specs/releases/download/"
        + expected_release_download_url
    ) == get_release_url_from_release_information(
        release_name, release_information
    )


@pytest.mark.parametrize(
    "release_name",
    [
        # Legacy pre-`tests`-tag release names must no longer resolve.
        "stable@latest",
        "stable@v4.5.0",
        "develop@latest",
        # A bare `vX.Y.Z` is shorthand for `tests@vX.Y.Z` and must never
        # fall back to the spec-package release tagged plain `v2.20.0` in
        # the manifest, even though it is the most recently published
        # release and its version exists.
        "v2.20.0",
        "tests@v2.20.0",
    ],
)
def test_non_fixture_releases_do_not_resolve(
    release_name: str,
    release_information: List[ReleaseInformation],
) -> None:
    """
    Test that legacy and spec-package releases never resolve.

    The manifest contains a spec-package decoy tagged `v2.20.0` whose only
    asset is the Python package sdist. It must be excluded twice over: its
    tag lacks the `tests` namespace, and it ships no fixture tarball.
    """
    with pytest.raises(NoSuchReleaseError):
        get_release_url_from_release_information(
            release_name, release_information
        )


@pytest.mark.parametrize(
    "url,expected",
    [
        # All currently supported release-hosting repos must be recognized so
        # `FixtureDownloader.get_cache_path` versions the cache directory by
        # release tag. A repo missing from `SUPPORTED_REPOS` falls through to
        # the unversioned `cache_folder / "other" / archive_name` path, which
        # silently shadows newer releases with the same archive filename.
        (
            "https://github.com/ethereum/execution-spec-tests/releases/download/v3.0.0/fixtures_stable.tar.gz",
            True,
        ),
        (
            "https://github.com/ethereum/execution-specs/releases/download/tests-bal%40v7.1.0/fixtures_bal.tar.gz",
            True,
        ),
        (
            "https://github.com/ethereum/tests/releases/download/v14.0/some.tar.gz",
            True,
        ),
        (
            "https://github.com/ethereum/legacytests/releases/download/v1.0/some.tar.gz",
            True,
        ),
        (
            # Not a recognized repo; must NOT match.
            "https://github.com/some-fork/execution-spec-tests/releases/download/v1/foo.tar.gz",
            False,
        ),
        (
            # Local path, not a URL.
            "./fixtures",
            False,
        ),
    ],
)
def test_is_release_url_covers_supported_repos(
    url: str, expected: bool
) -> None:
    """
    All entries in `SUPPORTED_REPOS` must be matched by `is_release_url`.

    Regression test for bal-devnet-7: when the BAL fixture URL moved from
    `execution-spec-tests` to `execution-specs`, the new URL stopped being
    recognized as a release URL, so the cache key dropped the version tag and
    a `tests-bal@v7.0.0` download from a prior session silently shadowed
    `tests-bal@v7.1.0`.
    """
    assert is_release_url(url) is expected


def test_supported_repos_contains_execution_specs() -> None:
    """
    `ethereum/execution-specs` hosts the BAL fixture releases (from
    `tests-bal@v7.1.0` onward) and must be in `SUPPORTED_REPOS`.
    """
    assert "ethereum/execution-specs" in SUPPORTED_REPOS
