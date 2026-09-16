"""Test which test modules the EIP version checker collects."""

import textwrap

import pytest

from execution_testing.forks import get_deployed_forks, get_forks

LATEST_FORK = get_forks()[-1]
LAST_DEPLOYED_FORK = get_deployed_forks()[-1]

VERSION_CHECK_ITEM = "*/eip9999_example/test_example.py::test_eip_spec_version"

CHECK_EIP_VERSIONS_INI = (
    "src/execution_testing/cli/pytest_commands/pytest_ini_files/"
    "pytest-check-eip-versions.ini"
)

MODULE_HEADER = textwrap.dedent(
    """
    import pytest

    REFERENCE_SPEC_GIT_PATH = "EIPS/eip-9999.md"
    REFERENCE_SPEC_VERSION = "0"
    """
)

MODULE_LEVEL_TEST = textwrap.dedent(
    """
    @pytest.mark.valid_from("{fork}")
    def test_example(state_test):
        pass
    """
)

CLASS_NESTED_TEST = textwrap.dedent(
    """
    class TestExample:
        @pytest.mark.valid_from("{fork}")
        def test_example(self, state_test):
            pass
    """
)


def collect_version_checks(
    pytester: pytest.Pytester, test_source: str, *args: str
) -> pytest.RunResult:
    """Collect the version checks for an EIP module holding `test_source`."""
    pytester.makepyfile(
        **{"tests/eip9999_example/test_example": MODULE_HEADER + test_source}
    )
    pytester.copy_example(name=CHECK_EIP_VERSIONS_INI)
    return pytester.runpytest(
        "-c",
        "pytest-check-eip-versions.ini",
        "--github-token",
        "unused",
        "--collect-only",
        "-q",
        *args,
    )


@pytest.mark.parametrize(
    "test_source",
    [
        pytest.param(MODULE_LEVEL_TEST, id="module_level"),
        pytest.param(CLASS_NESTED_TEST, id="class_nested"),
    ],
)
def test_module_reference_spec_is_checked(
    pytester: pytest.Pytester, test_source: str
) -> None:
    """
    Test that a module's reference spec is checked whether its tests are
    declared at module level or nested within a class.
    """
    result = collect_version_checks(
        pytester, test_source.format(fork="Frontier")
    )
    assert result.ret == pytest.ExitCode.OK
    result.stdout.fnmatch_lines([VERSION_CHECK_ITEM])


@pytest.mark.skipif(
    LATEST_FORK.is_deployed(),
    reason="the default only matters while a fork is under development",
)
@pytest.mark.parametrize(
    "fork_args,checked",
    [
        pytest.param([], True, id="default"),
        pytest.param(["--fork", LATEST_FORK.name()], True, id="fork_latest"),
        pytest.param(
            ["--until", LAST_DEPLOYED_FORK.name()],
            False,
            id="until_deployed",
        ),
    ],
)
def test_latest_fork_module_is_checked(
    pytester: pytest.Pytester, fork_args: list[str], checked: bool
) -> None:
    """
    Test that the checker collects a module for the latest fork unless
    `--until` ends before that fork.
    """
    result = collect_version_checks(
        pytester,
        MODULE_LEVEL_TEST.format(fork=LATEST_FORK.name()),
        *fork_args,
    )
    if checked:
        assert result.ret == pytest.ExitCode.OK
        result.stdout.fnmatch_lines([VERSION_CHECK_ITEM])
    else:
        assert result.ret == pytest.ExitCode.NO_TESTS_COLLECTED
        result.stdout.no_fnmatch_line(VERSION_CHECK_ITEM)
