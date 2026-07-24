"""Test release parsing given the github repository release JSON data."""

import os
import shutil
import time
from os.path import realpath
from pathlib import Path
from typing import Any, Dict, List

import pytest
import requests

from .. import releases
from ..releases import (
    SUPPORTED_REPOS,
    NoSuchReleaseError,
    ReleaseInformation,
    download_release_information,
    get_release_page_url,
    get_release_url,
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


# TODO: Remove with the legacy `stable`/`develop` support and the `v4.5.0`
# manifest entry after 2026-08 (see #3085).
@pytest.mark.parametrize(
    "release_name,expected_release_download_url",
    [
        (
            "stable@latest",
            "v4.5.0/fixtures_stable.tar.gz",
        ),
        (
            "develop@v4.5.0",
            "v4.5.0/fixtures_develop.tar.gz",
        ),
    ],
)
def test_legacy_release_parsing(
    release_name: str,
    expected_release_download_url: str,
    release_information: List[ReleaseInformation],
) -> None:
    """Test legacy `stable`/`develop` releases still resolve."""
    assert (
        "https://github.com/ethereum/execution-spec-tests/releases/download/"
        + expected_release_download_url
    ) == get_release_url_from_release_information(
        release_name, release_information
    )


@pytest.mark.parametrize(
    "release_name",
    [
        # A bare `vX.Y.Z` is shorthand for `tests@vX.Y.Z` and must never
        # fall back to the spec-package release tagged plain `v2.20.0` in
        # the manifest, even though it is the most recently published
        # release and its version exists.
        "v2.20.0",
        "tests@v2.20.0",
        # The legacy `stable`/`develop` fallback matches bare `vX.Y.Z`
        # tags, but the asset check must still exclude the decoy.
        "stable@v2.20.0",
    ],
)
def test_non_fixture_releases_do_not_resolve(
    release_name: str,
    release_information: List[ReleaseInformation],
) -> None:
    """
    Test that spec-package releases never resolve.

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


class FakeResponse:
    """A minimal stand-in for `requests.Response`."""

    def __init__(
        self, payload: List[Dict], rate_limited: bool = False
    ) -> None:
        """Initialize with a JSON payload or a rate-limited failure."""
        self.payload = payload
        self.rate_limited = rate_limited
        self.headers: Dict[str, str] = {}

    def json(self) -> List[Dict]:
        """Return the JSON payload."""
        return self.payload

    def raise_for_status(self) -> None:
        """Raise an `HTTPError` if the response is rate-limited."""
        if self.rate_limited:
            raise requests.exceptions.HTTPError(
                "403 Client Error: rate limit exceeded"
            )


def fake_release(tag_name: str, asset_name: str) -> Dict:
    """Build a minimal GitHub API release entry."""
    encoded_tag = tag_name.replace("@", "%40")
    return {
        "html_url": "https://github.com/ethereum/execution-specs/releases/"
        f"tag/{encoded_tag}",
        "id": 1,
        "tag_name": tag_name,
        "name": tag_name,
        "created_at": "2026-07-15T00:00:00Z",
        "published_at": "2026-07-15T00:00:00Z",
        "assets": [
            {
                "browser_download_url": "https://github.com/ethereum/"
                f"execution-specs/releases/download/{encoded_tag}/"
                f"{asset_name}",
                "id": 1,
                "name": asset_name,
                "content_type": "application/gzip",
                "size": 1,
            }
        ],
    }


@pytest.fixture
def release_cache_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """
    Redirect the release-information cache to a temporary path.

    Also disable the CI/Docker detection so the freshness check applies
    (in CI, the cache never expires).
    """
    cache_file = tmp_path / "release_information.json"
    monkeypatch.setattr(
        releases, "CACHED_RELEASE_INFORMATION_FILE", cache_file
    )
    monkeypatch.setattr(releases, "is_docker_or_ci", lambda: False)
    return cache_file


@pytest.fixture
def release_information_cache(release_cache_path: Path) -> Path:
    """Populate the redirected cache with a copy of the test manifest."""
    shutil.copyfile(
        CURRENT_FOLDER / "release_information.json", release_cache_path
    )
    return release_cache_path


def make_stale(cache_file: Path) -> None:
    """Age the cache file's mtime beyond the 4-hour freshness window."""
    stale_time = time.time() - 5 * 60 * 60
    os.utime(cache_file, (stale_time, stale_time))


def block_api(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any GitHub API request fail the test."""

    def no_api(*args: Any, **kwargs: Any) -> None:
        del args, kwargs
        pytest.fail("The GitHub API must not be hit")

    monkeypatch.setattr(releases.requests, "get", no_api)


def rate_limited_get(*args: Any, **kwargs: Any) -> FakeResponse:
    """Return a rate-limited (403) GitHub API response."""
    del args, kwargs
    return FakeResponse([], rate_limited=True)


def new_release_get(*args: Any, **kwargs: Any) -> FakeResponse:
    """Return a single-page response with a new `tests@v21.0.0` release."""
    del args, kwargs
    return FakeResponse([fake_release("tests@v21.0.0", "fixtures.tar.gz")])


def test_pinned_release_resolves_from_stale_cache_without_api(
    release_information_cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    A pinned version already resolvable from the cache must not refresh.

    Release tags are immutable, so a cached entry for an exact version
    cannot be outdated, no matter how old the cache file is. Regression
    test for `consume --input=tests@vX.Y.Z` raising INTERNALERROR when
    the unauthenticated GitHub API rate limit is exhausted, even though
    the (stale) cache resolved the release.
    """
    make_stale(release_information_cache)
    block_api(monkeypatch)
    assert get_release_url("tests@v20.0.0") == (
        "https://github.com/ethereum/execution-specs/releases/download/"
        "tests%40v20.0.0/fixtures.tar.gz"
    )
    assert get_release_page_url("tests@v20.0.0") == (
        "https://github.com/ethereum/execution-specs/releases/tag/"
        "tests%40v20.0.0"
    )
    assert release_information_cache.exists()


def test_fresh_cache_resolves_latest_without_api(
    release_information_cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fresh cache resolves unpinned lookups without an API request."""
    del release_information_cache
    block_api(monkeypatch)
    assert get_release_url("tests@latest").endswith(
        "tests%40v20.0.0/fixtures.tar.gz"
    )


def test_rate_limited_refresh_falls_back_to_stale_cache(
    release_information_cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    A failed refresh must fall back to the stale cache, not delete it.

    Previously the stale cache file was deleted before the download was
    attempted, so a rate-limited refresh crashed the run and left no
    cache at all, forcing every subsequent run onto the API.
    """
    make_stale(release_information_cache)
    monkeypatch.setattr(releases.requests, "get", rate_limited_get)
    assert get_release_url("tests@latest").endswith(
        "tests%40v20.0.0/fixtures.tar.gz"
    )
    assert release_information_cache.exists()


def test_rate_limited_refresh_without_cache_raises(
    release_cache_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without a cache file, a failed refresh is a hard error."""
    del release_cache_path
    monkeypatch.setattr(releases.requests, "get", rate_limited_get)
    with pytest.raises(requests.exceptions.HTTPError):
        get_release_url("tests@latest")


def test_unpinned_release_refreshes_stale_cache(
    release_information_cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    An unpinned lookup with a stale cache must refresh from the API.

    `latest` and bare feature names can resolve to a newer release at
    any time, so the pinned-release fast path must not apply to them.
    """
    make_stale(release_information_cache)
    calls: List[str] = []

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        calls.append(url)
        return new_release_get(url, **kwargs)

    monkeypatch.setattr(releases.requests, "get", fake_get)
    assert get_release_url("tests@latest").endswith(
        "tests%40v21.0.0/fixtures.tar.gz"
    )
    assert len(calls) == len(SUPPORTED_REPOS)
    assert "tests@v21.0.0" in release_information_cache.read_text()


def test_pinned_release_not_in_stale_cache_refreshes(
    release_information_cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    A pinned version missing from the stale cache must refresh.

    The pinned-release fast path only applies when the cache already
    resolves the requested version.
    """
    make_stale(release_information_cache)
    monkeypatch.setattr(releases.requests, "get", new_release_get)
    assert get_release_url("tests@v21.0.0").endswith(
        "tests%40v21.0.0/fixtures.tar.gz"
    )


def test_corrupt_cache_file_is_refreshed(
    release_information_cache: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    A corrupt cache file must be re-downloaded, not crash the run.

    A partially-written download (e.g. a killed process) must not wedge
    every subsequent run until the file is manually deleted.
    """
    release_information_cache.write_text("{ not json")
    monkeypatch.setattr(releases.requests, "get", new_release_get)
    assert get_release_url("tests@v21.0.0").endswith(
        "tests%40v21.0.0/fixtures.tar.gz"
    )


@pytest.mark.parametrize(
    "environment,expected_token",
    [
        pytest.param({}, None, id="unauthenticated"),
        pytest.param(
            {"GITHUB_TOKEN": "ghp_test_token"},
            "ghp_test_token",
            id="github_token",
        ),
        pytest.param(
            {"GH_TOKEN": "gho_test_token"},
            "gho_test_token",
            id="gh_token",
        ),
        pytest.param(
            {"GITHUB_TOKEN": "ghp_test_token", "GH_TOKEN": "gho_other"},
            "ghp_test_token",
            id="github_token_wins",
        ),
    ],
)
def test_download_release_information_github_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    environment: Dict[str, str],
    expected_token: str | None,
) -> None:
    """
    Authenticate GitHub API requests iff a GitHub token is set.

    `GITHUB_TOKEN` (preferred) or `GH_TOKEN` (the gh CLI's name)
    authenticates the request: 5000 requests/hour instead of the
    unauthenticated 60 requests/hour per IP.
    """
    for variable in ("GITHUB_TOKEN", "GH_TOKEN"):
        monkeypatch.delenv(variable, raising=False)
    for variable, token in environment.items():
        monkeypatch.setenv(variable, token)
    seen_headers: List[Dict[str, str]] = []

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        seen_headers.append(kwargs.get("headers") or {})
        return new_release_get(url, **kwargs)

    monkeypatch.setattr(releases.requests, "get", fake_get)
    download_release_information(tmp_path / "release_information.json")
    expected_headers = (
        {}
        if expected_token is None
        else {"Authorization": f"Bearer {expected_token}"}
    )
    assert seen_headers == [expected_headers] * len(SUPPORTED_REPOS)
