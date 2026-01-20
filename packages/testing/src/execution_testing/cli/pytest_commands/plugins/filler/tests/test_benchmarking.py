"""Test the benchmarking pytest plugin for gas benchmark values."""

import textwrap
from pathlib import Path
from typing import List

import pytest

test_module_dummy = textwrap.dedent(
    """\
    import pytest
    from execution_testing import BenchmarkTestFiller, JumpLoopGenerator, Op

    @pytest.mark.valid_at("Prague")
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
    @pytest.mark.repricing
    def test_benchmark_with_repricing(benchmark_test: BenchmarkTestFiller) -> None:
        benchmark_test(
            target_opcode=Op.JUMPDEST,
            code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
        )

    @pytest.mark.valid_at("Prague")
    def test_benchmark_without_repricing(
            benchmark_test: BenchmarkTestFiller
        ) -> None:
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
    def test_with_gas_benchmark_value(state_test, gas_benchmark_value: int) -> None:
        # This test intentionally uses state_test instead of benchmark_test
        # to verify that --fixed-opcode-count filters it out
        state_test(pre={}, post={}, tx=None)

    @pytest.mark.valid_at("Prague")
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
    from execution_testing import BenchmarkTestFiller, ExtCallGenerator, Op

    @pytest.mark.valid_at("Prague")
    @pytest.mark.repricing(opcode=Op.ADD)
    @pytest.mark.parametrize("opcode", [Op.ADD, Op.SUB, Op.MUL])
    def test_parametrized_with_repricing_kwargs(
        benchmark_test: BenchmarkTestFiller, opcode
    ) -> None:
        benchmark_test(
            target_opcode=opcode,
            code_generator=ExtCallGenerator(attack_block=opcode),
        )

    @pytest.mark.valid_at("Prague")
    @pytest.mark.repricing
    @pytest.mark.parametrize("opcode", [Op.ADD, Op.SUB])
    def test_parametrized_with_repricing_no_kwargs(
        benchmark_test: BenchmarkTestFiller, opcode
    ) -> None:
        benchmark_test(
            target_opcode=opcode,
            code_generator=ExtCallGenerator(attack_block=opcode),
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
