"""Test that `fill` fails loudly when a collected test has no spec type."""

import textwrap

import pytest

test_module_plain = textwrap.dedent(
    """\
    def test_plain_pytest_test() -> None:
        assert True
    """
)

test_module_fillable = textwrap.dedent(
    """\
    import pytest

    from execution_testing import Environment

    @pytest.mark.valid_at("Istanbul")
    def test_fillable_test(state_test) -> None:
        state_test(env=Environment(), pre={}, post={}, tx=None)
    """
)

test_module_mixed = textwrap.dedent(
    """\
    import pytest

    from execution_testing import Environment

    @pytest.mark.valid_at("Istanbul")
    def test_mixed_fillable_test(state_test) -> None:
        state_test(env=Environment(), pre={}, post={}, tx=None)


    def test_mixed_plain_pytest_test() -> None:
        assert True
    """
)


def prepare_fill_module(pytester: pytest.Pytester, contents: str) -> str:
    """Write a single test module below `tests/` and return its path."""
    tests_dir = pytester.mkdir("tests")
    istanbul_tests_dir = tests_dir / "istanbul"
    istanbul_tests_dir.mkdir()
    dummy_dir = istanbul_tests_dir / "dummy_test_module"
    dummy_dir.mkdir()
    (dummy_dir / "test_dummy_collect.py").write_text(contents)

    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    return "tests/istanbul/dummy_test_module/"


def run_fill_collect_only(
    pytester: pytest.Pytester, contents: str
) -> pytest.RunResult:
    """Collect a single test module with the `fill` ini file."""
    return pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Istanbul",
        prepare_fill_module(pytester, contents),
        "--collect-only",
        "-q",
    )


def run_fill_with_workers(
    pytester: pytest.Pytester, contents: str, workers: str
) -> pytest.RunResult:
    """Fill a single test module with the given number of xdist workers."""
    return pytester.runpytest_subprocess(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Istanbul",
        "-n",
        workers,
        "--no-html",
        prepare_fill_module(pytester, contents),
    )


def test_plain_pytest_test_fails_collection(pytester: pytest.Pytester) -> None:
    """A test with no spec type fails collection instead of being dropped."""
    result = run_fill_collect_only(pytester, test_module_plain)

    assert result.ret not in (
        pytest.ExitCode.OK,
        pytest.ExitCode.NO_TESTS_COLLECTED,
        pytest.ExitCode.INTERNAL_ERROR,
    ), f"Expected a collection failure, got {result.ret}:\n{result.outlines}"
    assert not any("INTERNALERROR" in line for line in result.outlines), (
        f"Collection crashed:\n{result.outlines}"
    )
    assert any("test_plain_pytest_test" in line for line in result.outlines), (
        f"Expected the offending test to be named: {result.outlines}"
    )
    assert any("request no spec type" in line for line in result.outlines), (
        f"Expected the failure to name the problem: {result.outlines}"
    )


def test_fillable_test_is_still_collected(pytester: pytest.Pytester) -> None:
    """A module that only contains fillable tests is unaffected."""
    result = run_fill_collect_only(pytester, test_module_fillable)

    assert result.ret == pytest.ExitCode.OK, (
        f"Fill command failed:\n{result.outlines}"
    )
    assert any(
        "test_fillable_test[fork_Istanbul-state_test]" in line
        for line in result.outlines
    ), f"Expected the fillable test to be collected: {result.outlines}"


def test_mixed_module_reports_the_plain_test(
    pytester: pytest.Pytester,
) -> None:
    """A plain test in a mixed module is named in the failure."""
    result = run_fill_collect_only(pytester, test_module_mixed)

    assert result.ret not in (
        pytest.ExitCode.OK,
        pytest.ExitCode.NO_TESTS_COLLECTED,
    ), f"Expected a collection failure, got {result.ret}:\n{result.outlines}"
    assert any(
        "test_mixed_plain_pytest_test" in line for line in result.outlines
    ), f"Expected the offending test to be named: {result.outlines}"


@pytest.mark.parametrize("workers", ["0", "2"])
def test_plain_pytest_test_fails_with_workers(
    pytester: pytest.Pytester, workers: str
) -> None:
    """The failure is reported with and without xdist workers."""
    result = run_fill_with_workers(pytester, test_module_plain, workers)
    output = "\n".join(result.outlines + result.errlines)

    assert "INTERNALERROR" not in output, f"Collection crashed:\n{output}"
    assert result.ret not in (
        pytest.ExitCode.OK,
        pytest.ExitCode.INTERNAL_ERROR,
    ), f"Expected a failure, got {result.ret}:\n{output}"
    assert "test_plain_pytest_test" in output, (
        f"Expected the offending test to be named: {output}"
    )
