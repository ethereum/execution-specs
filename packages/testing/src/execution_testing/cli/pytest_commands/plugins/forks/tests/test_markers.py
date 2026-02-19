"""Test fork markers and their effect on test parametrization."""

from typing import List

import pytest


def generate_test(**kwargs: str) -> str:
    """Generate a test function with the given fork markers."""
    markers = [f"@pytest.mark.{key}({value})" for key, value in kwargs.items()]
    marker_lines = "\n".join(markers)
    return f"""
import pytest
{marker_lines}
@pytest.mark.state_test_only
def test_case(state_test):
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
                valid_at_transition_to=(
                    '"Paris", subsequent_forks=True, until="Cancun"'
                ),
            ),
            ["--until=Prague"],
            {"passed": 2, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_at_transition_to,subsequent_forks=True,until",
        ),
        pytest.param(
            generate_test(
                valid_at_transition_to='"Cancun"',
            ),
            ["--fork=ShanghaiToCancunAtTime15k"],
            {"passed": 1, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_at_transition_to,--fork=transition_fork_only",
        ),
        pytest.param(
            generate_test(
                valid_from='"Osaka"',
                valid_until='"BPO1"',
            ),
            ["--until=BPO1"],
            {"passed": 1, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_until_bpo_fork_without_bpo_test_marker",
            marks=pytest.mark.skip(reason="BPO tests are not supported yet"),
        ),
        pytest.param(
            generate_test(
                valid_from='"Osaka"',
                valid_until='"BPO1"',
                valid_for_bpo_forks="",
            ),
            ["--until=BPO1"],
            {"passed": 2, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_until_bpo_fork_with_bpo_test_marker",
            marks=pytest.mark.skip(reason="BPO tests are not supported yet"),
        ),
        pytest.param(
            generate_test(
                valid_at_transition_to=(
                    '"Osaka", subsequent_forks=True, until="BPO1"'
                ),
            ),
            ["--until=BPO1"],
            {"passed": 1, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_at_transition_without_bpo_test_marker",
            marks=pytest.mark.skip(reason="BPO tests are not supported yet"),
        ),
        pytest.param(
            generate_test(
                valid_at_transition_to=(
                    '"Osaka", subsequent_forks=True, until="BPO1"'
                ),
                valid_for_bpo_forks="",
            ),
            ["--until=BPO1"],
            {"passed": 2, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_at_transition_with_bpo_test_marker",
            marks=pytest.mark.skip(reason="BPO tests are not supported yet"),
        ),
        pytest.param(
            generate_test(
                valid_at_transition_to='"Cancun"',
            ),
            ["--fork=Cancun"],
            {"passed": 1, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_at_transition_to_with_exact_fork",
        ),
        pytest.param(
            generate_test(
                valid_at_transition_to='"Cancun"',
            ),
            ["--from=Cancun", "--until=Prague"],
            {"passed": 1, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_at_transition_to_from_fork_until_later_fork",
        ),
        pytest.param(
            generate_test(
                valid_at_transition_to='"BPO1"',
                valid_for_bpo_forks="",
            ),
            ["--fork=Osaka"],
            {"passed": 0, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_at_transition_with_bpo_test_marker_fork_parent",
            marks=pytest.mark.skip(reason="BPO tests are not supported yet"),
        ),
        pytest.param(
            generate_test(
                valid_at_transition_to='"BPO1"',
                valid_for_bpo_forks="",
            ),
            ["--from=Osaka", "--until=Osaka"],
            {"passed": 0, "failed": 0, "skipped": 0, "errors": 0},
            id="valid_at_transition_with_bpo_test_marker_from_parent",
            marks=pytest.mark.skip(reason="BPO tests are not supported yet"),
        ),
    ],
)
def test_fork_markers(
    pytester: pytest.Pytester,
    test_function: str,
    outcomes: dict,
    pytest_args: List[str],
) -> None:
    """
    Test fork markers in an isolated test session, i.e., in
    a `fill` execution.

    In the case of an error, check that the expected error string is in the
    console output.
    """
    pytester.makepyfile(test_function)
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "-v",
        *pytest_args,
    )
    result.assert_outcomes(**outcomes)


# --- Tests for param-level validity markers --- #


def generate_param_level_marker_test() -> str:
    """Generate a test function with param-level fork validity markers."""
    return """
import pytest

@pytest.mark.parametrize(
    "value",
    [
        pytest.param(
            True,
            id="from_tangerine",
            marks=pytest.mark.valid_from("TangerineWhistle"),
        ),
        pytest.param(
            False,
            id="from_paris",
            marks=pytest.mark.valid_from("Paris"),
        ),
    ],
)
@pytest.mark.state_test_only
def test_param_level_valid_from(state_test, value):
    pass
"""


def generate_param_level_valid_until_test() -> str:
    """Generate a test function with param-level valid_until markers."""
    return """
