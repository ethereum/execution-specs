"""The module contains the pytest hooks for the gas benchmark values."""

import pytest

from execution_testing.test_types import Environment, EnvironmentDefaults

from .execute_fill import OpMode


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command line options for gas benchmark values."""
    evm_group = parser.getgroup(
        "evm", "Arguments defining evm executable behavior"
    )
    evm_group.addoption(
        "--gas-benchmark-values",
        action="store",
        dest="gas_benchmark_value",
        type=str,
        default=None,
        help="Specify gas benchmark values for tests as a comma-separated list.",
    )
    evm_group.addoption(
        "--fixed-opcode-count",
        action="store",
        dest="fixed_opcode_count",
        type=str,
        default=None,
        help="Specify fixed opcode counts for benchmark tests as a comma-separated list.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Configure the fill and execute mode to benchmarking."""
    config.addinivalue_line(
        "markers",
        "gas_ref: Mark test as a gas reference test for gas repricing analysis",
    )
    if config.getoption("gas_benchmark_value"):
        config.op_mode = OpMode.BENCHMARKING  # type: ignore[attr-defined]


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip non-gas_ref tests when --fixed-opcode-count is specified."""
    fixed_opcode_count = config.getoption("fixed_opcode_count")
    if not fixed_opcode_count:
        # If --fixed-opcode-count is not specified, don't filter anything
        return

    # Filter: keep only tests with gas_ref marker
    for item in items:
        has_gas_ref = item.get_closest_marker("gas_ref") is not None
        has_benchmark = item.get_closest_marker("benchmark") is not None

        # Skip benchmark tests that don't have gas_ref marker
        if has_benchmark and not has_gas_ref:
            item.add_marker(
                pytest.mark.skip(
                    reason="Test does not have gas_ref marker (required for --fixed-opcode-count)"
                )
            )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate tests for the gas benchmark values and fixed opcode counts."""
    if "gas_benchmark_value" in metafunc.fixturenames:
        gas_benchmark_values = metafunc.config.getoption("gas_benchmark_value")
        if gas_benchmark_values:
            gas_values = [
                int(x.strip()) for x in gas_benchmark_values.split(",")
            ]
            gas_parameters = [
                pytest.param(
                    gas_value * 1_000_000,
                    id=f"benchmark-gas-value_{gas_value}M",
                )
                for gas_value in gas_values
            ]
            metafunc.parametrize(
                "gas_benchmark_value", gas_parameters, scope="function"
            )

    if "fixed_opcode_count" in metafunc.fixturenames:
        # Only parametrize if test has gas_ref marker
        has_gas_ref = (
            metafunc.definition.get_closest_marker("gas_ref") is not None
        )
        if has_gas_ref:
            fixed_opcode_counts = metafunc.config.getoption(
                "fixed_opcode_count"
            )
            if fixed_opcode_counts:
                opcode_counts = [
                    int(x.strip()) for x in fixed_opcode_counts.split(",")
                ]
                opcode_count_parameters = [
                    pytest.param(
                        opcode_count,
                        id=f"opcount_{opcode_count}",
                    )
                    for opcode_count in opcode_counts
                ]
                metafunc.parametrize(
                    "fixed_opcode_count",
                    opcode_count_parameters,
                    scope="function",
                )


@pytest.fixture(scope="function")
def gas_benchmark_value(request: pytest.FixtureRequest) -> int:
    """Return a single gas benchmark value for the current test."""
    if hasattr(request, "param"):
        return request.param

    return EnvironmentDefaults.gas_limit


@pytest.fixture(scope="function")
def fixed_opcode_count(request: pytest.FixtureRequest) -> int | None:
    """Return a fixed opcode count for the current test, or None if not set."""
    if hasattr(request, "param"):
        return request.param

    return None


BENCHMARKING_MAX_GAS = 1_000_000_000_000


@pytest.fixture
def genesis_environment(request: pytest.FixtureRequest) -> Environment:  # noqa: D103
    """
    Return an Environment instance with appropriate gas limit based on test
    type.
    """
    if request.node.get_closest_marker("benchmark") is not None:
        return Environment(gas_limit=BENCHMARKING_MAX_GAS)
    return Environment()


@pytest.fixture
def env(request: pytest.FixtureRequest) -> Environment:  # noqa: D103
    """
    Return an Environment instance with appropriate gas limit based on test
    type.
    """
    if request.node.get_closest_marker("benchmark") is not None:
        return Environment(gas_limit=BENCHMARKING_MAX_GAS)
    return Environment()
