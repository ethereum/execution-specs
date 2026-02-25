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
from .fixture_output import (
    FORK_SUBDIR_PREFIX,
    SUBFOLDER_LEVEL_SEPARATOR,
    format_gas_limit_prefix,
)


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
            f"{SUBFOLDER_LEVEL_SEPARATOR}XXXXM/ subdirectories. "
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
            "Granularity rules (for ≤10%% CALL overhead): "
            "cheap ops (1-2 gas): integers only, no sub-1K; "
            "medium ops (3-5 gas): 0.5 increments, min 0.5K; "
            "expensive ops (6+ gas): 0.25 increments, min 0.25K; "
            "very expensive (100+ gas): 0.25 increments, min 0.01K. "
            "Example: '0.5,1,2' runs 500, 1K, 2K opcodes. "
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
            f"{GasBenchmarkValues.flag} and --fixed-opcode-count are mutually "
            "exclusive. Use only one at a time."
        )

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


class OpcodeCountsConfig(BaseModel, BenchmarkParametrizer):
    """Opcode counts configuration object."""

    scenario_configs: Dict[str, List[float]] = Field(default_factory=dict)
    default_counts: List[float] = Field(default_factory=lambda: [1.0])
    uses_config_file: bool = Field(default=False)

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
                data = default_file.read_bytes()
                instance = cls.model_validate_json(data)
                instance.uses_config_file = True
                return instance
            else:
                raise pytest.UsageError(
                    "--fixed-opcode-count was provided without a value, but "
                    f"{cls.default_config_file_name} was not found. "
                    "Run 'uv run benchmark_parser' to generate it, or provide "
                    "explicit values (e.g., --fixed-opcode-count 1,10,100)."
                )
        # Validate that value looks like comma-separated numbers (int or float)
        # This catches the case where argparse greedily consumes a test path
        parts = value.split(",")

        def is_number(s: str) -> bool:
            try:
                float(s.strip())
                return True
            except ValueError:
                return False

        if not all(is_number(part) for part in parts):
            raise pytest.UsageError(
                f"Invalid value for --fixed-opcode-count: '{value}'. "
                "Expected comma-separated numbers (e.g., '1,10,100' or "
                "'0.25,0.5,1') or no value to use the config file. "
                "If providing a value, use --fixed-opcode-count=VALUE "
                "syntax to avoid argparse consuming test paths as the value."
            )
        return cls.model_validate(
            {"default_counts": parts, "uses_config_file": False}
        )

    def get_opcode_counts(self, test_name: str) -> list[float]:
        """
        Get opcode counts for a test using pattern matching.

        Matching priority:
        1. Exact match in scenario_configs
        2. Regex pattern match (longest pattern wins for specificity)
        3. Default counts as fallback

        Example with config:
            {"test_dup": [10], "test_dup.*": [1], "test_dup.*DUP1.*": [5]}

        - "test_dup" -> [10] (exact match)
        - "test_dup[fork_Prague-opcode_DUP1]" -> [5] (longest pattern matches)
        - "test_dup[fork_Prague-opcode_DUP2]" -> [1] (matches "test_dup.*")
        - "test_other" -> default_counts (no match)

        Note: In config file mode, test names don't have opcount yet when this
        is called - we look up the count first, then add it to the test name.
        """
        counts = self.default_counts

        if test_name in self.scenario_configs:
            counts = self.scenario_configs[test_name]
        else:
            matches: list[tuple[str, list[float]]] = []
            for pattern, pattern_counts in self.scenario_configs.items():
                if pattern == test_name:
                    continue
                try:
                    if re.search(pattern, test_name):
                        matches.append((pattern, pattern_counts))
                except re.error as e:
                    raise ValueError(
                        f"Invalid regex pattern '{pattern}' in config: {e}"
                    ) from e

            if matches:
                matches.sort(key=lambda x: len(x[0]), reverse=True)
                counts = matches[0][1]

        return counts

    def get_test_parameters(self, test_name: str) -> list[ParameterSet]:
        """Get opcode counts as pytest parameters."""
        # Deduplicate while preserving order
        unique_counts = list(dict.fromkeys(self.get_opcode_counts(test_name)))
        return [
            pytest.param(
                opcode_count,
                id=f"opcount_{opcode_count}K",
                marks=[
                    pytest.mark.fixture_subfolder(
                        level=1,
                        prefix=f"opcount_{opcode_count}K",
                    ),
                ],
            )
            for opcode_count in unique_counts
        ]

    def parametrize(self, metafunc: pytest.Metafunc) -> None:
        """
        Parametrize a test with opcode counts.

        In config file mode with existing parametrizations (metafunc._calls),
        generates opcode counts per-parameter by matching patterns against
        simulated test IDs built from existing params.

        In CLI mode (explicit counts), uses function name for pattern matching.
        """
        # Check for direct or indirect use of fixed_opcode_count.
        # The benchmark_test fixture depends on fixed_opcode_count, so if the
        # test uses benchmark_test, we need to parametrize fixed_opcode_count.
        if self.parameter_name not in metafunc.fixturenames:
            if "benchmark_test" not in metafunc.fixturenames:
                return
            # benchmark_test uses fixed_opcode_count - add it to fixtures
            metafunc.fixturenames.append(self.parameter_name)

        test_name = metafunc.function.__name__

        if (
            self.uses_config_file
            and hasattr(metafunc, "_calls")
            and metafunc._calls
        ):
            # Config file mode with existing parametrizations:
            # Build simulated IDs from existing params and match patterns
            self._parametrize_with_existing_params(metafunc, test_name)
        else:
            # Config file mode (no existing params) or CLI mode:
            # match against function name
            metafunc.parametrize(
                self.parameter_name,
                self.get_test_parameters(test_name),
                scope="function",
            )

    def _parametrize_with_existing_params(
        self, metafunc: pytest.Metafunc, test_name: str
    ) -> None:
        """
        Parametrize opcode counts based on existing test parameters.

        For each existing parameter combination in metafunc._calls, build a
        simulated test ID and match patterns to get the appropriate counts.

        We collect ALL unique counts across all parameter combinations and add
        them as a simple parametrization. This creates all combinations
        (cartesian product). Unwanted combinations filtered in modifyitems.
        """
        # Collect opcode counts for each call (indexed by position)
        all_unique_counts: set[float] = set()

        for call in metafunc._calls:
            # Build simulated test ID using call.id (already formatted)
            # Format: test_name[fork_<FORK>-<fixture_format>-<user_params>]
            simulated_id = f"{test_name}[{call.id}]" if call.id else test_name

            # Get opcode counts for this simulated ID and add to unique set
            counts = self.get_opcode_counts(simulated_id)
            all_unique_counts.update(counts)

        # Add all unique counts as simple parametrization (multiplies with
        # existing). Unwanted combinations filtered in collection_modifyitems
        metafunc.parametrize(
            self.parameter_name,
            [
                pytest.param(count, id=f"opcount_{count}K")
                for count in sorted(all_unique_counts)
            ],
            scope="function",
        )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Filter tests based on repricing marker and opcode count patterns."""
    gas_benchmark_value = GasBenchmarkValues.from_config(config)
    fixed_opcode_count = OpcodeCountsConfig.from_config(config)

    # Only filter if either benchmark option is provided
    if not gas_benchmark_value and not fixed_opcode_count:
        return

    # In --fixed-opcode-count mode, we only support tests that meet all of
    # the following:
    #   - The test uses the benchmark_test fixture
    #   - The benchmark test uses a code generator
    #
    # Here we filter out tests that do not use the benchmark_test fixture.
    # Note: At this stage we cannot filter based on whether a code generator
    # is used.
    if fixed_opcode_count is not None:
        filtered = []
        for item in items:
            if (
                hasattr(item, "fixturenames")
                and "benchmark_test" in item.fixturenames
            ):
                filtered.append(item)
        items[:] = filtered

        # Filter per-parameter opcode counts if using config file mode
        if fixed_opcode_count.uses_config_file:
            _filter_opcode_count_combinations(items, fixed_opcode_count)

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


def _filter_opcode_count_combinations(
    items: list[pytest.Item], opcode_config: "OpcodeCountsConfig"
) -> None:
    """
    Filter test items to only keep valid opcode count combinations.

    When using config file mode with per-parameter patterns, we generate all
    combinations (cartesian product) in pytest_generate_tests. Here we filter
    out combinations where the opcode count doesn't match the pattern for
    that specific parameter combination.
    """
    filtered = []

    for item in items:
        if not hasattr(item, "callspec"):
            filtered.append(item)
            continue

        params = item.callspec.params
        opcode_count = params.get(OpcodeCountsConfig.parameter_name)

        if opcode_count is None:
            filtered.append(item)
            continue

        # Build simulated test ID WITHOUT the opcode count for pattern matching
        # Format: test_func[fork_X-fixture_format-params-opcount_Y]
        # Target: test_func[fork_X-fixture_format-params]
        test_name = item.name

        # Remove the opcode count part from the test ID for pattern matching
        # Pattern: -opcount_X.XK or -opcount_XK at the end before ]
        simulated_id = re.sub(r"-opcount_[\d.]+K\]$", "]", test_name)

        # Get valid counts for this parameter combination
        valid_counts = opcode_config.get_opcode_counts(simulated_id)

        # Keep item only if its opcode count is valid for this combination
        if opcode_count in valid_counts:
            filtered.append(item)

    items[:] = filtered


@pytest.hookimpl(trylast=True)
def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """
    Generate tests for the gas benchmark values and fixed opcode counts.

    Uses trylast=True to run after other parametrizations so we can access
    existing parameters in metafunc._calls for pattern matching.
    """
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
