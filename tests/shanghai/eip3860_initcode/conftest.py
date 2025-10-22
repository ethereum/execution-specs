"""Fixtures for the EIP-3860 initcode tests."""

import pytest
from execution_testing import Alloc, Environment


@pytest.fixture
def env() -> Environment:
    """Environment fixture."""
    return Environment()


@pytest.fixture
def post() -> Alloc:
    """Post state fixture."""
    return Alloc()
