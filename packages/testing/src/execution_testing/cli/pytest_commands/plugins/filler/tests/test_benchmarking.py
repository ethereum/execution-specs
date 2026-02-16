"""Test the benchmarking pytest plugin for gas benchmark values."""

import json
import textwrap
from pathlib import Path
from typing import List
from unittest.mock import MagicMock

import pytest

from execution_testing.cli.pytest_commands.plugins.shared.benchmarking import (
    OpcodeCountsConfig,
)

# EVM binary for tests that actually fill (not just collect)
BENCHMARK_EVM_T8N = "evmone-t8n"

test_module_dummy = textwrap.dedent(
    """\
    import pytest
    from execution_testing import BenchmarkTestFiller, JumpLoopGenerator, Op

    @pytest.mark.valid_at("Prague")
    @pytest.mark.benchmark
    def test_dummy_benchmark_test(benchmark_test: BenchmarkTestFiller) -> None:
        benchmark_test(
            target_opcode=Op.JUMPDEST,
            code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
        )
    """
)

test_module_without_fixture = textwrap.dedent(
    """\
    import pytest
    from execution_testing import BenchmarkTestFiller, JumpLoopGenerator, Op

    @pytest.mark.valid_at("Prague")
    @pytest.mark.benchmark
    def test_dummy_no_benchmark_test(benchmark_test: BenchmarkTestFiller) -> None:
        benchmark_test(
            target_opcode=Op.JUMPDEST,
            code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
        )
    """  # noqa: E501
)

test_module_with_repricing = textwrap.dedent(
    """\
    import pytest
    from execution_testing import BenchmarkTestFiller, JumpLoopGenerator, Op

    @pytest.mark.valid_at("Prague")
    @pytest.mark.benchmark
    @pytest.mark.repricing
    def test_benchmark_with_repricing(benchmark_test: BenchmarkTestFiller) -> None:
        benchmark_test(
            target_opcode=Op.JUMPDEST,
            code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
        )

    @pytest.mark.valid_at("Prague")
    @pytest.mark.benchmark
    def test_benchmark_without_repricing(benchmark_test: BenchmarkTestFiller) -> None:
        benchmark_test(
            target_opcode=Op.JUMPDEST,
            code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
        )
    """  # noqa: E501
)

test_module_without_benchmark_test_fixture = textwrap.dedent(
    """\
    import pytest
    from execution_testing import BenchmarkTestFiller, JumpLoopGenerator, Op

    @pytest.mark.valid_at("Prague")
    @pytest.mark.benchmark
    def test_with_gas_benchmark_value(state_test, gas_benchmark_value: int) -> None:
        # This test intentionally uses state_test instead of benchmark_test
        # to verify that --fixed-opcode-count filters it out
        state_test(pre={}, post={}, tx=None)

    @pytest.mark.valid_at("Prague")
    @pytest.mark.benchmark
    def test_with_benchmark_test(benchmark_test: BenchmarkTestFiller) -> None:
        benchmark_test(
            target_opcode=Op.JUMPDEST,
            code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
        )
    """  # noqa: E501
)

test_module_with_repricing_kwargs = textwrap.dedent(
    """\
    import pytest
    from execution_testing import BenchmarkTestFiller, JumpLoopGenerator, Op

    @pytest.mark.valid_at("Prague")
    @pytest.mark.benchmark
    @pytest.mark.repricing(opcode=Op.ADD)
    @pytest.mark.parametrize("opcode", [Op.ADD, Op.SUB, Op.MUL])
    def test_parametrized_with_repricing_kwargs(
        benchmark_test: BenchmarkTestFiller, opcode
    ) -> None:
        # Use JUMPDEST for benchmarking; opcode param is for filtering
        benchmark_test(
            target_opcode=Op.JUMPDEST,
            code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
        )

    @pytest.mark.valid_at("Prague")
    @pytest.mark.benchmark
    @pytest.mark.repricing
    @pytest.mark.parametrize("opcode", [Op.ADD, Op.SUB])
    def test_parametrized_with_repricing_no_kwargs(
        benchmark_test: BenchmarkTestFiller, opcode
    ) -> None:
        # Use JUMPDEST for benchmarking; opcode param is for filtering
        benchmark_test(
            target_opcode=Op.JUMPDEST,
            code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
        )
    """
)


