"""Test the --include-benchmark flag gates tests/benchmark/ collection."""

import textwrap
from pathlib import Path

import pytest

REAL_BENCHMARK_CONFTEST = (
    Path(__file__).resolve().parents[9] / "tests" / "benchmark" / "conftest.py"
)
assert REAL_BENCHMARK_CONFTEST.is_file(), (
    f"Expected real benchmark conftest at {REAL_BENCHMARK_CONFTEST}; the "
    "repo layout likely changed and the parent traversal above is stale."
)

BENCHMARK_TEST_MODULE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import Environment

    @pytest.mark.valid_at("Prague")
    def test_dummy_benchmark(state_test) -> None:
        state_test(env=Environment(), pre={}, post={}, tx=None)
    """
)

CONSENSUS_TEST_MODULE = textwrap.dedent(
    """\
    import pytest

    from execution_testing import Environment

    @pytest.mark.valid_at("Prague")
    def test_dummy_consensus(state_test) -> None:
        state_test(env=Environment(), pre={}, post={}, tx=None)
    """
)


def _setup_benchmark_and_consensus_tests(
    pytester: pytest.Pytester,
) -> None:
    """Seed `tests/benchmark/` and `tests/prague/` test modules."""
    tests_dir = pytester.mkdir("tests")

    benchmark_dir = tests_dir / "benchmark"
    benchmark_dir.mkdir()
    (benchmark_dir / "conftest.py").write_text(
        REAL_BENCHMARK_CONFTEST.read_text()
    )
    benchmark_module = benchmark_dir / "dummy_test_module"
    benchmark_module.mkdir()
    (benchmark_module / "test_dummy_benchmark.py").write_text(
        BENCHMARK_TEST_MODULE
    )

    consensus_dir = tests_dir / "prague"
    consensus_dir.mkdir()
    consensus_module = consensus_dir / "dummy_test_module"
    consensus_module.mkdir()
    (consensus_module / "test_dummy_consensus.py").write_text(
        CONSENSUS_TEST_MODULE
    )

    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )


def test_default_excludes_benchmark(pytester: pytest.Pytester) -> None:
    """A plain `tests/` collection hides `tests/benchmark/`."""
    _setup_benchmark_and_consensus_tests(pytester)

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "tests/",
        "--collect-only",
        "-q",
    )

    assert result.ret == 0, f"Collection failed:\n{result.outlines}"
    assert any("test_dummy_consensus" in line for line in result.outlines)
    assert not any(
        "test_dummy_benchmark" in line for line in result.outlines
    ), f"Benchmark should be hidden by default:\n{result.outlines}"


def test_include_benchmark_flag_collects_both(
    pytester: pytest.Pytester,
) -> None:
    """`--include-benchmark` forces `tests/benchmark/` into collection."""
    _setup_benchmark_and_consensus_tests(pytester)

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Prague",
        "tests/",
        "--include-benchmark",
        "--collect-only",
        "-q",
    )

    assert result.ret == 0, f"Collection failed:\n{result.outlines}"
    assert any("test_dummy_consensus" in line for line in result.outlines)
    assert any("test_dummy_benchmark" in line for line in result.outlines), (
        f"Benchmark should be collected with the flag:\n{result.outlines}"
    )
