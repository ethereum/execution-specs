"""
Tests for pytest commands (e.g., fill) click CLI.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Generator

import pytest
from click.testing import CliRunner

import pytest_plugins.filler.filler

from ..pytest_commands.fill import fill


@pytest.fixture
def runner():
    """Provides a Click CliRunner for invoking command-line interfaces."""
    return CliRunner()


def test_fill_help(runner):
    """
    Test the `--help` option of the `fill` command.
    """
    result = runner.invoke(fill, ["--help"])
    assert result.exit_code == pytest.ExitCode.OK
    assert "[--evm-bin EVM_BIN]" in result.output
    assert "[--traces]" in result.output
    assert "[--evm-code-type EVM_CODE_TYPE]" in result.output
    assert "--help" in result.output
    assert "Arguments defining evm executable behavior:" in result.output


def test_fill_pytest_help(runner):
    """
    Test the `--pytest-help` option of the `fill` command.
    """
    result = runner.invoke(fill, ["--pytest-help"])
    assert result.exit_code == pytest.ExitCode.OK
    assert "[options] [file_or_dir] [file_or_dir] [...]" in result.output
    assert "-k EXPRESSION" in result.output


def test_fill_with_invalid_option(runner):
    """
    Test invoking `fill` with an invalid option.
    """
    result = runner.invoke(fill, ["--invalid-option"])
    assert result.exit_code != 0
    assert "unrecognized arguments" in result.output


def test_tf_deprecation(runner):
    """
    Test the deprecation message of the `tf` command.
    """
    from ..pytest_commands.fill import tf

    result = runner.invoke(tf, [])
    assert result.exit_code == 1
    assert "The `tf` command-line tool has been superseded by `fill`" in result.output


@pytest.mark.run_in_serial
class TestHtmlReportFlags:
    """
    Test html report generation and output options.
    """

    @pytest.fixture
    def fill_args(self):
        """
        Provides default arguments for the `fill` command when testing html report
        generation.

        Specifies a single existing example test case for faster fill execution,
        and to allow for tests to check for the fixture generation location.
        """
        return ["-k", "test_dup and state_test-DUP16", "--fork", "Frontier"]

    @pytest.fixture()
    def default_html_report_file_path(self):
        """
        The default file path for fill's pytest html report.
        """
        return pytest_plugins.filler.filler.default_html_report_file_path()

    @pytest.fixture(scope="function")
    def temp_dir(self) -> Generator[Path, None, None]:  # noqa: D102
        temp_dir = TemporaryDirectory()
        yield Path(temp_dir.name)
        temp_dir.cleanup()

    @pytest.fixture(scope="function", autouse=True)
    def monkeypatch_default_output_directory(self, monkeypatch, temp_dir):
        """
        Monkeypatch default output directory for the pytest commands.

        This avoids using the local directory in user space for the output of pytest
        commands and uses the a temporary directory instead.
        """

        def mock_default_output_directory():
            return temp_dir

        monkeypatch.setattr(
            pytest_plugins.filler.filler,
            "default_output_directory",
            mock_default_output_directory,
        )

    def test_fill_default_output_options(
        self,
        runner,
        temp_dir,
        fill_args,
        default_html_report_file_path,
    ):
        """
        Test default pytest html behavior: Neither `--html` or `--output` is specified.
        """
        default_html_path = temp_dir / default_html_report_file_path
        result = runner.invoke(fill, fill_args)
        assert result.exit_code == pytest.ExitCode.OK
        assert default_html_path.exists()

    def test_fill_no_html_option(
        self,
        runner,
        temp_dir,
        fill_args,
        default_html_report_file_path,
    ):
        """
        Test pytest html report is disabled with the `--no-html` flag.
        """
        default_html_path = temp_dir / default_html_report_file_path
        fill_args += ["--no-html"]
        result = runner.invoke(fill, fill_args)
        assert result.exit_code == pytest.ExitCode.OK
        assert not default_html_path.exists()

    def test_fill_html_option(
        self,
        runner,
        temp_dir,
        fill_args,
    ):
        """
        Tests pytest html report generation with only the `--html` flag.
        """
        non_default_html_path = temp_dir / "non_default_output_dir" / "report.html"
        fill_args += ["--html", str(non_default_html_path)]
        result = runner.invoke(fill, fill_args)
        assert result.exit_code == pytest.ExitCode.OK
        assert non_default_html_path.exists()

    def test_fill_output_option(
        self,
        runner,
        temp_dir,
        fill_args,
        default_html_report_file_path,
    ):
        """
        Tests pytest html report generation with only the `--output` flag.
        """
        output_dir = temp_dir / "non_default_output_dir"
        non_default_html_path = output_dir / default_html_report_file_path
        fill_args += ["--output", str(output_dir)]
        result = runner.invoke(fill, fill_args)
        assert result.exit_code == pytest.ExitCode.OK
        assert non_default_html_path.exists()
        assert (output_dir / "state_tests").exists(), "No fixtures in output directory"

    def test_fill_html_and_output_options(
        self,
        runner,
        temp_dir,
        fill_args,
    ):
        """
        Tests pytest html report generation with both `--output` and `--html` flags.
        """
        output_dir = temp_dir / "non_default_output_dir_fixtures"
        html_path = temp_dir / "non_default_output_dir_html" / "non_default.html"
        fill_args += ["--output", str(output_dir), "--html", str(html_path)]
        result = runner.invoke(fill, fill_args)
        assert result.exit_code == pytest.ExitCode.OK
        assert html_path.exists()
        assert (output_dir / "state_tests").exists(), "No fixtures in output directory"