def setup_test_directory_structure(
    pytester: pytest.Pytester, test_content: str, test_filename: str
) -> Path:
    """
    Set up the common test directory structure used across multiple tests.

    Args:
      pytester: The pytest Pytester fixture
      test_content: The content to write to the test file
      test_filename: The name of the test file to create

    Returns: The path to the created test module file

    """
    tests_dir = pytester.mkdir("tests")
    benchmark_tests_dir = tests_dir / "benchmark"
    benchmark_tests_dir.mkdir()
    dummy_dir = benchmark_tests_dir / "dummy_test_module"
    dummy_dir.mkdir()
    test_module = dummy_dir / test_filename
    test_module.write_text(test_content)

    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )

    return test_module


def test_gas_benchmark_option_added(pytester: pytest.Pytester) -> None:
    """Test that the --gas-benchmark-values option is properly added."""
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )

    # Equivalent to: fill --help
    result = pytester.runpytest("-c", "pytest-fill.ini", "--help")

    assert result.ret == 0
    assert any("--gas-benchmark-values" in line for line in result.outlines)
    assert any(
        "Gas limits (in millions) for benchmark tests" in line
        for line in result.outlines
    )


def test_benchmarking_mode_configured_with_option(
    pytester: pytest.Pytester,
) -> None:
    """
    Test that op_mode is set to BENCHMARKING when --gas-benchmark-values used.
    """
    setup_test_directory_structure(
        pytester, test_module_dummy, "test_dummy_benchmark.py"
    )

    # Test with gas benchmark values
    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "--gas-benchmark-values",
        "10,20,30",
        "tests/benchmark/dummy_test_module/",
        "--collect-only",
        "-q",
    )

    assert result.ret == 0
    assert any("6 tests collected" in line for line in result.outlines)
    # Check that the test names include the benchmark gas values
    assert any("benchmark-gas-value_10M" in line for line in result.outlines)
    assert any("benchmark-gas-value_20M" in line for line in result.outlines)
    assert any("benchmark-gas-value_30M" in line for line in result.outlines)


def test_benchmarking_mode_not_configured_without_option(
    pytester: pytest.Pytester,
) -> None:
    """
    Test that op_mode is not set to BENCHMARKING when --gas-benchmark-values
    not used.
    """
    setup_test_directory_structure(
        pytester, test_module_dummy, "test_dummy_benchmark.py"
    )

    # Test without gas benchmark values
    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "tests/benchmark/dummy_test_module/",
        "--collect-only",
        "-q",
    )

    assert result.ret == 0
    # Should generate normal test variants (2) without parametrization
    assert any("2 tests collected" in line for line in result.outlines)
    assert not any(
        "benchmark-gas-value_10M" in line for line in result.outlines
    )
    assert not any(
        "benchmark-gas-value_20M" in line for line in result.outlines
    )
    assert not any(
        "benchmark-gas-value_30M" in line for line in result.outlines
    )


@pytest.mark.parametrize(
    "benchmark_option,benchmark_args",
    [
        pytest.param(
            "--gas-benchmark-values",
            ["10"],
            id="gas-benchmark-values",
        ),
        pytest.param(
            "--fixed-opcode-count",
            ["1"],
            id="fixed-opcode-count",
        ),
    ],
)
def test_repricing_marker_filter_with_benchmark_options(
    pytester: pytest.Pytester,
    benchmark_option: str,
    benchmark_args: List[str],
) -> None:
    """
    Test that -m repricing filter works with both --gas-benchmark-values and
    --fixed-opcode-count options.

    When -m repricing is specified along with a benchmark option, only tests
    with the repricing marker should be collected.
    """
    setup_test_directory_structure(
        pytester, test_module_with_repricing, "test_repricing_filter.py"
    )

    # Test with -m repricing filter - should only collect repricing tests
    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        benchmark_option,
        *benchmark_args,
        "-m",
        "repricing",
        "tests/benchmark/dummy_test_module/",
        "--collect-only",
        "-q",
    )

    assert result.ret == 0
    # The repricing test should be collected
    assert any(
        "test_benchmark_with_repricing" in line for line in result.outlines
    )
    # The non-repricing test should NOT be collected
    assert not any(
        "test_benchmark_without_repricing" in line for line in result.outlines
    )


