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


def run_fill_collect_only(
    pytester: pytest.Pytester, contents: str
) -> pytest.RunResult:
    """Collect a single test module with the `fill` ini file."""
    tests_dir = pytester.mkdir("tests")
    istanbul_tests_dir = tests_dir / "istanbul"
    istanbul_tests_dir.mkdir()
    dummy_dir = istanbul_tests_dir / "dummy_test_module"
    dummy_dir.mkdir()
    (dummy_dir / "test_dummy_collect.py").write_text(contents)

    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )

    return pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Istanbul",
        "tests/istanbul/dummy_test_module/",
        "--collect-only",
        "-q",
    )


def test_plain_pytest_test_fails_loudly(pytester: pytest.Pytester) -> None:
    """A test with no spec type aborts the session instead of being dropped."""
    result = run_fill_collect_only(pytester, test_module_plain)

    assert result.ret == pytest.ExitCode.USAGE_ERROR, (
        f"Expected a usage error, got {result.ret}:\n{result.outlines}"
    )
    assert not any("INTERNALERROR" in line for line in result.outlines), (
        f"Collection crashed:\n{result.outlines}"
    )
    assert any(
        "ERROR: Tests without a spec type" in line for line in result.outlines
    ), f"Expected an error report: {result.outlines}"
    assert any("test_plain_pytest_test" in line for line in result.outlines), (
        f"Expected the offending test to be named: {result.outlines}"
    )
    assert any("must request one of" in line for line in result.outlines), (
        f"Expected the report to list the spec types: {result.outlines}"
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
    """A plain test in a mixed module is named in the error report."""
    result = run_fill_collect_only(pytester, test_module_mixed)

    assert result.ret == pytest.ExitCode.USAGE_ERROR, (
        f"Expected a usage error, got {result.ret}:\n{result.outlines}"
    )
    assert any(
        "test_mixed_plain_pytest_test" in line for line in result.outlines
    ), f"Expected the offending test to be named: {result.outlines}"
