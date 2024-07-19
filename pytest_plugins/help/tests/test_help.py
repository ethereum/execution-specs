"""
Test the test_help plugin.
"""

import pytest

TEST_ARGS = (
    "--evm-bin",
    "--traces",
    "--solc-bin",
    "--filler-path",
    "--output",
    "--forks",
    "--fork",
    "--from",
    "--until",
    "--test-help",
)


@pytest.mark.parametrize("help_flag", ["--test-help"])
def test_local_arguments_present_in_est_help(pytester, help_flag):
    """
    Test that locally defined command-line flags appear in the help if
    our custom help flag is used.
    """
    pytester.copy_example(name="pytest.ini")
    result = pytester.runpytest(help_flag)
    for test_arg in TEST_ARGS:
        assert test_arg in "\n".join(result.stdout.lines)