def test_fixed_opcode_count_filters_tests_without_benchmark_test_fixture(
    pytester: pytest.Pytester,
) -> None:
    """
    Test that --fixed-opcode-count filters out tests that don't use the
    benchmark_test fixture.

    Only tests with the benchmark_test fixture should be collected when
    --fixed-opcode-count is provided.
    """
    setup_test_directory_structure(
        pytester,
        test_module_without_benchmark_test_fixture,
        "test_fixture_filter.py",
    )

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "--fixed-opcode-count",
        "1",
        "tests/benchmark/dummy_test_module/",
        "--collect-only",
        "-q",
    )

    assert result.ret == 0
    # Test with benchmark_test fixture should be collected
    assert any("test_with_benchmark_test" in line for line in result.outlines)
    # Test with only gas_benchmark_value fixture should NOT be collected
    assert not any(
        "test_with_gas_benchmark_value" in line for line in result.outlines
    )


def test_repricing_marker_with_kwargs_filters_parametrized_tests(
    pytester: pytest.Pytester,
) -> None:
    """
    Test that repricing marker with kwargs filters parametrized tests to only
    include matching parameter combinations.

    When @pytest.mark.repricing(opcode=Op.ADD) is used, only test variants
    where opcode=Op.ADD should be collected.
    """
    setup_test_directory_structure(
        pytester,
        test_module_with_repricing_kwargs,
        "test_repricing_kwargs.py",
    )

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "--fixed-opcode-count",
        "1",
        "-m",
        "repricing",
        "tests/benchmark/dummy_test_module/",
        "--collect-only",
        "-q",
    )

    assert result.ret == 0
    # For repricing(opcode=Op.ADD), only ADD variant should be collected
    collected_lines = [
        line for line in result.outlines if "test_parametrized" in line
    ]

    # test_parametrized_with_repricing_kwargs should only have ADD variants
    # (multiple test types like blockchain_test and blockchain_test_engine)
    kwargs_test_lines = [
        line
        for line in collected_lines
        if "test_parametrized_with_repricing_kwargs" in line
    ]
    # All collected variants should be ADD only (no SUB or MUL)
    assert all("ADD" in line for line in kwargs_test_lines)
    assert not any("SUB" in line for line in kwargs_test_lines)
    assert not any("MUL" in line for line in kwargs_test_lines)

    # test_parametrized_with_repricing_no_kwargs: all variants (ADD and SUB)
    no_kwargs_test_lines = [
        line
        for line in collected_lines
        if "test_parametrized_with_repricing_no_kwargs" in line
    ]
    # Should have both ADD and SUB variants
    assert any("ADD" in line for line in no_kwargs_test_lines)
    assert any("SUB" in line for line in no_kwargs_test_lines)


def test_not_repricing_marker_negation(
    pytester: pytest.Pytester,
) -> None:
    """
    Test that -m 'not repricing' does not apply the repricing filter.

    When -m 'not repricing' is specified, the custom repricing filter should
    be skipped and pytest's built-in marker filtering should be used.
    """
    setup_test_directory_structure(
        pytester, test_module_with_repricing, "test_repricing_negation.py"
    )

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "--fixed-opcode-count",
        "1",
        "-m",
        "not repricing",
        "tests/benchmark/dummy_test_module/",
        "--collect-only",
        "-q",
    )

    assert result.ret == 0
    # The repricing test should NOT be collected (negated)
    assert not any(
        "test_benchmark_with_repricing" in line for line in result.outlines
    )
    # The non-repricing test should be collected
    assert any(
        "test_benchmark_without_repricing" in line for line in result.outlines
    )


