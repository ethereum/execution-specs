"""Pytest (plugin) definitions local to Identity precompile tests."""

import pytest
from execution_testing import Fork


@pytest.fixture
def tx_gas_limit(fork: Fork) -> int:
    """Return the gas limit for transactions."""
    # The `nonzerovalue` variants transfer 1 wei to the identity
    # precompile, creating its account and charging NEW_ACCOUNT
    # state gas under EIP-8037 (0 otherwise).
    return 365_224 + fork.gas_costs().NEW_ACCOUNT
