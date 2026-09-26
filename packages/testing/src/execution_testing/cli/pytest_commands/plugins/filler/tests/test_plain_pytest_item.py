"""Test that `fill` deselects test items that request no spec type."""

import textwrap

import pytest

test_module_plain = textwrap.dedent(
    """\
    def test_plain_pytest_test() -> None:
        assert True
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


def test_plain_pytest_test_is_deselected(pytester: pytest.Pytester) -> None:
    """A test requesting no spec type is deselected, not a crash."""
    result = run_fill_collect_only(pytester, test_module_plain)

    # Every collected item is deselected, so pytest reports no tests collected
    # instead of aborting the session with an INTERNALERROR.
    assert result.ret in (
        pytest.ExitCode.OK,
        pytest.ExitCode.NO_TESTS_COLLECTED,
    ), f"Fill command failed:\n{result.outlines}"
    assert not any("INTERNALERROR" in line for line in result.outlines), (
        f"Collection crashed:\n{result.outlines}"
    )
    assert any("no spec type requested" in line for line in result.outlines), (
        f"Expected a notice naming the offending test: {result.outlines}"
    )
    assert any("test_plain_pytest_test" in line for line in result.outlines), (
        f"Expected the offending test to be named: {result.outlines}"
    )


def test_plain_pytest_test_does_not_affect_fillable_tests(
    pytester: pytest.Pytester,
) -> None:
    """Fillable tests in the same module are still collected."""
    result = run_fill_collect_only(pytester, test_module_mixed)

    assert result.ret == 0, f"Fill command failed:\n{result.outlines}"
    assert not any("INTERNALERROR" in line for line in result.outlines), (
        f"Collection crashed:\n{result.outlines}"
    )
    assert any(
        "test_mixed_fillable_test[fork_Istanbul-state_test]" in line
        for line in result.outlines
    ), f"Expected the fillable test to be collected: {result.outlines}"
    assert not any(
        "test_mixed_plain_pytest_test[fork_Istanbul-state_test]" in line
        for line in result.outlines
    ), f"Expected the plain test to be deselected: {result.outlines}"
