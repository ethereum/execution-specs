"""Pytest (plugin) definitions local to EIP-6780 tests."""

import pytest

from ethereum_test_tools import Address, Alloc, Environment


@pytest.fixture
def env() -> Environment:
    """Environment for all tests."""
    return Environment()


@pytest.fixture
def selfdestruct_recipient_address(pre: Alloc) -> Address:
    """Address that can receive a SELFDESTRUCT operation."""
    return pre.fund_eoa(amount=0)
