"""Test the benchmarking pytest plugin for gas benchmark values."""

import json
import os
import textwrap
from pathlib import Path
from typing import List

import pytest

from execution_testing.cli.pytest_commands.plugins.shared.fixture_output import (  # noqa: E501
    FORK_SUBDIR_PREFIX,
    format_fork_subdir,
)

# EVM binary for fill tests. Unset (or empty) -> the in-repo EELS t8n
# (fill's default when --evm-bin is omitted). Set EVM_BIN to fill
# against a specific binary, e.g. geth's `evm`.
BENCHMARK_EVM_T8N = os.environ.get("EVM_BIN") or None


def _evm_bin_args() -> List[str]:
    """Return `--evm-bin` args, or none to use fill's EELS default."""
    if BENCHMARK_EVM_T8N is None:
        return []
    return [f"--evm-bin={BENCHMARK_EVM_T8N}"]


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
    def test_benchmark_without_repricing(benchmark_test: BenchmarkTestFiller) -> None:
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


def test_benchmark_gas_values_split_into_subdirs(
    pytester: pytest.Pytester, tmp_path: Path
) -> None:
    """Ensure per-gas-limit outputs are written to separate directories."""
    benchmark_marked_module = textwrap.dedent(
        """\
        import pytest
        from execution_testing import (
            BenchmarkTestFiller,
            JumpLoopGenerator,
            Op,
        )

        @pytest.mark.valid_at("Prague")
        def test_dummy_benchmark_test(
            benchmark_test: BenchmarkTestFiller,
        ) -> None:
            benchmark_test(
                target_opcode=Op.JUMPDEST,
                code_generator=JumpLoopGenerator(attack_block=Op.JUMPDEST),
            )
        """
    )
    setup_test_directory_structure(
        pytester, benchmark_marked_module, "test_dummy_benchmark.py"
    )

    output_dir = tmp_path / "fixtures"
    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "--gas-benchmark-values",
        "1,2",
        "-m",
        "blockchain_test and primary_format",
        "--no-html",
        "--skip-index",
        f"--output={output_dir}",
        "tests/benchmark/dummy_test_module/",
        "-q",
    )

    assert result.ret == 0, f"Fill command failed:\n{result.outlines}"

    gas_1_subdir = format_fork_subdir("Prague", "0001M")
    gas_2_subdir = format_fork_subdir("Prague", "0002M")
    gas_1_dir = output_dir / "blockchain_tests" / gas_1_subdir
    gas_2_dir = output_dir / "blockchain_tests" / gas_2_subdir
    assert gas_1_dir.exists()
    assert gas_2_dir.exists()

    gas_1_files = list(gas_1_dir.rglob("*.json"))
    gas_2_files = list(gas_2_dir.rglob("*.json"))
    assert gas_1_files, f"Expected fixtures under {gas_1_subdir}"
    assert gas_2_files, f"Expected fixtures under {gas_2_subdir}"

    def _assert_keys(
        files: list[Path], expected: str, unexpected: str
    ) -> None:
        for file_path in files:
            data = json.loads(file_path.read_text())
            assert data, f"Empty fixture file: {file_path}"
            for key in data.keys():
                assert expected in key, (
                    f"Expected {expected} in key {key} ({file_path})"
                )
                assert unexpected not in key, (
                    f"Unexpected {unexpected} in key {key} ({file_path})"
                )

    _assert_keys(gas_1_files, "benchmark-gas-value_1M", "2M")
    _assert_keys(gas_2_files, "benchmark-gas-value_2M", "1M")

    root_json = []
    for json_path in output_dir.rglob("*.json"):
        rel = json_path.relative_to(output_dir)
        if not rel.parts:
            continue
        if rel.parts[0] == ".meta":
            continue
        if rel.parts[0] in (
            "blockchain_tests",
            "blockchain_tests_engine",
            "blockchain_tests_engine_x",
        ):
            continue
        root_json.append(json_path)
    assert not root_json, f"Unexpected root JSON files: {root_json}"

    top_level_for_dirs = [
        p
        for p in output_dir.iterdir()
        if p.is_dir() and p.name.startswith(FORK_SUBDIR_PREFIX)
    ]
    assert not top_level_for_dirs, (
        f"Unexpected top-level {FORK_SUBDIR_PREFIX} dirs: {top_level_for_dirs}"
    )


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


def test_repricing_marker_filter_with_benchmark_options(
    pytester: pytest.Pytester,
) -> None:
    """
    Test that -m repricing filter works with --gas-benchmark-values.

    When -m repricing is specified along with --gas-benchmark-values, only
    tests with the repricing marker should be collected.
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
        "--gas-benchmark-values",
        "10",
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
        "--gas-benchmark-values",
        "10",
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
        "--gas-benchmark-values",
        "10",
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
        "--gas-benchmark-values",
        "10",
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


def test_consensus_fixtures_split_by_fork(
    pytester: pytest.Pytester, tmp_path: Path
) -> None:
    """Ensure non-benchmark fixtures are split into fork subdirectories."""
    consensus_module = textwrap.dedent(
        """\
        import pytest
        from execution_testing import Transaction

        @pytest.mark.valid_from("Prague")
        def test_fork_split_example(state_test, pre) -> None:
            tx = Transaction(
                to=0, gas_limit=21_000, sender=pre.fund_eoa()
            ).with_signature_and_sender()
            state_test(pre=pre, post={}, tx=tx)
        """
    )
    tests_dir = pytester.mkdir("tests")
    test_dir = tests_dir / "prague" / "dummy_split"
    test_dir.mkdir(parents=True)
    test_file = test_dir / "test_fork_split.py"
    test_file.write_text(consensus_module)

    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )

    output_dir = tmp_path / "fixtures"
    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--from=Prague",
        "--until=Osaka",
        "-m",
        "not blockchain_test_engine",
        "--no-html",
        "--skip-index",
        f"--output={output_dir}",
        str(test_file),
        "-q",
    )

    assert result.ret == 0, f"Fill command failed:\n{result.outlines}"

    prague_subdir = format_fork_subdir("Prague")
    osaka_subdir = format_fork_subdir("Osaka")

    # Verify fork subdirs exist under state_tests
    state_tests_dir = output_dir / "state_tests"
    prague_dir = state_tests_dir / prague_subdir
    osaka_dir = state_tests_dir / osaka_subdir
    assert prague_dir.exists(), (
        f"Expected {prague_subdir}/ under {state_tests_dir}"
    )
    assert osaka_dir.exists(), (
        f"Expected {osaka_subdir}/ under {state_tests_dir}"
    )

    prague_files = list(prague_dir.rglob("*.json"))
    osaka_files = list(osaka_dir.rglob("*.json"))
    assert prague_files, f"Expected fixtures under {prague_subdir}/"
    assert osaka_files, f"Expected fixtures under {osaka_subdir}/"

    # Verify each file contains only the expected fork's fixtures
    for file_path in prague_files:
        data = json.loads(file_path.read_text())
        for key in data:
            assert "fork_Prague" in key, (
                f"Expected fork_Prague in key {key} ({file_path})"
            )
            assert "fork_Osaka" not in key, (
                f"Unexpected fork_Osaka in key {key} ({file_path})"
            )

    for file_path in osaka_files:
        data = json.loads(file_path.read_text())
        for key in data:
            assert "fork_Osaka" in key, (
                f"Expected fork_Osaka in key {key} ({file_path})"
            )
            assert "fork_Prague" not in key, (
                f"Unexpected fork_Prague in key {key} ({file_path})"
            )
