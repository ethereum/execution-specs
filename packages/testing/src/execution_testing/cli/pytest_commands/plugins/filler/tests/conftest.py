"""Pytest configuration for filler tests."""

from typing import Generator

import pytest


@pytest.fixture
def restore_environment_defaults() -> Generator[None, None, None]:
    """Restore EnvironmentDefaults.gas_limit after test runs to prevent side effects."""
    from execution_testing.test_types.block_types import EnvironmentDefaults

    original_gas_limit = EnvironmentDefaults.gas_limit
    yield
    EnvironmentDefaults.gas_limit = original_gas_limit
