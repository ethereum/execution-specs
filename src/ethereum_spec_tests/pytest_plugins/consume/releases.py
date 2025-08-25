"""Procedures to consume fixtures from Github releases."""

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List
from urllib.parse import urlparse

import platformdirs
import requests
from pydantic import BaseModel, Field, RootModel

CACHED_RELEASE_INFORMATION_FILE = (
    Path(platformdirs.user_cache_dir("ethereum-execution-spec-tests")) / "release_information.json"
)

SUPPORTED_REPOS = ["ethereum/execution-spec-tests", "ethereum/tests", "ethereum/legacytests"]


class NoSuchReleaseError(Exception):
    """Raised when a release does not exist."""

    def __init__(self, release_string: str):
        """Initialize the exception."""
        super().__init__(f"Unknown release source: {release_string}")


class AssetNotFoundError(Exception):
    """Raised when a release has no assets."""

    def __init__(self, release_string: str):
        """Initialize the exception."""
        super().__init__(f"Asset not found: {release_string}")


@dataclass(kw_only=True)
class ReleaseTag:
    """A descriptor for a release."""

    tag_name: str
    version: str | None

    @classmethod
    def from_string(cls, release_string: str) -> "ReleaseTag":
        """
        Create a release descriptor from a string.

        The release source can be in the format `tag_name@version` or just `tag_name`.
        """
        version: str | None
        if "@" in release_string:
            tag_name, version = release_string.split("@")
            if version == "" or version.lower() == "latest":
                version = None
        else:
            tag_name = release_string
            version = None
        return cls(tag_name=tag_name, version=version)

    @staticmethod
    def is_release_string(release_string: str) -> bool:
        """Check if the release string is in the correct format."""
        return "@" in release_string

    def __eq__(self, value) -> bool:
        """
        Check if the release descriptor matches the string value.

        Returns True if the value is the same as the tag name or the tag name and version.
        """
        assert isinstance(value, str), f"Expected a string, but got: {value}"
        if self.version is not None:
            # normal release, e.g., stable@v4.0.0
            normal_release_match = value == self.version
            # pre release, e.g., pectra-devnet-6@v1.0.0
            pre_release_match = value == f"{self.tag_name}@{self.version}"
            return normal_release_match or pre_release_match
        return value.startswith(self.tag_name)

    @property
    def asset_name(self) -> str:
        """Get the asset name."""
        return f"fixtures_{self.tag_name}.tar.gz"


class Asset(BaseModel):
    """Information about a release asset."""

    url: str = Field(..., alias="browser_download_url")
    id: int
    name: str
    content_type: str
    size: int


class Assets(RootModel[List[Asset]]):
    """A list of assets and their information."""

    root: List[Asset]

    def __contains__(self, release_descriptor: ReleaseTag) -> bool:
        """Check if the assets contain the release descriptor."""
        return any(release_descriptor.asset_name == asset.name for asset in self.root)


class ReleaseInformation(BaseModel):
    """Information about a release."""

    url: str = Field(..., alias="html_url")
    id: int
    tag_name: str
    name: str
    created_at: datetime
    published_at: datetime
    assets: Assets

    def __contains__(self, release_descriptor: ReleaseTag) -> bool:
        """Check if the release information contains the release descriptor."""
        if release_descriptor.version is not None:
            return release_descriptor == self.tag_name
        for asset in self.assets.root:
            if asset.name == release_descriptor.asset_name:
                return True
        return False

    def get_asset(self, release_descriptor: ReleaseTag) -> Asset:
        """Get the asset URL."""
        for asset in self.assets.root:
            if asset.name == release_descriptor.asset_name:
                return asset
        raise AssetNotFoundError(release_descriptor.tag_name)


class Releases(RootModel[List[ReleaseInformation]]):
    """A list of releases and their information."""

    root: List[ReleaseInformation]


def is_docker_or_ci() -> bool:
    """Check if the code is running inside a Docker container or a CI environment."""
    return "GITHUB_ACTIONS" in os.environ or Path("/.dockerenv").exists()


def is_url(string: str) -> bool:
    """Check if a string is a remote URL."""
    result = urlparse(string)
    return all([result.scheme, result.netloc])


def is_release_url(input_str: str) -> bool:
    """Check if the release string is a URL."""
    if not is_url(input_str):
        return False
    repo_pattern = "|".join(re.escape(repo) for repo in SUPPORTED_REPOS)
    regex_pattern = rf"https://github\.com/({repo_pattern})/releases/download/"
    return re.match(regex_pattern, input_str) is not None


