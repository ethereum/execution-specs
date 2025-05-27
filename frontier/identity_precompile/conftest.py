"""Pytest (plugin) definitions local to Identity precompile tests."""

import pytest


@pytest.fixture
def tx_gas_limit() -> int:
    """Return the gas limit for transactions."""
    return 365_224
