"""Pytest plugin to deploy required contracts for execute command."""

from typing import Literal

import pytest

from execution_testing.forks import Fork, ForkAdapter
from execution_testing.rpc import EthRPC


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    deploy_group = parser.getgroup(
        "execute", "Arguments for deploying required contracts."
    )
    deploy_group.addoption(
        "--gas-price",
        action="store",
        dest="deploy_gas_price",
        type=int,
        default=None,
        help=(
            "Gas price to use for deployment transactions in wei. "
            "Default: 1.5x the current network gas price."
        ),
    )
    deploy_group.addoption(
        "--check-only",
        action="store_true",
        dest="check_only",
        default=False,
        help="Only check if contracts are deployed without deploying them.",
    )
    deploy_group.addoption(
        "--fork",
        action="store",
        dest="fork",
        type=ForkAdapter.validate_python,
        default=None,
        help="Currently active fork of the network.",
    )


@pytest.fixture(scope="session")
def gas_price(request: pytest.FixtureRequest, eth_rpc: EthRPC) -> int:
    """Get the gas price for deployment transactions."""
    gas_price_option = request.config.option.deploy_gas_price
    if gas_price_option is not None:
        return gas_price_option

    # Use network gas price
    return int(eth_rpc.gas_price() * 1.5)


@pytest.fixture(scope="session")
def check_only(request: pytest.FixtureRequest) -> bool:
    """Get the check-only flag."""
    return request.config.option.check_only


@pytest.fixture(scope="session")
def session_fork(request: pytest.FixtureRequest) -> Fork:
    """Return a default fork for the deploy command."""
    return request.config.option.fork


@pytest.fixture(scope="session")
def transactions_per_block() -> Literal[1]:
    """Return the number of transactions per block for the deploy command."""
    return 1
