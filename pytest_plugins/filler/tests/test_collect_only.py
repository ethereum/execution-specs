"""Test the fill command's --collect-only pytest option."""

import textwrap

from click.testing import CliRunner

from cli.pytest_commands.fill import fill

test_module_dummy = textwrap.dedent(
    """\
    import pytest

    from ethereum_test_tools import Environment

    @pytest.mark.valid_at("Istanbul")
    def test_dummy_collect_only_test(state_test):
        state_test(env=Environment(), pre={}, post={}, tx=None)
    """
)


def test_collect_only_output(testdir):
    """Test that --collect-only option produces expected output."""
    tests_dir = testdir.mkdir("tests")
    istanbul_tests_dir = tests_dir.mkdir("istanbul")
    dummy_dir = istanbul_tests_dir.mkdir("dummy_test_module")
    test_module = dummy_dir.join("test_dummy_collect.py")
    test_module.write(test_module_dummy)

    testdir.copy_example(name="pytest.ini")

    runner = CliRunner()
    result = runner.invoke(
        fill,
        [
            "--fork",
            "Istanbul",
            "tests/istanbul/dummy_test_module/",
            "--collect-only",
            "-q",
        ],
    )

    assert result.exit_code == 0, f"Fill command failed:\n{result.output}"

    assert (
        "tests/istanbul/dummy_test_module/test_dummy_collect.py::test_dummy_collect_only_test[fork_Istanbul-state_test]"
        in result.output
    )
    assert (
        "tests/istanbul/dummy_test_module/test_dummy_collect.py::test_dummy_collect_only_test[fork_Istanbul-blockchain_test_from_state_test]"
        in result.output
    )
    # fill generates 3 test variants: state_test, blockchain_test, and blockchain_test_engine
    assert "3 tests collected" in result.output