def parse_release_information(release_information: List) -> List[ReleaseInformation]:
    """Parse the release information from the Github API."""
    return Releases.model_validate(release_information).root  # type: ignore


def download_release_information(destination_file: Path | None) -> List[ReleaseInformation]:
    """
    Download all releases from the GitHub API, handling pagination properly.

    GitHub's API returns releases in pages of 30 by default. This function
    follows the pagination links to ensure we get every release, which is
    crucial for finding older version or latest releases.
    """
    all_releases = []
    for repo in SUPPORTED_REPOS:
        current_url: str | None = f"https://api.github.com/repos/{repo}/releases"
        max_pages = 2
        while current_url and max_pages > 0:
            max_pages -= 1
            response = requests.get(current_url)
            response.raise_for_status()
            all_releases.extend(response.json())
            current_url = None
            if "link" in response.headers:
                for link in requests.utils.parse_header_links(response.headers["link"]):
                    if link["rel"] == "next":
                        current_url = link["url"]
                        break

    if destination_file:
        destination_file.parent.mkdir(parents=True, exist_ok=True)
        with open(destination_file, "w") as file:
            json.dump(all_releases, file)
    return parse_release_information(all_releases)


def parse_release_information_from_file(
    release_information_file: Path,
) -> List[ReleaseInformation]:
    """Parse the release information from a file."""
    with open(release_information_file, "r") as file:
        release_information = json.load(file)
    return parse_release_information(release_information)


def get_release_url_from_release_information(
    release_string: str, release_information: List[ReleaseInformation]
) -> str:
    """Get the URL for a specific release."""
    release_descriptor = ReleaseTag.from_string(release_string)
    for release in release_information:
        if release_descriptor in release:
            return release.get_asset(release_descriptor).url
    raise NoSuchReleaseError(release_string)


def get_release_page_url(release_string: str) -> str:
    """
    Return the GitHub Release page URL for a specific release descriptor.

    This function can handle:
    - A standard release string (e.g., "eip7692@latest") - from execution-spec-tests only.
    - A direct asset download link (e.g.,
        "https://github.com/ethereum/execution-spec-tests/releases/download/v4.0.0/fixtures_eip7692.tar.gz").
    """
    release_information = get_release_information()

    # Case 1: If it's a direct GitHub Releases download link,
    #         find which release in `release_information` has an asset with this exact URL.
    repo_pattern = "|".join(re.escape(repo) for repo in SUPPORTED_REPOS)
    regex_pattern = rf"https://github\.com/({repo_pattern})/releases/download/"
    if re.match(regex_pattern, release_string):
        for release in release_information:
            for asset in release.assets.root:
                if asset.url == release_string:
                    return release.url  # The HTML page for this release
        raise NoSuchReleaseError(f"No release found for asset URL: {release_string}")

    # Case 2: Otherwise, treat it as a release descriptor (e.g., "eip7692@latest")
    release_descriptor = ReleaseTag.from_string(release_string)
    for release in release_information:
        if release_descriptor in release:
            return release.url

    # If nothing matched, raise
    raise NoSuchReleaseError(release_string)


def get_release_information() -> List[ReleaseInformation]:
    """
    Get the release information.

    First check if the cached release information file exists. If it does, but it is older than 4
    hours, delete the file, unless running inside a CI environment or a Docker container.
    Then download the release information from the Github API and save it to the cache file.
    """
    if CACHED_RELEASE_INFORMATION_FILE.exists():
        last_modified = CACHED_RELEASE_INFORMATION_FILE.stat().st_mtime
        if (datetime.now().timestamp() - last_modified) < 4 * 60 * 60 or is_docker_or_ci():
            return parse_release_information_from_file(CACHED_RELEASE_INFORMATION_FILE)
        CACHED_RELEASE_INFORMATION_FILE.unlink()
    if not CACHED_RELEASE_INFORMATION_FILE.exists():
        return download_release_information(CACHED_RELEASE_INFORMATION_FILE)
    return parse_release_information_from_file(CACHED_RELEASE_INFORMATION_FILE)


def get_release_url(release_string: str) -> str:
    """Get the URL for a specific release."""
    release_information = get_release_information()
    return get_release_url_from_release_information(release_string, release_information)
