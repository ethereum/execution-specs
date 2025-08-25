"""Tests for execute command click CLI."""

import pytest
from click.testing import CliRunner

from ..pytest_commands.execute import execute


@pytest.fixture
def runner():
    """Provide a Click CliRunner for invoking command-line interfaces."""
    return CliRunner()


def test_execute_help_shows_subcommand_docstrings(runner):
    """Test that execute --help shows sub-command docstrings."""
    result = runner.invoke(execute, ["--help"])
    assert result.exit_code == 0

    # Check that all sub-commands are shown with their help text
    assert "hive" in result.output
    assert "Execute tests using hive as a backend" in result.output

    assert "remote" in result.output
    assert "Execute tests using a remote RPC endpoint" in result.output

    assert "recover" in result.output
    assert "Recover funds from test executions" in result.output


def test_execute_subcommands_have_help_text(runner):
    """Test that execute sub-commands have proper help text defined."""
    from ..pytest_commands.execute import hive, recover, remote

    # Test that each sub-command has a docstring
    assert hive.__doc__ is not None
    assert "hive" in hive.__doc__.lower()

    assert remote.__doc__ is not None
    assert "remote" in remote.__doc__.lower()

    assert recover.__doc__ is not None
    assert "recover" in recover.__doc__.lower()
