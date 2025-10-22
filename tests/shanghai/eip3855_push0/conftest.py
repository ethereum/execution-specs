"""Fixtures for the EIP-3855 PUSH0 tests."""

import pytest
from eest import Alloc, Environment


@pytest.fixture
def env() -> Environment:
    """Environment fixture."""
    return Environment()


@pytest.fixture
def post() -> Alloc:
    """Post state fixture."""
    return Alloc()
