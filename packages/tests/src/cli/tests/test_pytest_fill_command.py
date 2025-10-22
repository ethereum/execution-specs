"""Tests for pytest commands (e.g., fill) click CLI."""

from pathlib import Path
from typing import Callable

import pytest
from click.testing import CliRunner, Result
from pytest import MonkeyPatch, Pytester, RunResult, TempPathFactory

import pytest_plugins.filler.filler

from ..pytest_commands.fill import fill

MINIMAL_TEST_FILE_NAME = "test_example.py"
MINIMAL_TEST_CONTENTS = """
from ethereum_test_tools import Transaction
def test_function(state_test, pre):
    tx = Transaction(to=0, gas_limit=21_000, sender=pre.fund_eoa())
    state_test(pre=pre, post={}, tx=tx)
"""


@pytest.fixture
def expected_exit_code() -> pytest.ExitCode:
    return pytest.ExitCode.OK


class TestFillClickCli:
    """Test fill command using Click CLI."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Provide a Click CliRunner for invoking command-line interfaces."""
        return CliRunner()

    @pytest.fixture
    def run_fill(
        self, runner: CliRunner, expected_exit_code: pytest.ExitCode
    ) -> Callable[..., Result]:
        """Provide a Click CliRunner for invoking command-line interfaces."""

        def _run_fill(*args: str) -> Result:
            result = runner.invoke(fill, args)
            assert result.exit_code == expected_exit_code, (
                f"Invalid exit code, {result.exit_code}, "
                f"expected {expected_exit_code}, "
                f"stdout: {result.stdout}, "
                f"stderr: {result.stderr}, "
                f"command-line args: {args}"
            )
            return result

        return _run_fill

    def test_fill_help(self, run_fill: Callable[..., Result]) -> None:
        """Test the `--help` option of the `fill` command."""
        result = run_fill("--help")
        assert "[--evm-bin EVM_BIN]" in result.output
        assert "[--traces]" in result.output
        assert "[--evm-code-type EVM_CODE_TYPE]" in result.output
        assert "--help" in result.output
        assert "Arguments defining evm executable behavior:" in result.output

    def test_fill_pytest_help(self, run_fill: Callable[..., Result]) -> None:
        """Test the `--pytest-help` option of the `fill` command."""
        result = run_fill("--pytest-help")
        assert "[options] [file_or_dir] [file_or_dir] [...]" in result.output
        assert "-k EXPRESSION" in result.output

    @pytest.mark.parametrize(
        "expected_exit_code", [pytest.ExitCode.USAGE_ERROR]
    )
    def test_fill_with_invalid_option(
        self, run_fill: Callable[..., Result]
    ) -> None:
        """Test invoking `fill` with an invalid option."""
        result = run_fill("--invalid-option")
        assert "unrecognized arguments" in result.output


