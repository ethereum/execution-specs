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


@pytest.fixture(autouse=True)
def restore_chain_config_defaults() -> Generator[None, None, None]:
    """
    Reset ChainConfigDefaults.chain_id around each test.

    `--chain-id` is applied by the nested in-process fill session, so without
    this it leaks into later tests on the same worker.
    """
    from execution_testing.test_types.chain_config_types import (
        DEFAULT_CHAIN_ID,
        ChainConfigDefaults,
    )

    ChainConfigDefaults.chain_id = DEFAULT_CHAIN_ID
    yield
    ChainConfigDefaults.chain_id = DEFAULT_CHAIN_ID