def test_mutual_exclusivity_of_benchmark_options(
    pytester: pytest.Pytester,
) -> None:
    """
    Test that --gas-benchmark-values and --fixed-opcode-count cannot be used
    together.
    """
    setup_test_directory_structure(
        pytester, test_module_with_repricing, "test_mutual_exclusivity.py"
    )

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "--gas-benchmark-values",
        "10",
        "--fixed-opcode-count",
        "1",
        "tests/benchmark/dummy_test_module/",
        "--collect-only",
        "-q",
    )

    # Should fail with usage error
    assert result.ret != 0
    assert any(
        "mutually exclusive" in line
        for line in result.outlines + result.errlines
    )


def test_without_repricing_flag_collects_all_tests(
    pytester: pytest.Pytester,
) -> None:
    """
    Test that without -m repricing flag, both repricing and non-repricing
    tests are collected.
    """
    setup_test_directory_structure(
        pytester, test_module_with_repricing, "test_no_filter.py"
    )

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "--fixed-opcode-count",
        "1",
        "tests/benchmark/dummy_test_module/",
        "--collect-only",
        "-q",
    )

    assert result.ret == 0
    # Both tests should be collected
    assert any(
        "test_benchmark_with_repricing" in line for line in result.outlines
    )
    assert any(
        "test_benchmark_without_repricing" in line for line in result.outlines
    )


def test_fixed_opcode_count_exact_match_priority() -> None:
    """
    Exact match takes priority over regex patterns.

    When using a config file, patterns are matched against test names. An exact
    string match should take priority over a regex pattern that also matches.
    """
    config = OpcodeCountsConfig(
        scenario_configs={
            "test_dup": [10],
            "test_dup.*": [1],
        },
        default_counts=[99],
    )

    params = config.get_test_parameters("test_dup")
    assert params[0].values[0] == 10


def test_fixed_opcode_count_longest_pattern_wins() -> None:
    """
    Longest matching pattern takes priority.

    When using a config file, if multiple regex patterns match a test name, the
    longest pattern should win. This allows more specific patterns to override
    broader ones.
    """
    config = OpcodeCountsConfig(
        scenario_configs={
            "test_dup.*": [1],
            "test_dup.*DUP1.*": [5],
        },
        default_counts=[99],
    )

    # Longer pattern should win for DUP1
    params = config.get_test_parameters(
        "test_dup[fork_Prague-opcount_1K-opcode_DUP1]"
    )
    assert params[0].values[0] == 5

    # Shorter pattern should match for DUP2
    params = config.get_test_parameters(
        "test_dup[fork_Prague-opcount_1K-opcode_DUP2]"
    )
    assert params[0].values[0] == 1


def test_fixed_opcode_count_default_fallback() -> None:
    """
    Default counts are used when no pattern matches.

    When using a config file, if no pattern matches the test name, the
    default_counts should be used as a fallback.
    """
    config = OpcodeCountsConfig(
        scenario_configs={
            "test_dup.*": [1],
        },
        default_counts=[99],
    )

    params = config.get_test_parameters("test_other")
    assert params[0].values[0] == 99


def test_fixed_opcode_count_multiple_patterns() -> None:
    """
    Multiple overlapping patterns are handled correctly.

    Verifies that multiple overlapping patterns of different lengths are
    handled correctly. The most specific (longest) matching pattern wins.
    """
    config = OpcodeCountsConfig(
        scenario_configs={
            "test_.*": [1],
            "test_bitwise.*": [2],
            "test_bitwise.*AND.*": [3],
        },
        default_counts=[99],
    )

    # Most specific pattern should win
    params = config.get_test_parameters("test_bitwise[fork_Prague-opcode_AND]")
    assert params[0].values[0] == 3

    # Middle specificity
    params = config.get_test_parameters("test_bitwise[fork_Prague-opcode_OR]")
    assert params[0].values[0] == 2

    # Least specific
    params = config.get_test_parameters("test_other[fork_Prague]")
    assert params[0].values[0] == 1


