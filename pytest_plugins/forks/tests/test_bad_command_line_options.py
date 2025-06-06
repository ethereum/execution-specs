"""
Test that the correct error is produced if bad/invalid command-line
arguments are used.
"""

import pytest

invalid_cli_option_test_cases = (
    (
        "from_nonexistent_fork",
        (
            ("--from", "Marge"),  # codespell:ignore marge
            "Unsupported fork provided to --from: Marge",  # codespell:ignore marge
        ),
    ),
    (
        "until_nonexistent_fork",
        (
            ("--until", "Shangbye"),
            "Unsupported fork provided to --until: Shangbye",
        ),
    ),
    (
        "fork_nonexistent_fork",
        (
            ("--fork", "Cantcun"),
            "Unsupported fork provided to --fork: Cantcun",
        ),
    ),
    (
        "fork_and_from",
        (
            ("--fork", "Frontier", "--from", "Frontier"),
            "--fork cannot be used in combination with --from or --until",
        ),
    ),
    (
        "fork_and_until",
        (
            ("--fork", "Frontier", "--until", "Frontier"),
            "--fork cannot be used in combination with --from or --until",
        ),
    ),
    (
        "invalid_fork_range",
        (
            ("--from", "Paris", "--until", "Frontier"),
            "--from Paris --until Frontier creates an empty fork range",
        ),
    ),
)


@pytest.mark.parametrize(
    "options, error_string",
    [test_case for _, test_case in invalid_cli_option_test_cases],
    ids=[test_id for test_id, _ in invalid_cli_option_test_cases],
)
def test_bad_options(pytester, options, error_string):
    """
    Test that a test with an invalid command-line options:
        - Creates an outcome with exactly one error.
        - Triggers the expected error string in pytest's console output.

    Each invalid marker/marker combination is tested with one test in its own test
    session.
    """
    pytester.makepyfile(
        """
        def test_should_not_run(state_test):
            assert 0
        """
    )
    pytester.copy_example(name="pytest.ini")
    result = pytester.runpytest("-v", *options)
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    assert error_string in "\n".join(result.stderr.lines)
