"""Test release parsing given the github repository release JSON data."""

from os.path import realpath
from pathlib import Path
from typing import List

import pytest

from ..releases import (
    SUPPORTED_REPOS,
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
        (
            "pectra-devnet-5",
            "pectra-devnet-5%40v1.0.0/fixtures_pectra-devnet-5.tar.gz",
        ),
        (
            "pectra-devnet-4@v1.0.0",
            "pectra-devnet-4%40v1.0.0/fixtures_pectra-devnet-4.tar.gz",
        ),
        (
            "stable",
            "v3.0.0/fixtures_stable.tar.gz",
        ),
        (
            "develop",
            "v3.0.0/fixtures_develop.tar.gz",
        ),
        (
            "eip7692-prague",
            "eip7692%40v1.1.1/fixtures_eip7692-prague.tar.gz",
        ),
    ],
)
def test_release_parsing(
    release_name: str,
    expected_release_download_url: str,
    release_information: List[ReleaseInformation],
) -> None:
    """Test release parsing."""
    assert (
        "https://github.com/ethereum/execution-spec-tests/releases/download/"
        + expected_release_download_url
    ) == get_release_url_from_release_information(
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
