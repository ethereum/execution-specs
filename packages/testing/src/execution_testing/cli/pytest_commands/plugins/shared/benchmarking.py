"""The module contains the pytest hooks for the gas benchmark values."""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Dict, List, Self

import pytest
from pydantic import BaseModel, Field, RootModel

from execution_testing.test_types import Environment, EnvironmentDefaults
from execution_testing.tools import ParameterSet

from .execute_fill import OpMode


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command line options for benchmark tests."""
    benchmark_group = parser.getgroup(
        "benchmarking", "Arguments for benchmark test execution"
    )
    benchmark_group.addoption(
        GasBenchmarkValues.flag,
        action="store",
        dest=GasBenchmarkValues.parameter_name,
        type=str,
        default=None,
        help=(
            "Gas limits (in millions) for benchmark tests. "
            "Example: '100,500' runs tests with 100M and 500M gas. "
            f"Cannot be used with {OpcodeCountsConfig.flag}."
        ),
    )
    benchmark_group.addoption(
        OpcodeCountsConfig.flag,
        action="store",
        dest=OpcodeCountsConfig.parameter_name,
        type=str,
        default=None,
        nargs="?",
        const="",
        help=(
            "Opcode counts (in thousands) for benchmark tests. "
            "Example: '1,10,100' runs tests with 1K, 10K, 100K opcodes. "
            "Without value, uses .fixed_opcode_counts.json config. "
            f"Cannot be used with {GasBenchmarkValues.flag}."
        ),
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Configure the fill and execute mode to benchmarking."""
    config.addinivalue_line(
        "markers",
        "repricing: Mark test as reference test for gas repricing analysis",
    )

    # Ensure mutual exclusivity
    gas_benchmark_values = GasBenchmarkValues.from_config(config)
    fixed_opcode_count = OpcodeCountsConfig.from_config(config)
    if gas_benchmark_values is not None and fixed_opcode_count is not None:
        raise pytest.UsageError(
            f"{GasBenchmarkValues.flag} and --fixed-opcode-count are mutually exclusive. "
            "Use only one at a time."
        )

    if gas_benchmark_values is not None:
        config.op_mode = OpMode.BENCHMARKING  # type: ignore[attr-defined]


class BenchmarkParametrizer(ABC):
    """Object used to parametrize benchmark tests using parameters."""

    flag: ClassVar[str]
    parameter_name: ClassVar[str]
    config_field: ClassVar[str]

    @classmethod
    @abstractmethod
    def from_parameter_value(
        cls, config: pytest.Config, value: str
    ) -> Self | None:
        """Given the parameter value and config, return the expected object."""
        pass

    @classmethod
    def from_config(cls, config: pytest.Config) -> Self | None:
        """
        Parse the config the parametrizer configuration from the config.

        Return `None` if the parameter is not specified.
        """
        if hasattr(config, cls.config_field):
            return getattr(config, cls.config_field)

        parameter_value = config.getoption(cls.parameter_name)
        setattr(config, cls.config_field, None)

        if parameter_value is None:
            return None
        else:
            setattr(
                config,
                cls.config_field,
                cls.from_parameter_value(config, parameter_value),
            )
        return getattr(config, cls.config_field)

    @abstractmethod
    def get_test_parameters(self, test_name: str) -> list[ParameterSet]:
        """Get the parameters list for a given test."""
        pass

    def parametrize(self, metafunc: pytest.Metafunc) -> None:
        """Parametrize a test."""
        if self.parameter_name in metafunc.fixturenames:
            test_name = metafunc.function.__name__
            metafunc.parametrize(
                self.parameter_name,
                self.get_test_parameters(test_name),
                scope="function",
            )


class GasBenchmarkValues(RootModel, BenchmarkParametrizer):
    """Gas benchmark values configuration object."""

    root: List[int]

    flag: ClassVar[str] = "--gas-benchmark-values"
    config_field: ClassVar[str] = "_gas_benchmark_values_config"
    parameter_name: ClassVar[str] = "gas_benchmark_value"

    @classmethod
    def from_parameter_value(
        cls, config: pytest.Config, value: str
    ) -> Self | None:
        """Given the parameter value and config, return the expected object."""
        return cls.model_validate(value.split(","))

    def get_test_parameters(self, test_name: str) -> list[ParameterSet]:
        """Get benchmark values. All tests have the same list."""
        return [
            pytest.param(
                gas_value * 1_000_000,
                id=f"benchmark-gas-value_{gas_value}M",
            )
            for gas_value in self.root
        ]


