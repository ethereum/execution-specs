"""Pytest (plugin) definitions local to EIP-6780 tests."""

import pytest
from execution_testing import Address, Alloc, Environment


@pytest.fixture
def env() -> Environment:
    """Environment for all tests."""
    return Environment()


@pytest.fixture
def selfdestruct_recipient_address(pre: Alloc) -> Address:
    """Address that can receive a SELFDESTRUCT operation."""
    return pre.fund_eoa(amount=0)
