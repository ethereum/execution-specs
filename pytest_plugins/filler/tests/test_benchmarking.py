"""Test the benchmarking pytest plugin for gas benchmark values."""

import textwrap

import pytest

test_module_dummy = textwrap.dedent(
    """\
    import pytest

    from ethereum_test_tools import Environment

    @pytest.mark.valid_at("Istanbul")
    def test_dummy_benchmark_test(state_test, gas_benchmark_value):
        state_test(
            env=env,pre={},post={},tx=None)
    """
)

test_module_without_fixture = textwrap.dedent(
    """\
    import pytest

    from ethereum_test_tools import Environment

    @pytest.mark.valid_at("Istanbul")
    def test_dummy_no_benchmark_test(state_test):
        state_test(env=env, pre={}, post={}, tx=None)
    """
)


def setup_test_directory_structure(
    pytester: pytest.Pytester, test_content: str, test_filename: str
):
    """
    Set up the common test directory structure used across multiple tests.

    Args:
        pytester: The pytest Pytester fixture
        test_content: The content to write to the test file
        test_filename: The name of the test file to create

    Returns:
        The path to the created test module file

    """
    tests_dir = pytester.mkdir("tests")
    istanbul_tests_dir = tests_dir / "istanbul"
    istanbul_tests_dir.mkdir()
    dummy_dir = istanbul_tests_dir / "dummy_test_module"
    dummy_dir.mkdir()
    test_module = dummy_dir / test_filename
    test_module.write_text(test_content)

    pytester.copy_example(name="src/cli/pytest_commands/pytest_ini_files/pytest-fill.ini")

    return test_module


def test_gas_benchmark_option_added(pytester: pytest.Pytester):
    """Test that the --gas-benchmark-values option is properly added."""
    pytester.copy_example(name="src/cli/pytest_commands/pytest_ini_files/pytest-fill.ini")

    # Command: pytest -p pytest_plugins.filler.benchmarking --help
    result = pytester.runpytest("-c", "pytest-fill.ini", "--help")

    assert result.ret == 0
    assert any("--gas-benchmark-values" in line for line in result.outlines)
    assert any("Specify gas benchmark values for tests" in line for line in result.outlines)


def test_benchmarking_mode_configured_with_option(pytester: pytest.Pytester):
    """Test that fill_mode is set to BENCHMARKING when --gas-benchmark-values is used."""
    setup_test_directory_structure(pytester, test_module_dummy, "test_dummy_benchmark.py")

    # Test with gas benchmark values
    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Istanbul",
        "--gas-benchmark-values",
        "10,20,30",
        "tests/istanbul/dummy_test_module/",
        "--collect-only",
        "-q",
    )

    assert result.ret == 0
    assert any("9 tests collected" in line for line in result.outlines)
    # Check that the test names include the benchmark gas values
    assert any("benchmark-gas-value_10M" in line for line in result.outlines)
    assert any("benchmark-gas-value_20M" in line for line in result.outlines)
    assert any("benchmark-gas-value_30M" in line for line in result.outlines)


def test_benchmarking_mode_not_configured_without_option(pytester: pytest.Pytester):
    """Test that fill_mode is not set to BENCHMARKING when --gas-benchmark-values is not used."""
    setup_test_directory_structure(pytester, test_module_dummy, "test_dummy_benchmark.py")

    # Test without gas benchmark values
    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Istanbul",
        "tests/istanbul/dummy_test_module/",
        "--collect-only",
        "-q",
    )

    assert result.ret == 0
    # Should generate normal test variants (3) without parametrization
    assert any("3 tests collected" in line for line in result.outlines)
    assert not any("benchmark-gas-value_10M" in line for line in result.outlines)
    assert not any("benchmark-gas-value_20M" in line for line in result.outlines)
    assert not any("benchmark-gas-value_30M" in line for line in result.outlines)
