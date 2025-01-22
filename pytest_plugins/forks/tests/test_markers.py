"""Test fork markers and their effect on test parametrization."""

from typing import List

import pytest


def generate_test(**kwargs: str):
    """Generate a test function with the given fork markers."""
    markers = [f"@pytest.mark.{key}({value})" for key, value in kwargs.items()]
    marker_lines = "\n".join(markers)
    return f"""
import pytest
{marker_lines}
def test_case(state_test_only):
    pass
"""


@pytest.mark.parametrize(
    "test_function,pytest_args,outcomes",
    [
        pytest.param(
            generate_test(
                valid_until='"Cancun"',
            ),
            [],
            {"passed": 10, "failed": 0, "skipped": 1, "errors": 0},
            id="valid_until",
        ),
        pytest.param(
            generate_test(
                valid_until='"Cancun"',
            ),
            ["--from=Berlin"],
            {"passed": 5, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_until,--from",
        ),
        pytest.param(
            generate_test(
                valid_from='"Paris"',
            ),
            ["--until=Prague"],
            {"passed": 4, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_from",
        ),
        pytest.param(
            generate_test(
                valid_from='"Paris"',
                valid_until='"Cancun"',
            ),
            [],
            {"passed": 3, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_from_until",
        ),
        pytest.param(
            generate_test(
                valid_from='"Paris"',
                valid_until='"Cancun"',
            ),
            ["--until=Prague"],
            {"passed": 3, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_from_until,--until=Prague",
        ),
        pytest.param(
            generate_test(
                valid_from='"Paris"',
                valid_until='"Cancun"',
            ),
            ["--until=Shanghai"],
            {"passed": 2, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_from_until,--until=Shanghai",
        ),
        pytest.param(
            generate_test(
                valid_at_transition_to='"Shanghai"',
            ),
            [],
            {"passed": 1, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_at_transition_to",
        ),
        pytest.param(
            generate_test(
                valid_at_transition_to='"Shanghai"',
            ),
            ["--until=Prague"],
            {"passed": 1, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_at_transition_to,--until=Prague",
        ),
        pytest.param(
            generate_test(
                valid_at_transition_to='"Shanghai"',
            ),
            ["--until=Berlin"],
            {"passed": 0, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_at_transition_to,--until=Berlin",
        ),
        pytest.param(
            generate_test(
                valid_at_transition_to='"Paris", subsequent_forks=True',
            ),
            ["--until=Prague"],
            {"passed": 3, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_at_transition_to,subsequent_forks=True",
        ),
        pytest.param(
            generate_test(
                valid_at_transition_to='"Paris", subsequent_forks=True, until="Cancun"',
            ),
            ["--until=Prague"],
            {"passed": 2, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_at_transition_to,subsequent_forks=True,until",
        ),
    ],
)
def test_fork_markers(pytester, test_function: str, outcomes: dict, pytest_args: List[str]):
    """
    Test fork markers in an isolated test session, i.e., in
    a `fill` execution.

    In the case of an error, check that the expected error string is in the
    console output.
    """
    pytester.makepyfile(test_function)
    pytester.copy_example(name="pytest.ini")
    result = pytester.runpytest("-v", *pytest_args)
    result.assert_outcomes(**outcomes)