class TestFillPytester:
    """
    Test fill command using pytester.

    This mode skips the fill command's Click CLI and uses pytester to run the command.

    Pytester allows to actually fill the python test files.
    """

    @pytest.fixture
    def pytester_temp_dir(self, pytester: pytest.Pytester) -> Path:
        """
        Get the base temporary directory for pytest.
        """
        return pytester.path

    @pytest.fixture
    def minimal_test_path(self, pytester: pytest.Pytester) -> Path:
        """
        Minimal test file that's written to a file using pytester and ready to
        fill.
        """
        tests_dir = pytester.mkdir("tests")
        test_file = tests_dir / MINIMAL_TEST_FILE_NAME
        test_file.write_text(MINIMAL_TEST_CONTENTS)
        return test_file

    @pytest.fixture
    def fill_args(self, minimal_test_path: Path) -> list[str]:
        """Default fill arguments."""
        return [
            "--fork",
            "Cancun",
            str(minimal_test_path),
        ]

    @pytest.fixture
    def run_fill(
        self, pytester: Pytester, expected_exit_code: pytest.ExitCode
    ) -> Callable[..., RunResult]:
        """Provide a function to run the fill command with various options."""

        def _run_fill(*args: str) -> RunResult:
            pytester.copy_example(
                name="src/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
            )
            args = (
                "-c",
                "pytest-fill.ini",
                *args,
            )
            result = pytester.runpytest(*args)
            assert result.ret == expected_exit_code, (
                f"Invalid exit code, {result.ret}, "
                f"expected {expected_exit_code}, "
                f"stdout: {result.outlines}, "
                f"stderr: {result.errlines}, "
                f"command-line args: {args}"
            )
            return result

        return _run_fill

    @pytest.fixture()
    def default_html_report_file_path(self) -> str:
        """File path for fill's pytest html report."""
        return pytest_plugins.filler.filler.default_html_report_file_path()

    @pytest.fixture(scope="function")
    def default_fixtures_output(
        self, tmp_path_factory: TempPathFactory
    ) -> Path:
        """Provide a temporary directory as a pytest fixture."""
        return tmp_path_factory.mktemp("fixtures")

    @pytest.fixture(scope="function", autouse=True)
    def monkeypatch_default_output_directory(
        self, monkeypatch: MonkeyPatch, default_fixtures_output: Path
    ) -> None:
        """
        Monkeypatch default output directory for the pytest commands.

        This avoids using the local directory in user space for the output of
        pytest commands and uses the a temporary directory instead.
        """

        def mock_default_output_directory() -> Path:
            return default_fixtures_output

        monkeypatch.setattr(
            pytest_plugins.filler.filler,
            "default_output_directory",
            mock_default_output_directory,
        )

    def test_fill_default_output_options(
        self,
        run_fill: Callable[..., RunResult],
        default_fixtures_output: Path,
        fill_args: list[str],
        default_html_report_file_path: str,
    ) -> None:
        """
        Test default pytest html behavior: Neither `--html` or `--output` is
        specified.
        """
        default_html_path = (
            default_fixtures_output / default_html_report_file_path
        )
        run_fill(*fill_args)
        assert default_html_path.exists()

    def test_fill_no_html_option(
        self,
        run_fill: Callable[..., RunResult],
        default_fixtures_output: Path,
        fill_args: list[str],
        default_html_report_file_path: str,
    ) -> None:
        """Test pytest html report is disabled with the `--no-html` flag."""
        default_html_path = (
            default_fixtures_output / default_html_report_file_path
        )
        fill_args += ["--no-html"]
        run_fill(*fill_args)
        assert not default_html_path.exists()

    def test_fill_html_option(
        self,
        run_fill: Callable[..., RunResult],
        pytester_temp_dir: Path,
        fill_args: list[str],
    ) -> None:
        """Tests pytest html report generation with only the `--html` flag."""
        non_default_html_path = (
            pytester_temp_dir / "non_default_output_dir" / "report.html"
        )
        fill_args += ["--html", str(non_default_html_path)]
        run_fill(*fill_args)
        assert non_default_html_path.exists()

    def test_fill_output_option(
        self,
        run_fill: Callable[..., RunResult],
        pytester_temp_dir: Path,
        fill_args: list[str],
        default_html_report_file_path: str,
    ) -> None:
        """
        Tests pytest html report generation with only the `--output` flag.
        """
        output_dir = pytester_temp_dir / "non_default_output_dir"
        non_default_html_path = output_dir / default_html_report_file_path
        fill_args += ["--output", str(output_dir)]
        run_fill(*fill_args)
        assert non_default_html_path.exists()
        assert (output_dir / "state_tests").exists(), (
            "No fixtures in output directory"
        )

    def test_fill_html_and_output_options(
        self,
        run_fill: Callable[..., RunResult],
        pytester_temp_dir: Path,
        fill_args: list[str],
    ) -> None:
        """
        Tests pytest html report generation with both `--output` and `--html`
        flags.
        """
        output_dir = pytester_temp_dir / "non_default_output_dir_fixtures"
        html_path = (
            pytester_temp_dir
            / "non_default_output_dir_html"
            / "non_default.html"
        )
        fill_args += ["--output", str(output_dir), "--html", str(html_path)]
        run_fill(*fill_args)
        assert html_path.exists()
        assert (output_dir / "state_tests").exists(), (
            "No fixtures in output directory"
        )
