"""
Test the forks plugin.
"""

import pytest

from ethereum_test_forks import (
    ArrowGlacier,
    Paris,
    forks_from_until,
    get_deployed_forks,
    get_forks,
)
from ethereum_test_tools import StateTest


@pytest.fixture
def fork_map():
    """
    Lookup fork.name() : fork class.
    """
    return {fork.name(): fork for fork in get_forks()}


def test_no_options_no_validity_marker(pytester):
    """
    Test test parametrization with:
    - no fork command-line options,
    - no fork validity marker.
    """
    pytester.makepyfile(
        f"""
        import pytest

        def test_all_forks({StateTest.pytest_parameter_name()}):
            pass
        """
    )
    pytester.copy_example(name="pytest.ini")
    result = pytester.runpytest("-v")
    all_forks = get_deployed_forks()
    forks_under_test = forks_from_until(all_forks[0], all_forks[-1])
    expected_skipped = 2  # eels doesn't support Constantinople
    expected_passed = (
        len(forks_under_test) * len(StateTest.supported_fixture_formats) - expected_skipped
    )
    stdout = "\n".join(result.stdout.lines)
    for fork in forks_under_test:
        for fixture_format in StateTest.supported_fixture_formats:
            if fixture_format.name.endswith("ENGINE") and fork < Paris:
                expected_passed -= 1
                assert f":test_all_forks[fork_{fork}-{fixture_format.name.lower()}]" not in stdout
                continue
            assert f":test_all_forks[fork_{fork}-{fixture_format.name.lower()}]" in stdout

    result.assert_outcomes(
        passed=expected_passed,
        failed=0,
        skipped=expected_skipped,
        errors=0,
    )


@pytest.mark.parametrize("fork", ["London", "Paris"])
def test_from_london_option_no_validity_marker(pytester, fork_map, fork):
    """
    Test test parametrization with:
    - --from London command-line option,
    - no until command-line option,
    - no fork validity marker.
    """
    pytester.makepyfile(
        f"""
        import pytest

        def test_all_forks({StateTest.pytest_parameter_name()}):
            pass
        """
    )
    pytester.copy_example(name="pytest.ini")
    result = pytester.runpytest("-v", "--from", fork)
    all_forks = get_deployed_forks()
    forks_under_test = forks_from_until(fork_map[fork], all_forks[-1])
    expected_passed = len(forks_under_test) * len(StateTest.supported_fixture_formats)
    stdout = "\n".join(result.stdout.lines)
    for fork in forks_under_test:
        for fixture_format in StateTest.supported_fixture_formats:
            if fixture_format.name.endswith("ENGINE") and fork < Paris:
                expected_passed -= 1
                assert f":test_all_forks[fork_{fork}-{fixture_format.name.lower()}]" not in stdout
                continue
            assert f":test_all_forks[fork_{fork}-{fixture_format.name.lower()}]" in stdout
    result.assert_outcomes(
        passed=expected_passed,
        failed=0,
        skipped=0,
        errors=0,
    )


def test_from_london_until_shanghai_option_no_validity_marker(pytester, fork_map):
    """
    Test test parametrization with:
    - --from London command-line option,
    - --until Shanghai command-line option,
    - no fork validity marker.
    """
    pytester.makepyfile(
        f"""
        import pytest

        def test_all_forks({StateTest.pytest_parameter_name()}):
            pass
        """
    )
    pytester.copy_example(name="pytest.ini")
    result = pytester.runpytest("-v", "--from", "London", "--until", "Shanghai")
    forks_under_test = forks_from_until(fork_map["London"], fork_map["Shanghai"])
    expected_passed = len(forks_under_test) * len(StateTest.supported_fixture_formats)
    stdout = "\n".join(result.stdout.lines)
    if ArrowGlacier in forks_under_test:
        forks_under_test.remove(ArrowGlacier)
        expected_passed -= len(StateTest.supported_fixture_formats)
    for fork in forks_under_test:
        for fixture_format in StateTest.supported_fixture_formats:
            if fixture_format.name.endswith("ENGINE") and fork < Paris:
                expected_passed -= 1
                assert f":test_all_forks[fork_{fork}-{fixture_format.name.lower()}]" not in stdout
                continue
            assert f":test_all_forks[fork_{fork}-{fixture_format.name.lower()}]" in stdout
    result.assert_outcomes(
        passed=expected_passed,
        failed=0,
        skipped=0,
        errors=0,
    )


def test_from_merge_until_merge_option_no_validity_marker(pytester, fork_map):
    """
    Test test parametrization with:
    - --from Merge command-line option,
    - --until Merge command-line option,
    - no fork validity marker.
    """
    pytester.makepyfile(
        f"""
        import pytest

        def test_all_forks({StateTest.pytest_parameter_name()}):
            pass
        """
    )
    pytester.copy_example(name="pytest.ini")
    result = pytester.runpytest("-v", "--from", "Merge", "--until", "Merge")
    forks_under_test = forks_from_until(fork_map["Paris"], fork_map["Paris"])
    expected_passed = len(forks_under_test) * len(StateTest.supported_fixture_formats)
    stdout = "\n".join(result.stdout.lines)
    for fork in forks_under_test:
        for fixture_format in StateTest.supported_fixture_formats:
            assert f":test_all_forks[fork_{fork}-{fixture_format.name.lower()}]" in stdout
    result.assert_outcomes(
        passed=expected_passed,
        failed=0,
        skipped=0,
        errors=0,
    )
