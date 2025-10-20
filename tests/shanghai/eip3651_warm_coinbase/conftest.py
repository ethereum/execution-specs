"""Fixtures for the EIP-3651 warm coinbase tests."""

import pytest

from ethereum_test_tools import Alloc, Environment


@pytest.fixture
def env() -> Environment:
    """Environment fixture."""
    return Environment()


@pytest.fixture
def post() -> Alloc:
    """Post state fixture."""
    return Alloc()
