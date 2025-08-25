"""Test release parsing given the github repository release JSON data."""

from os.path import realpath
from pathlib import Path
from typing import List

import pytest

from ..releases import (
    ReleaseInformation,
    get_release_url_from_release_information,
    parse_release_information_from_file,
)

CURRENT_FILE = Path(realpath(__file__))
CURRENT_FOLDER = CURRENT_FILE.parent


@pytest.fixture(scope="session")
def release_information() -> List[ReleaseInformation]:
    """Return the release information from a file."""
    return parse_release_information_from_file(CURRENT_FOLDER / "release_information.json")


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
):
    """Test release parsing."""
    assert (
        "https://github.com/ethereum/execution-spec-tests/releases/download/"
        + expected_release_download_url
    ) == get_release_url_from_release_information(release_name, release_information)
