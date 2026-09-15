"""Test which forks' modules the EIP version checker collects."""

import pytest

from execution_testing.forks import get_deployed_forks, get_forks

LATEST_FORK = get_forks()[-1]
LAST_DEPLOYED_FORK = get_deployed_forks()[-1]

VERSION_CHECK_ITEM = "*/eip9999_example/test_example.py::test_eip_spec_version"


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
    pytester.makepyfile(
        **{
            "tests/eip9999_example/test_example": f"""
                import pytest

                REFERENCE_SPEC_GIT_PATH = "EIPS/eip-9999.md"
                REFERENCE_SPEC_VERSION = "0"

                @pytest.mark.valid_from("{LATEST_FORK.name()}")
                def test_example(state_test):
                    pass
            """
        }
    )
    pytester.copy_example(
        name="src/execution_testing/cli/pytest_commands/pytest_ini_files/pytest-check-eip-versions.ini"
    )
    result = pytester.runpytest(
        "-c",
        "pytest-check-eip-versions.ini",
        "--github-token",
        "unused",
        "--collect-only",
        "-q",
        *fork_args,
    )
    if checked:
        assert result.ret == pytest.ExitCode.OK
        result.stdout.fnmatch_lines([VERSION_CHECK_ITEM])
    else:
        assert result.ret == pytest.ExitCode.NO_TESTS_COLLECTED
        result.stdout.no_fnmatch_line(VERSION_CHECK_ITEM)
