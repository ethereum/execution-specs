"""The module contains the pytest hooks for the gas benchmark values."""

import json
import re
import warnings
from pathlib import Path
from typing import Any

import pytest

from execution_testing.test_types import Environment, EnvironmentDefaults

from .execute_fill import OpMode


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command line options for benchmark tests."""
    benchmark_group = parser.getgroup(
        "benchmarking", "Arguments for benchmark test execution"
    )
    benchmark_group.addoption(
        "--gas-benchmark-values",
        action="store",
        dest="gas_benchmark_value",
        type=str,
        default=None,
        help=(
            "Gas limits (in millions) for benchmark tests. "
            "Example: '100,500' runs tests with 100M and 500M gas. "
            "Cannot be used with --fixed-opcode-count."
        ),
    )
    benchmark_group.addoption(
        "--fixed-opcode-count",
        action="store",
        dest="fixed_opcode_count",
        type=str,
        default=None,
        nargs="?",
        const="",
        help=(
            "Opcode counts (in thousands) for benchmark tests. "
            "Example: '1,10,100' runs tests with 1K, 10K, 100K opcodes. "
            "Without value, uses .fixed_opcode_counts.json config. "
            "Cannot be used with --gas-benchmark-values."
        ),
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


def load_opcode_counts_config(
    config: pytest.Config,
) -> dict[str, Any] | None:
    """
    Load the opcode counts configuration from `.fixed_opcode_counts.json`.

    Returns dictionary with scenario_configs and default_counts, or None
    if not found.
    """
    config_file = Path(config.rootpath) / ".fixed_opcode_counts.json"

    if not config_file.exists():
        return None

    try:
        data = json.loads(config_file.read_text())
        return {
            "scenario_configs": data.get("scenario_configs", {}),
            "default_counts": [1],
        }
    except (json.JSONDecodeError, KeyError):
        return None


def get_opcode_counts_for_test(
    test_name: str,
    scenario_configs: dict[str, list[int]],
    default_counts: list[int],
) -> list[int]:
    """
    Get opcode counts for a test using regex pattern matching.
    """
    # Try exact match first (faster)
    if test_name in scenario_configs:
        return scenario_configs[test_name]

    # Try regex patterns
    for pattern, counts in scenario_configs.items():
        if pattern == test_name:
            continue
        try:
            if re.search(pattern, test_name):
                return counts
        except re.error:
            continue

    return default_counts


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Filter tests based on repricing marker when benchmark options are used."""
    gas_benchmark_value = config.getoption("gas_benchmark_value")
    fixed_opcode_count = config.getoption("fixed_opcode_count")

    # Only filter if either benchmark option is provided
    if not gas_benchmark_value and fixed_opcode_count is None:
        return

    # Load config data if --fixed-opcode-count flag provided without value
    if fixed_opcode_count == "":
        config_data = load_opcode_counts_config(config)
        if config_data:
            config._opcode_counts_config = config_data  # type: ignore[attr-defined]
        else:
            warnings.warn(
                "--fixed-opcode-count was provided without a value, but "
                ".fixed_opcode_counts.json was not found. "
                "Run 'uv run benchmark_parser' to generate it, or provide "
                "explicit values (e.g., --fixed-opcode-count 1,10,100).",
                UserWarning,
                stacklevel=1,
            )

    # Check if -m repricing marker filter was specified
    markexpr = config.getoption("markexpr", "")
    if "repricing" not in markexpr or "not repricing" in markexpr:
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
    fixed_opcode_counts_cli = metafunc.config.getoption("fixed_opcode_count")

    # Ensure mutual exclusivity
    if gas_benchmark_values and fixed_opcode_counts_cli:
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
        # Parametrize for any benchmark test when --fixed-opcode-count is provided
        if fixed_opcode_counts_cli is None:
            return

        opcode_counts_to_use = None

        if fixed_opcode_counts_cli:
            # CLI flag with value takes precedence
            opcode_counts_to_use = [
                int(x.strip()) for x in fixed_opcode_counts_cli.split(",")
            ]
        else:
            # Flag provided without value - load from config file
            # Check if config data was already loaded in pytest_collection_modifyitems
            config_data = getattr(
                metafunc.config, "_opcode_counts_config", None
            )

            # If not loaded yet (pytest_generate_tests runs first), load it now
            if config_data is None:
                config_data = load_opcode_counts_config(metafunc.config)
                if config_data:
                    metafunc.config._opcode_counts_config = config_data  # type: ignore[attr-defined]

            if config_data:
                # Look up opcode counts using regex pattern matching
                test_name = metafunc.function.__name__
                opcode_counts_to_use = get_opcode_counts_for_test(
                    test_name,
                    config_data.get("scenario_configs", {}),
                    config_data.get("default_counts", [1]),
                )

        # Parametrize if we have counts to use
        if opcode_counts_to_use:
            opcode_count_parameters = [
                pytest.param(
                    opcode_count,
                    id=f"opcount_{opcode_count}K",
                )
                for opcode_count in opcode_counts_to_use
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

    # Only use high gas limit if --fixed-opcode-count flag was provided
    fixed_opcode_count = request.config.getoption("fixed_opcode_count")
    if fixed_opcode_count is not None:
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
