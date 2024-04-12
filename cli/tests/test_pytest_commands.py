"""
Tests for pytest commands (e.g., fill) click CLI.
"""

import pytest
from click.testing import CliRunner

from ..pytest_commands import fill


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
    assert "[--evm-bin EVM_BIN] [--traces]" in result.output
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
    from ..pytest_commands import tf

    result = runner.invoke(tf, [])
    assert result.exit_code == 1
    assert "The `tf` command-line tool has been superseded by `fill`" in result.output