@pytest.mark.parametrize(
    "cli_input,expected_counts",
    [
        ("1", [1]),  # Single integer
        ("1,2,3", [1, 2, 3]),  # Multiple integers
        ("0.5", [0.5]),  # Single float
        ("0.1,0.5,1", [0.1, 0.5, 1]),  # Multiple floats
        ("1,0.5,2", [1, 0.5, 2]),  # Mixed int/float
        # 10 mixed values
        (
            "0.1,0.25,0.5,0.75,1,1.25,1.5,1.75,2,3",
            [0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 3],
        ),
    ],
)
def test_fixed_opcode_count_valid_input(
    cli_input: str, expected_counts: list
) -> None:
    """
    Valid comma-separated numbers are accepted.

    The flag accepts comma-separated numbers (integers or floats) as default
    opcode counts. This test verifies valid inputs are parsed correctly.
    """
    mock_config = MagicMock()
    mock_config.rootpath = Path("/tmp")

    result = OpcodeCountsConfig.from_parameter_value(mock_config, cli_input)
    assert result is not None
    assert result.default_counts == expected_counts


def test_fixed_opcode_count_invalid_input() -> None:
    """
    Invalid values like test paths are rejected.

    The flag should reject invalid inputs like test paths that get accidentally
    consumed by argparse. This prevents confusing errors when users forget to
    specify opcode counts before the test path.
    """
    mock_config = MagicMock()
    mock_config.rootpath = Path("/tmp")

    with pytest.raises(pytest.UsageError) as exc_info:
        OpcodeCountsConfig.from_parameter_value(
            mock_config, "tests/benchmark/compute/test_foo.py"
        )

    assert "Invalid value for --fixed-opcode-count" in str(exc_info.value)


def test_fixed_opcode_count_missing_config() -> None:
    """
    Missing config file raises UsageError with helpful message.

    When used without arguments, it expects to load config from
    .fixed_opcode_counts.json. If the file is missing, a helpful UsageError
    should be raised explaining where to create the config file.
    """
    mock_config = MagicMock()
    mock_config.rootpath = Path("/nonexistent/path")

    with pytest.raises(pytest.UsageError) as exc_info:
        OpcodeCountsConfig.from_parameter_value(mock_config, "")

    assert ".fixed_opcode_counts.json" in str(exc_info.value)
    assert "was not found" in str(exc_info.value)


def test_fixed_opcode_count_float_values() -> None:
    """
    Float values are supported for sub-1K opcode iterations.

    For expensive precompiles that can't run 1000+ iterations within gas
    limits, float values like 0.001 (1 opcode) or 0.5 (500 opcodes) work.
    """
    config = OpcodeCountsConfig(
        scenario_configs={
            "test_precompile.*": [0.001, 0.01, 0.1],
        },
        default_counts=[1.0],
    )

    counts = config.get_opcode_counts("test_precompile_bn128")
    assert counts == [0.001, 0.01, 0.1]

    params = config.get_test_parameters("test_precompile_bn128")
    assert len(params) == 3
    assert params[0].id == "opcount_0.001K"
    assert params[1].id == "opcount_0.01K"
    assert params[2].id == "opcount_0.1K"


def test_fixed_opcode_count_invalid_regex_raises_error() -> None:
    """
    Invalid regex patterns raise an error.

    If a pattern in the config file contains invalid regex syntax, it should
    raise a ValueError with a helpful message indicating the invalid pattern.
    """
    config = OpcodeCountsConfig(
        scenario_configs={
            "[invalid(regex": [10.0],  # Invalid regex
            "test_valid.*": [5.0],
        },
        default_counts=[1.0],
    )

    # Should raise error when trying to match against invalid regex
    with pytest.raises(ValueError) as exc_info:
        config.get_opcode_counts("test_other")

    assert "Invalid regex pattern" in str(exc_info.value)
    assert "[invalid(regex" in str(exc_info.value)


