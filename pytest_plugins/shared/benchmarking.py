"""The module contains the pytest hooks for the gas benchmark values."""

import pytest

from ethereum_test_tools import Environment
from ethereum_test_types import EnvironmentDefaults

from .execute_fill import OpMode


def pytest_addoption(parser: pytest.Parser):
    """Add command line options for gas benchmark values."""
    evm_group = parser.getgroup("evm", "Arguments defining evm executable behavior")
    evm_group.addoption(
        "--gas-benchmark-values",
        action="store",
        dest="gas_benchmark_value",
        type=str,
        default=None,
        help="Specify gas benchmark values for tests as a comma-separated list.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Configure the fill and execute mode to benchmarking."""
    if config.getoption("gas_benchmark_value"):
        config.op_mode = OpMode.BENCHMARKING


def pytest_generate_tests(metafunc: pytest.Metafunc):
    """Generate tests for the gas benchmark values."""
    if "gas_benchmark_value" in metafunc.fixturenames:
        gas_benchmark_values = metafunc.config.getoption("gas_benchmark_value")
        if gas_benchmark_values:
            gas_values = [int(x.strip()) for x in gas_benchmark_values.split(",")]
            gas_parameters = [
                pytest.param(gas_value * 1_000_000, id=f"benchmark-gas-value_{gas_value}M")
                for gas_value in gas_values
            ]
            metafunc.parametrize("gas_benchmark_value", gas_parameters, scope="function")


@pytest.fixture(scope="function")
def gas_benchmark_value(request: pytest.FixtureRequest) -> int:
    """Return a single gas benchmark value for the current test."""
    if hasattr(request, "param"):
        return request.param

    return EnvironmentDefaults.gas_limit


BENCHMARKING_MAX_GAS = 500_000_000_000


@pytest.fixture
def genesis_environment(request: pytest.FixtureRequest) -> Environment:  # noqa: D103
    """Return an Environment instance with appropriate gas limit based on test type."""
    if request.node.get_closest_marker("benchmark") is not None:
        return Environment(gas_limit=BENCHMARKING_MAX_GAS)
    return Environment()


@pytest.fixture
def env(request: pytest.FixtureRequest) -> Environment:  # noqa: D103
    """Return an Environment instance with appropriate gas limit based on test type."""
    if request.node.get_closest_marker("benchmark") is not None:
        return Environment(gas_limit=BENCHMARKING_MAX_GAS)
    return Environment()
