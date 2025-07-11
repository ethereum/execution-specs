"""Test the fill command's --collect-only pytest option."""

import textwrap

import pytest

test_module_dummy = textwrap.dedent(
    """\
    import pytest

    from ethereum_test_tools import Environment

    @pytest.mark.valid_at("Istanbul")
    def test_dummy_collect_only_test(state_test):
        state_test(env=Environment(), pre={}, post={}, tx=None)
    """
)


def test_collect_only_output(pytester: pytest.Pytester):
    """Test that --collect-only option produces expected output."""
    tests_dir = pytester.mkdir("tests")
    istanbul_tests_dir = tests_dir / "istanbul"
    istanbul_tests_dir.mkdir()
    dummy_dir = istanbul_tests_dir / "dummy_test_module"
    dummy_dir.mkdir()
    test_module = dummy_dir / "test_dummy_collect.py"
    test_module.write_text(test_module_dummy)

    pytester.copy_example(name="src/cli/pytest_commands/pytest_ini_files/pytest-fill.ini")

    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "--fork",
        "Istanbul",
        "tests/istanbul/dummy_test_module/",
        "--collect-only",
        "-q",
    )

    assert result.ret == 0, f"Fill command failed:\n{result.outlines}"

    assert any(
        "tests/istanbul/dummy_test_module/test_dummy_collect.py::test_dummy_collect_only_test[fork_Istanbul-state_test]"
        in line
        for line in result.outlines
    ), f"Expected test output: {result.outlines}"
    assert any(
        "tests/istanbul/dummy_test_module/test_dummy_collect.py::test_dummy_collect_only_test[fork_Istanbul-blockchain_test_from_state_test]"
        in line
        for line in result.outlines
    ), f"Expected test output: {result.outlines}"
    # fill generates 3 test variants: state_test, blockchain_test_from_state_test,
    # blockchain_test_engine_from_state_test
    assert any("3 tests collected" in line for line in result.outlines)