@pytest.mark.parametrize(
    "config_counts,expected_tests,expected_ids",
    [
        pytest.param([1], 2, ["opcount_1"], id="single_int"),
        pytest.param(
            [1, 2, 3],
            6,
            ["opcount_1", "opcount_2", "opcount_3"],
            id="multiple_ints",
        ),
        pytest.param([0.5], 2, ["opcount_0.5"], id="single_float"),
        pytest.param(
            [0.5, 1, 2],
            6,
            ["opcount_0.5", "opcount_1", "opcount_2"],
            id="multiple_floats",
        ),
        pytest.param(
            [1, 0.5, 2],
            6,
            ["opcount_1", "opcount_0.5", "opcount_2"],
            id="mixed_int_float",
        ),
        pytest.param(
            [1, 2, 3, 5],
            8,
            ["opcount_1", "opcount_2", "opcount_3", "opcount_5"],
            id="four_ints",
        ),
    ],
)
def test_fixed_opcode_count_config_file_parametrized(
    pytester: pytest.Pytester,
    config_counts: list,
    expected_tests: int,
    expected_ids: list,
) -> None:
    """
    Config file opcode counts create correct test variants.

    The config file can specify single counts, multiple counts, or floats.
    Each should parametrize tests correctly.
    """
    setup_test_directory_structure(
        pytester, test_module_dummy, "test_config_counts.py"
    )

    config_file = pytester.path / ".fixed_opcode_counts.json"
    config_file.write_text(
        json.dumps(
            {
                "scenario_configs": {
                    "test_dummy_benchmark_test.*": config_counts
                }
            }
        )
    )

    # Use subprocess mode to isolate each parametrized inner session.
    # pytester defaults to in-process mode, which shares the Python
    # interpreter across all inner sessions in the same test run.
    # Pydantic's ModelMetaclass caches __init__ wrappers for dynamically
    # created classes (like BaseTestWrapper); when a second in-process
    # session creates a new BaseTestWrapper, the cached wrapper re-invokes
    # __init__ re-entrantly, causing generate() to run twice per test and
    # doubling the opcode count. This is strictly a pytester/in-process
    # artifact — normal `fill` runs are unaffected because each fill
    # invocation is a fresh Python process.
    #
    # Place --fixed-opcode-count after test path to avoid argparse consuming
    # the path as the option value (nargs='?' behavior)
    result = pytester.runpytest_subprocess(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "tests/benchmark/dummy_test_module/",
        f"--evm-bin={BENCHMARK_EVM_T8N}",
        "--fixed-opcode-count",
        "-v",
    )

    assert result.ret == 0
    # Check expected number of tests (2 test types * len(counts))
    assert any(f"{expected_tests} passed" in line for line in result.outlines)
    # Check opcode count IDs are present
    for expected_id in expected_ids:
        assert any(expected_id in line for line in result.outlines)


# Test module with parametrized test for per-parameter pattern matching
test_module_parametrized = textwrap.dedent(
    """\
    import pytest
    from execution_testing import BenchmarkTestFiller, JumpLoopGenerator, Op

    @pytest.mark.valid_at("Prague")
    @pytest.mark.benchmark
    @pytest.mark.parametrize("size", [0, 32, 256, 1024])
    def test_parametrized_benchmark(
        benchmark_test: BenchmarkTestFiller, size: int
    ) -> None:
        benchmark_test(
            target_opcode=Op.JUMPDEST,
            code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
        )
    """
)


