"""
Tests for the solc plugin.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
import solc_select.constants  # type: ignore
import solc_select.solc_select  # type: ignore

pytestmark = [pytest.mark.run_in_serial]


@pytest.fixture(scope="module")
def create_clean_solc_select_environment(request):
    """
    Setup: Copies solc artifacts to a temporary location before starting tests
    Teardown: Restores the artifacts after tests are done.
    """
    try:
        test_session_solc_version, _ = solc_select.solc_select.current_version()
    except Exception as e:
        raise Exception(
            "Error in setup: ensure you've called `solc-select use <version>` before running the "
            f"framework tests (exception: {e})"
        )

    artifacts_dir = solc_select.constants.ARTIFACTS_DIR
    global_version_file = solc_select.constants.SOLC_SELECT_DIR.joinpath("global-version")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        # Copy global-version and artifacts to a temporary directory and delete them
        if global_version_file.exists():
            shutil.copy(global_version_file, temp_dir_path / "global-version")
            os.remove(global_version_file)
        if artifacts_dir.exists():
            shutil.copytree(artifacts_dir, temp_dir_path / "artifacts", dirs_exist_ok=True)
            shutil.rmtree(artifacts_dir)

        os.makedirs(artifacts_dir, exist_ok=True)  # this won't get recreated by solc-select

        yield
        # Teardown: Restore the original files and directory from the temporary location
        if global_version_file.exists():
            os.remove(global_version_file)
        if artifacts_dir.exists():
            shutil.rmtree(artifacts_dir)

        # Restore the global-version file and artifacts
        if (temp_dir_path / "global-version").exists():
            shutil.copy(temp_dir_path / "global-version", global_version_file)
        if (temp_dir_path / "artifacts").exists():
            shutil.copytree(temp_dir_path / "artifacts", artifacts_dir, dirs_exist_ok=True)

        # Restore the solc version
        solc_select.solc_select.switch_global_version(
            str(test_session_solc_version), always_install=True
        )


@pytest.mark.usefixtures("create_clean_solc_select_environment")
@pytest.mark.parametrize("solc_version", ["0.8.21", "0.8.26"])
class TestSolcVersion:  # noqa: D101
    def test_solc_versions_flag(self, pytester, solc_version):
        """
        Ensure that the version specified by the `--solc-version` gets installed and is used.
        """
        pytester.makeconftest(
            f"""
            import pytest
            from ethereum_test_tools.code import Solc

            @pytest.fixture(autouse=True)
            def check_solc_version(request, solc_bin):
                assert request.config.getoption("solc_version") == "{solc_version}"
                assert Solc(solc_bin).version == "{solc_version}"
            """
        )
        pytester.copy_example(name="pytest.ini")
        pytester.copy_example(name="tests/homestead/yul/test_yul_example.py")
        result = pytester.runpytest(
            "-v",
            "--fork=Homestead",
            "--flat-output",  # required as copy_example doesn't copy to "tests/"" sub-folder
            "-m",
            "state_test",
            f"--solc-version={solc_version}",
        )

        result.assert_outcomes(
            passed=1,
            failed=0,
            skipped=0,
            errors=0,
        )


def test_solc_version_too_old(pytester):
    """
    Test the plugin exits with a UsageError if a version prior to Frontier is specified.
    """
    old_solc_version = "0.8.19"
    pytester.copy_example(name="pytest.ini")
    test_path = pytester.copy_example(name="tests/homestead/yul/test_yul_example.py")
    result = pytester.runpytest(
        "-v", "--fork=Frontier", "--solc-version", old_solc_version, test_path
    )
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    assert "Unsupported solc version" in "\n".join(result.stderr.lines)


def test_unknown_solc_version(pytester):
    """
    Test the plugin exits with a UsageError if a version unknown to solc-select is specified.
    """
    unknown_solc_version = "420.69.0"
    pytester.copy_example(name="pytest.ini")
    test_path = pytester.copy_example(name="tests/homestead/yul/test_yul_example.py")
    result = pytester.runpytest(
        "-v", "--fork=Frontier", "--solc-version", unknown_solc_version, test_path
    )
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    stderr = "\n".join(result.stderr.lines)
    assert f"Unknown version '{unknown_solc_version}'" in stderr
    assert "List available versions using" in stderr


def test_bad_solc_flag_combination(pytester):
    """
    Test the plugin exits with a UsageError if both `--solc-bin` and `--solc-version` are
    specified.
    """
    pytester.copy_example(name="pytest.ini")
    test_path = pytester.copy_example(name="tests/homestead/yul/test_yul_example.py")
    result = pytester.runpytest(
        "-v", "--fork=Frontier", "--solc-version=0.8.24", "--solc-bin=solc", test_path
    )
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    assert "You cannot specify both --solc-bin and --solc-version" in "\n".join(
        result.stderr.lines
    )


@pytest.mark.usefixtures("create_clean_solc_select_environment")
class TestSolcBin:
    """
    Test the `--solc-bin` flag.
    """

    @pytest.fixture()
    def solc_version(self):  # noqa: D102
        return "0.8.25"

    @pytest.fixture()
    def solc_bin(self, solc_version):
        """
        Returns an available solc binary.
        """
        solc_select.solc_select.switch_global_version(solc_version, always_install=True)
        bin_path = Path(f"solc-{solc_version}") / f"solc-{solc_version}"
        return solc_select.constants.ARTIFACTS_DIR.joinpath(bin_path)

    def test_solc_bin(self, pytester, solc_version, solc_bin):
        """
        Ensure that the version specified by the `--solc-version` gets installed and is used.
        """
        pytester.makeconftest(
            f"""
            import pytest
            from ethereum_test_tools.code import Solc

            @pytest.fixture(autouse=True)
            def check_solc_version(request, solc_bin):
                # test via solc_bin fixture
                assert Solc(solc_bin).version == "{solc_version}"
            """
        )
        pytester.copy_example(name="pytest.ini")
        pytester.copy_example(name="tests/homestead/yul/test_yul_example.py")
        result = pytester.runpytest(
            "-v",
            "--fork=Homestead",
            "-m",
            "state_test",
            "--flat-output",  # required as copy_example doesn't copy to "tests/"" sub-folder,
            f"--solc-bin={solc_bin}",
        )

        result.assert_outcomes(
            passed=1,
            failed=0,
            skipped=0,
            errors=0,
        )
