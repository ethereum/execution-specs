"""Test which test modules the EIP version checker collects."""

import textwrap

import pytest

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
    @pytest.mark.valid_from("Frontier")
    def test_example(state_test):
        pass
    """
)

CLASS_NESTED_TEST = textwrap.dedent(
    """
    class TestExample:
        @pytest.mark.valid_from("Frontier")
        def test_example(self, state_test):
            pass
    """
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
    pytester.makepyfile(
        **{"tests/eip9999_example/test_example": MODULE_HEADER + test_source}
    )
    pytester.copy_example(name=CHECK_EIP_VERSIONS_INI)
    result = pytester.runpytest(
        "-c",
        "pytest-check-eip-versions.ini",
        "--github-token",
        "unused",
        "--collect-only",
        "-q",
    )
    assert result.ret == pytest.ExitCode.OK
    result.stdout.fnmatch_lines([VERSION_CHECK_ITEM])