@pytest.mark.parametrize(
    "config,expected_test_ids",
    [
        # Single count per parameter - different counts for different sizes
        pytest.param(
            {
                "test_parametrized_benchmark.*size_0.*": [5],
                "test_parametrized_benchmark.*size_256.*": [3],
                "test_parametrized_benchmark.*size_1024.*": [2],
            },
            [
                # size_0->5, size_32->default(1), size_256->3, size_1024->2
                "size_0-opcount_5",
                "size_32-opcount_1",
                "size_256-opcount_3",
                "size_1024-opcount_2",
            ],
            id="single_count_per_param",
        ),
        # Multiple counts per parameter (floats and ints)
        pytest.param(
            {
                "test_parametrized_benchmark.*size_0.*": [0.5, 1, 2],
                "test_parametrized_benchmark.*size_1024.*": [0.5, 0.75],
            },
            [
                # size_0->[0.5,1,2], size_32->default[1], size_1024->[0.5,0.75]
                "size_0-opcount_0.5",
                "size_0-opcount_1",
                "size_0-opcount_2",
                "size_32-opcount_1",
                "size_256-opcount_1",
                "size_1024-opcount_0.5",
                "size_1024-opcount_0.75",
            ],
            id="multiple_counts_per_param",
        ),
        # Per-param patterns with test_.* fallback for unmatched params
        pytest.param(
            {
                "test_parametrized_benchmark.*size_0.*": [5],
                "test_parametrized_benchmark.*size_1024.*": [10],
                "test_.*": [2, 3],  # Fallback for size_32, size_256
            },
            [
                # size_0 -> [5] (specific), size_32 -> [2,3] (fallback),
                # size_256 -> [2,3] (fallback), size_1024 -> [10] (specific)
                "size_0-opcount_5",
                "size_32-opcount_2",
                "size_32-opcount_3",
                "size_256-opcount_2",
                "size_256-opcount_3",
                "size_1024-opcount_10",
            ],
            id="per_param_with_fallback",
        ),
        # All params same counts via broad pattern
        pytest.param(
            {
                "test_parametrized_benchmark.*": [1, 2, 3],
            },
            [
                # All sizes get [1, 2, 3]
                "size_0-opcount_1",
                "size_0-opcount_2",
                "size_0-opcount_3",
                "size_32-opcount_1",
                "size_1024-opcount_3",
            ],
            id="all_same_counts",
        ),
    ],
)
def test_fixed_opcode_count_per_parameter_patterns(
    pytester: pytest.Pytester,
    config: dict,
    expected_test_ids: List[str],
) -> None:
    """
    Per-parameter opcode count patterns work correctly.

    Patterns like "test_foo.*size_256.*" should match tests with that specific
    parameter value and apply the corresponding opcode counts.
    """
    setup_test_directory_structure(
        pytester, test_module_parametrized, "test_param_benchmark.py"
    )

    config_file = pytester.path / ".fixed_opcode_counts.json"
    config_file.write_text(json.dumps({"scenario_configs": config}))

    # Subprocess mode: avoids Pydantic metaclass cache pollution across
    # in-process pytester sessions (see comment in
    # test_fixed_opcode_count_config_file_parametrized).
    result = pytester.runpytest_subprocess(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "tests/benchmark/dummy_test_module/",
        f"--evm-bin={BENCHMARK_EVM_T8N}",
        "--fixed-opcode-count",
        "-v",
    )

    assert result.ret == 0

    # Verify expected test IDs are present
    output = "\n".join(result.outlines)
    for expected_id in expected_test_ids:
        assert expected_id in output, (
            f"Expected '{expected_id}' in output but not found.\n"
            f"Output:\n{output}"
        )


def test_cli_mode_ignores_per_parameter_patterns(
    pytester: pytest.Pytester,
) -> None:
    """
    CLI mode applies same counts to all parameters.

    When using --fixed-opcode-count=1,5 (explicit CLI values), all test
    variants should get the same opcode counts regardless of their parameters.
    This verifies CLI mode doesn't accidentally use per-parameter matching.
    """
    setup_test_directory_structure(
        pytester, test_module_parametrized, "test_cli_mode.py"
    )

    # Subprocess mode: avoids Pydantic metaclass cache pollution across
    # in-process pytester sessions (see comment in
    # test_fixed_opcode_count_config_file_parametrized).
    result = pytester.runpytest_subprocess(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "--fixed-opcode-count=1,5",
        "tests/benchmark/dummy_test_module/",
        f"--evm-bin={BENCHMARK_EVM_T8N}",
        "-v",
    )

    assert result.ret == 0
    output = "\n".join(result.outlines)

    # All size variants should have both opcount_1 and opcount_5
    for size in ["size_0", "size_32", "size_256", "size_1024"]:
        assert (
            f"{size}-opcount_1.0K" in output or f"{size}-opcount_1K" in output
        ), f"Expected {size} with opcount_1 in output"
        assert (
            f"{size}-opcount_5.0K" in output or f"{size}-opcount_5K" in output
        ), f"Expected {size} with opcount_5 in output"
