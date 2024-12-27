"""Common pytest fixtures for ethereum_test_tools tests."""

import pytest
from semver import Version

from ethereum_test_forks import Frontier

from ..code import Solc

SOLC_PADDING_VERSION = Version.parse("0.8.21")


@pytest.fixture(scope="session")
def solc_version() -> Version:
    """Return the version of solc being used for tests."""
    solc_version = Solc("").version.finalize_version()
    if solc_version < Frontier.solc_min_version():
        raise Exception("Unsupported solc version: {}".format(solc_version))
    return solc_version
