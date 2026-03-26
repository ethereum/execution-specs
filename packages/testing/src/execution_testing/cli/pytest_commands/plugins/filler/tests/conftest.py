"""Pytest configuration for filler tests."""

from typing import Generator

import pytest


@pytest.fixture(autouse=True)
def restore_environment_defaults() -> Generator[None, None, None]:
    """
    Reset EnvironmentDefaults.gas_limit around each test.

    Reset the gas limit to DEFAULT_BLOCK_GAS_LIMIT before and after each test
    run to prevent side effects from nested in-process pytest sessions leaking
    into later tests on the same worker.
    """
    from execution_testing.test_types.block_types import (
        DEFAULT_BLOCK_GAS_LIMIT,
        EnvironmentDefaults,
    )

    EnvironmentDefaults.gas_limit = DEFAULT_BLOCK_GAS_LIMIT
    yield
    EnvironmentDefaults.gas_limit = DEFAULT_BLOCK_GAS_LIMIT
