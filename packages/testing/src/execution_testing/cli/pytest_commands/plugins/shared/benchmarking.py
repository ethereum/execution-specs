"""The module contains the pytest hooks for the gas benchmark values."""

from abc import ABC, abstractmethod
from typing import ClassVar, List, Self

import pytest
from pydantic import RootModel

from execution_testing.test_types import Environment, EnvironmentDefaults
from execution_testing.tools import ParameterSet

from .address_stubs import AddressStubs
from .execute_fill import OpMode
from .fixture_output import (
    FORK_SUBDIR_PREFIX,
    SUBFOLDER_LEVEL_SEPARATOR,
    format_gas_limit_prefix,
)
from .helpers import is_benchmark_test


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
            "Benchmark outputs are grouped under "
            f"{FORK_SUBDIR_PREFIX}{{fork}}"
            f"{SUBFOLDER_LEVEL_SEPARATOR}XXXXM/ subdirectories."
        ),
    )
    benchmark_group.addoption(
        "--address-stubs",
        action="store",
        dest="address_stubs",
        default=None,
        type=AddressStubs.model_validate_json_or_file,
        help=(
            "Address stubs mapping stub names to on-chain addresses. "
            "Can be a JSON string or path to a JSON file."
        ),
    )
    benchmark_group.addoption(
        "--include-benchmark",
        action="store_true",
        dest="include_benchmark",
        default=False,
        help=(
            "Include tests/benchmark/ during collection even when no "
            "benchmark path is passed as a positional argument. Needed "
            "when collecting both tests/ and tests/benchmark/ in a single "
            "pytest invocation, since pytest's path deduplication drops "
            "the broader tests/ arg."
        ),
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Configure the fill and execute mode to benchmarking."""
    config.addinivalue_line(
        "markers",
        "repricing: Mark test as reference test for gas repricing analysis",
    )
    config.addinivalue_line(
        "markers",
        "stub_parametrize(param, prefix): parametrize with matching stubs",
    )

    gas_benchmark_values = GasBenchmarkValues.from_config(config)
    if gas_benchmark_values is not None:
        fixture_output = getattr(config, "fixture_output", None)
        if fixture_output is not None and fixture_output.is_stdout:
            raise pytest.UsageError(
                f"{GasBenchmarkValues.flag} cannot be used with "
                "--output=stdout. Use a directory output."
            )
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
        cls, _config: pytest.Config, value: str
    ) -> Self | None:
        """Given the parameter value and config, return the expected object."""
        return cls.model_validate(value.split(","))

    def get_test_parameters(self, _test_name: str) -> list[ParameterSet]:
        """Get benchmark values. All tests have the same list."""
        return [
            pytest.param(
                gas_value * 1_000_000,
                id=f"benchmark-gas-value_{gas_value}M",
                marks=[
                    pytest.mark.fixture_subfolder(
                        level=1,
                        prefix=format_gas_limit_prefix(gas_value, self.root),
                    ),
                ],
            )
            for gas_value in self.root
        ]


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Filter tests based on the repricing marker."""
    if not GasBenchmarkValues.from_config(config):
        return

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


@pytest.hookimpl(trylast=True)
def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate tests for the gas benchmark values."""
    parametrizer = GasBenchmarkValues.from_config(metafunc.config)
    if parametrizer:
        parametrizer.parametrize(metafunc)


@pytest.fixture(scope="function")
def gas_benchmark_value(request: pytest.FixtureRequest) -> int:
    """Return a single gas benchmark value for the current test."""
    if hasattr(request, "param"):
        return request.param

    return EnvironmentDefaults.gas_limit


BENCHMARKING_MAX_GAS = 1_000_000_000_000


@pytest.fixture
def genesis_environment(request: pytest.FixtureRequest) -> Environment:
    """Return an Environment with appropriate gas limit."""
    if is_benchmark_test(request):
        return Environment(gas_limit=BENCHMARKING_MAX_GAS)
    return Environment()


@pytest.fixture
def env(request: pytest.FixtureRequest) -> Environment:
    """Return an Environment with appropriate gas limit."""
    if is_benchmark_test(request):
        return Environment(gas_limit=BENCHMARKING_MAX_GAS)
    return Environment()
