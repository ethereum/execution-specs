"""
Fixtures for the EIP-3855 PUSH0 tests.
"""

import pytest

from ethereum_test_tools import EOA, Alloc, Environment


@pytest.fixture
def env() -> Environment:  # noqa: D103
    return Environment()


@pytest.fixture
def post() -> Alloc:  # noqa: D103
    return Alloc()


@pytest.fixture
def sender(pre: Alloc) -> EOA:
    """
    Funded EOA used for sending transactions.
    """
    return pre.fund_eoa()
