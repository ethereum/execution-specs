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
        help="Specify fixed opcode counts (in thousands) for benchmark tests as a comma-separated list.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Configure the fill and execute mode to benchmarking."""
    config.addinivalue_line(
        "markers",
        "repricing: Mark test as reference test for gas repricing analysis",
    )
    if config.getoption("gas_benchmark_value"):
        config.op_mode = OpMode.BENCHMARKING  # type: ignore[attr-defined]


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Remove non-repricing tests when --fixed-opcode-count is specified."""
    fixed_opcode_count = config.getoption("fixed_opcode_count")
    if not fixed_opcode_count:
        # If --fixed-opcode-count is not specified, don't filter anything
        return

    filtered = []
    for item in items:
        if not item.get_closest_marker("benchmark"):
            continue

        repricing_marker = item.get_closest_marker("repricing")
        if not repricing_marker:
            continue

        if not repricing_marker.kwargs:
            filtered.append(item)
            continue

        if hasattr(item, "callspec"):
            if all(
                item.callspec.params.get(key) == value
                for key, value in repricing_marker.kwargs.items()
            ):
                filtered.append(item)
        else:
            if not repricing_marker.kwargs:
                filtered.append(item)

    items[:] = filtered


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate tests for the gas benchmark values and fixed opcode counts."""
    gas_benchmark_values = metafunc.config.getoption("gas_benchmark_value")
    fixed_opcode_counts = metafunc.config.getoption("fixed_opcode_count")

    # Ensure mutual exclusivity
    if gas_benchmark_values and fixed_opcode_counts:
        raise pytest.UsageError(
            "--gas-benchmark-values and --fixed-opcode-count are mutually exclusive. "
            "Use only one at a time."
        )

    if "gas_benchmark_value" in metafunc.fixturenames:
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
        # Only parametrize if test has repricing marker
        has_repricing = (
            metafunc.definition.get_closest_marker("repricing") is not None
        )
        if has_repricing:
            if fixed_opcode_counts:
                opcode_counts = [
                    int(x.strip()) for x in fixed_opcode_counts.split(",")
                ]
                opcode_count_parameters = [
                    pytest.param(
                        opcode_count,
                        id=f"opcount_{opcode_count}K",
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

    # If --fixed-opcode-count is specified, use high gas limit to avoid gas constraints
    if request.config.getoption("fixed_opcode_count"):
        return HIGH_GAS_LIMIT

    return EnvironmentDefaults.gas_limit


@pytest.fixture(scope="function")
def fixed_opcode_count(request: pytest.FixtureRequest) -> int | None:
    """Return a fixed opcode count for the current test, or None if not set."""
    if hasattr(request, "param"):
        return request.param

    return None


BENCHMARKING_MAX_GAS = 1_000_000_000_000
HIGH_GAS_LIMIT = 1_000_000_000


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
