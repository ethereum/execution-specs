"""
Test the forks plugin.
"""

import pytest

from ethereum_test_forks import ArrowGlacier, forks_from_until, get_deployed_forks, get_forks


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
        """
        import pytest

        def test_all_forks(state_test):
            pass
        """
    )
    pytester.copy_example(name="pytest.ini")
    result = pytester.runpytest("-v")
    all_forks = get_deployed_forks()
    forks_under_test = forks_from_until(all_forks[0], all_forks[-1])
    for fork in forks_under_test:
        assert f":test_all_forks[fork_{fork}]" in "\n".join(result.stdout.lines)
    result.assert_outcomes(
        passed=len(forks_under_test),
        failed=0,
        skipped=0,
        errors=0,
    )


@pytest.mark.parametrize("fork", ["London", "Merge"])
def test_from_london_option_no_validity_marker(pytester, fork_map, fork):
    """
    Test test parametrization with:
    - --from London command-line option,
    - no until command-line option,
    - no fork validity marker.
    """
    pytester.makepyfile(
        """
        import pytest

        def test_all_forks(state_test):
            pass
        """
    )
    pytester.copy_example(name="pytest.ini")
    result = pytester.runpytest("-v", "--from", fork)
    all_forks = get_deployed_forks()
    forks_under_test = forks_from_until(fork_map[fork], all_forks[-1])
    for fork_under_test in forks_under_test:
        assert f":test_all_forks[fork_{fork_under_test}]" in "\n".join(result.stdout.lines)
    result.assert_outcomes(
        passed=len(forks_under_test),
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
        """
        import pytest

        def test_all_forks(state_test):
            pass
        """
    )
    pytester.copy_example(name="pytest.ini")
    result = pytester.runpytest("-v", "--from", "London", "--until", "Shanghai")
    forks_under_test = forks_from_until(fork_map["London"], fork_map["Shanghai"])
    if ArrowGlacier in forks_under_test:
        forks_under_test.remove(ArrowGlacier)
    for fork_under_test in forks_under_test:
        assert f":test_all_forks[fork_{fork_under_test}]" in "\n".join(result.stdout.lines)
    result.assert_outcomes(
        passed=len(forks_under_test),
        failed=0,
        skipped=0,
        errors=0,
    )