import pytest

@pytest.mark.parametrize(
    "value",
    [
        pytest.param(
            True,
            id="until_cancun",
            marks=pytest.mark.valid_until("Cancun"),
        ),
        pytest.param(
            False,
            id="until_paris",
            marks=pytest.mark.valid_until("Paris"),
        ),
    ],
)
@pytest.mark.state_test_only
def test_param_level_valid_until(state_test, value):
    pass
"""


def generate_param_level_mixed_test() -> str:
    """Generate a test with both function-level and param-level markers."""
    return """
import pytest

@pytest.mark.parametrize(
    "value",
    [
        pytest.param(
            True,
            id="all_forks",
            marks=pytest.mark.valid_from("TangerineWhistle"),
        ),
        pytest.param(
            False,
            id="paris_only",
            marks=pytest.mark.valid_from("Paris"),
        ),
    ],
)
@pytest.mark.valid_until("Cancun")
@pytest.mark.state_test_only
def test_mixed_function_and_param_markers(state_test, value):
    pass
"""


@pytest.mark.parametrize(
    "test_function,pytest_args,outcomes",
    [
        pytest.param(
            generate_param_level_marker_test(),
            ["--from=Paris", "--until=Cancun"],
            # from_tangerine: Paris, Shanghai, Cancun = 3 forks
            # from_paris: Paris, Shanghai, Cancun = 3 forks
            # Total: 6 tests
            {"passed": 6, "failed": 0, "skipped": 0, "errors": 0},
            id="param_level_valid_from_paris_to_cancun",
        ),
        pytest.param(
            generate_param_level_marker_test(),
            ["--from=Berlin", "--until=Shanghai"],
            # from_tangerine: Berlin, London, Paris, Shanghai = 4 forks
            # from_paris: Paris, Shanghai = 2 forks
            # Total: 6 tests
            {"passed": 6, "failed": 0, "skipped": 0, "errors": 0},
            id="param_level_valid_from_berlin_to_shanghai",
        ),
        pytest.param(
            generate_param_level_marker_test(),
            ["--from=Berlin", "--until=London"],
            # from_tangerine: Berlin, London = 2 forks
            # from_paris: none (Paris > London)
            # Total: 2 tests
            {"passed": 2, "failed": 0, "skipped": 0, "errors": 0},
            id="param_level_valid_from_berlin_to_london",
        ),
        pytest.param(
            generate_param_level_valid_until_test(),
            ["--from=Paris", "--until=Prague"],
            # until_cancun: Paris, Shanghai, Cancun = 3 forks
            # until_paris: Paris = 1 fork
            # Total: 4 tests
            {"passed": 4, "failed": 0, "skipped": 0, "errors": 0},
            id="param_level_valid_until_paris_to_prague",
        ),
        pytest.param(
            generate_param_level_valid_until_test(),
            ["--from=Shanghai", "--until=Prague"],
            # until_cancun: Shanghai, Cancun = 2 forks
            # until_paris: none (Shanghai > Paris)
            # Total: 2 tests
            {"passed": 2, "failed": 0, "skipped": 0, "errors": 0},
            id="param_level_valid_until_shanghai_to_prague",
        ),
        pytest.param(
            generate_param_level_mixed_test(),
            ["--from=Berlin", "--until=Prague"],
            # Function marker: valid_until("Cancun") limits to <= Cancun
            # all_forks (TangerineWhistle):
            #   Berlin, London, Paris, Shanghai, Cancun = 5
            # paris_only: Paris, Shanghai, Cancun = 3
            # Total: 8 tests
            {"passed": 8, "failed": 0, "skipped": 0, "errors": 0},
            id="mixed_markers_berlin_to_prague",
        ),
        pytest.param(
            generate_param_level_mixed_test(),
            ["--from=Paris", "--until=Shanghai"],
            # Function marker: valid_until("Cancun") limits to <= Cancun
            # Command line: --until=Shanghai further limits to <= Shanghai
            # all_forks: Paris, Shanghai = 2 forks
            # paris_only: Paris, Shanghai = 2 forks
            # Total: 4 tests
            {"passed": 4, "failed": 0, "skipped": 0, "errors": 0},
            id="mixed_markers_paris_to_shanghai",
        ),
    ],
)
def test_param_level_validity_markers(
    pytester: pytest.Pytester,
    test_function: str,
    outcomes: dict,
    pytest_args: List[str],
) -> None:
    """
    Test param-level validity markers (valid_from, valid_until).

    The pytest_collection_modifyitems hook filters tests based on param-level
    markers after parametrization, allowing different parameter values to have
    different fork validity ranges.
    """
    pytester.makepyfile(test_function)
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
    )
    result = pytester.runpytest(
        "-c",
        "pytest-fill.ini",
        "-v",
        *pytest_args,
    )
    result.assert_outcomes(**outcomes)