class OpcodeCountsConfig(BaseModel, BenchmarkParametrizer):
    """Opcode counts configuration object."""

    scenario_configs: Dict[str, List[int]] = Field(default_factory=dict)
    default_counts: List[int] = Field(default_factory=lambda: [1])

    default_config_file_name: ClassVar[str] = ".fixed_opcode_counts.json"
    flag: ClassVar[str] = "--fixed-opcode-count"
    config_field: ClassVar[str] = "_opcode_counts_config"
    parameter_name: ClassVar[str] = "fixed_opcode_count"

    @classmethod
    def from_parameter_value(
        cls, config: pytest.Config, value: str
    ) -> Self | None:
        """Given the parameter value and config, return the expected object."""
        if value == "":
            default_file = Path(config.rootpath) / cls.default_config_file_name
            if default_file.exists():
                return cls.model_validate_json(default_file.read_bytes())
            else:
                pytest.UsageError(
                    "--fixed-opcode-count was provided without a value, but "
                    f"{cls.default_config_file_name} was not found. "
                    "Run 'uv run benchmark_parser' to generate it, or provide "
                    "explicit values (e.g., --fixed-opcode-count 1,10,100)."
                )
        return cls.model_validate({"default_counts": value.split(",")})

    def get_test_parameters(self, test_name: str) -> list[ParameterSet]:
        """
        Get opcode counts for a test using regex pattern matching.
        """
        counts = self.default_counts
        # Try exact match first (faster)
        if test_name in self.scenario_configs:
            counts = self.scenario_configs[test_name]
        else:
            # Try regex patterns
            for pattern, pattern_counts in self.scenario_configs.items():
                if pattern == test_name:
                    continue
                try:
                    if re.search(pattern, test_name):
                        counts = pattern_counts
                        break
                except re.error:
                    continue
        return [
            pytest.param(
                opcode_count,
                id=f"opcount_{opcode_count}K",
            )
            for opcode_count in counts
        ]


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Filter tests based on repricing marker."""
    gas_benchmark_value = GasBenchmarkValues.from_config(config)
    fixed_opcode_count = OpcodeCountsConfig.from_config(config)

    # Only filter if either benchmark option is provided
    if not gas_benchmark_value and not fixed_opcode_count:
        return

    # In --fixed-opcode-count mode, we only support tests that meet all of the following:
    #   - The test uses the benchmark_test fixture
    #   - The benchmark test uses a code generator
    #
    # Here we filter out tests that do not use the benchmark_test fixture.
    # Note: At this stage we cannot filter based on whether a code generator is used.
    if fixed_opcode_count is not None:
        filtered = []
        for item in items:
            if (
                hasattr(item, "fixturenames")
                and "benchmark_test" in item.fixturenames
            ):
                filtered.append(item)
        items[:] = filtered

    # Extract the specified flag from the command line.
    # If the `-m repricing` flag is not specified, or is negated,
    # we skip filtering tests by the repricing marker.
    markexpr = config.getoption("markexpr", "")
    if "repricing" not in markexpr or "not repricing" in markexpr:
        return

    filtered = []
    for item in items:
        # If the test does not have the repricing marker, skip it
        repricing_marker = item.get_closest_marker("repricing")
        if not repricing_marker:
            continue

        # If the test has the repricing marker but no specific kwargs,
        # include the entire parametrized test in the filtered list.
        if not repricing_marker.kwargs:
            filtered.append(item)
            continue

        # If the test has the repricing marker with specific kwargs,
        # filter the test cases according to those kwargs.
        if hasattr(item, "callspec"):
            if all(
                item.callspec.params.get(key) == value
                for key, value in repricing_marker.kwargs.items()
            ):
                filtered.append(item)

    items[:] = filtered


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate tests for the gas benchmark values and fixed opcode counts."""
    parametrizer = GasBenchmarkValues.from_config(
        metafunc.config
    ) or OpcodeCountsConfig.from_config(metafunc.config)

    if parametrizer:
        parametrizer.parametrize(metafunc)


@pytest.fixture(scope="function")
def gas_benchmark_value(request: pytest.FixtureRequest) -> int:
    """Return a single gas benchmark value for the current test."""
    if hasattr(request, "param"):
        return request.param

    # Only use high gas limit if --fixed-opcode-count flag was provided
    fixed_opcode_count = request.config.getoption("fixed_opcode_count")
    if fixed_opcode_count is not None:
        return BENCHMARKING_MAX_GAS

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
