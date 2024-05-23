"""
Pytest fixtures for EIP-663 tests
"""
import pytest

from ethereum_test_tools import Transaction


@pytest.fixture
def tx() -> Transaction:
    """
    Produces the default Transaction.
    """
    return Transaction(to=0xC0DE, gas_limit=10_000_000)
