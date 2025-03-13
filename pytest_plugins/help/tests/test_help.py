"""Test the help plugin."""

import pytest

FILL_TEST_ARGS = (
    "--evm-bin",
    "--traces",
    "--solc-bin",
    "--filler-path",
    "--output",
    "--forks",
    "--fork",
    "--from",
    "--until",
    "--help",
)


@pytest.mark.parametrize("help_flag", ["--fill-help"])
def test_local_arguments_present_in_fill_help(pytester, help_flag):
    """
    Test that locally defined command-line flags appear in the help if
    our custom help flag is used.
    """
    pytester.copy_example(name="pytest.ini")
    result = pytester.runpytest(help_flag)
    for test_arg in FILL_TEST_ARGS:
        assert test_arg in "\n".join(result.stdout.lines)


CONSUME_TEST_ARGS = (
    "--input",
    "--no-html",
    "--help",
)


@pytest.mark.parametrize(
    "command, help_flag",
    [
        ("direct", "--consume-help"),
        ("rlp", "--consume-help"),
        ("engine", "--consume-help"),
        ("hive", "--consume-help"),
    ],
)
def test_local_arguments_present_in_base_consume_help(pytester, help_flag, command):
    """Test that locally defined command-line flags appear in the help for consume subcommands."""
    pytester.copy_example(name="pytest-consume.ini")
    result = pytester.runpytest("-c", "./pytest-consume.ini", command, help_flag)
    for test_arg in CONSUME_TEST_ARGS:
        assert test_arg in "\n".join(result.stdout.lines)
