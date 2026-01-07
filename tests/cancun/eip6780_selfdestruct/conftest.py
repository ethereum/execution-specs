"""Pytest (plugin) definitions local to EIP-6780 tests."""

import pytest
from execution_testing import Address, Alloc, Environment
from execution_testing.forks.helpers import Fork


@pytest.fixture
def env() -> Environment:
    """Environment for all tests."""
    return Environment()


@pytest.fixture
def selfdestruct_recipient_address(pre: Alloc) -> Address:
    """Address that can receive a SELFDESTRUCT operation."""
    return pre.fund_eoa(amount=0)


@pytest.fixture
def fork_extra_gas(fork: Fork) -> int:
    """
    Extra gas variable by fork to ensure there is enough gas for the
    transaction. Applicable only for tests which do not test gas usage. The
    amount of gas required is a very rough estimate.
    """
    gas_costs = fork.gas_costs()
    sstore_cost = 5 * (gas_costs.G_STORAGE_SET + gas_costs.G_COLD_SLOAD)
    cold_access_cost = 5 * gas_costs.G_COLD_ACCOUNT_ACCESS
    return sstore_cost + cold_access_cost
