"""
Common pytest fixtures for ethereum_test_tools tests.
"""

import pytest
from semver import Version

from ..code import Yul

SUPPORTED_SOLC_VERSIONS = [Version.parse(v) for v in ["0.8.20", "0.8.21", "0.8.22", "0.8.23"]]

SOLC_PADDING_VERSION = Version.parse("0.8.21")


@pytest.fixture(scope="session")
def solc_version() -> Version:
    """Return the version of solc being used for tests."""
    solc_version = Yul("").version().finalize_version()
    if solc_version not in SUPPORTED_SOLC_VERSIONS:
        raise Exception("Unsupported solc version: {}".format(solc_version))
    return solc_version
