"""
Common pytest fixtures for ethereum_test_tools tests.
"""

import pytest
from packaging import version

from ..code import Yul

SUPPORTED_SOLC_VERSIONS = [
    version.parse(v)
    for v in [
        "0.8.20",
        "0.8.21",
    ]
]


@pytest.fixture(scope="session")
def solc_version() -> version.Version:
    """Return the version of solc being used for tests."""
    solc_version = version.parse(Yul("").version().split("+")[0])
    if solc_version not in SUPPORTED_SOLC_VERSIONS:
        raise Exception("Unsupported solc version: {}".format(solc_version))
    return solc_version
