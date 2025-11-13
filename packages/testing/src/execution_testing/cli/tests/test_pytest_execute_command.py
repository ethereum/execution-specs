"""Tests for execute command click CLI."""

import pytest
from click.testing import CliRunner

from ..pytest_commands.execute import execute


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click CliRunner for invoking command-line interfaces."""
    return CliRunner()


def test_execute_help_shows_subcommand_docstrings(runner: CliRunner) -> None:
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


def test_execute_subcommands_have_help_text() -> None:
    """Test that execute sub-commands have proper help text defined."""
    from ..pytest_commands.execute import hive, recover, remote

    # Test that each sub-command has a docstring
    assert hive.__doc__ is not None
    assert "hive" in hive.__doc__.lower()

    assert remote.__doc__ is not None
    assert "remote" in remote.__doc__.lower()

    assert recover.__doc__ is not None
    assert "recover" in recover.__doc__.lower()


def test_execute_main_help(runner: CliRunner) -> None:
    """Test that execute --help works without errors."""
    result = runner.invoke(execute, ["--help"])
    assert result.exit_code == 0
    assert "Execute command to run tests" in result.output


def test_execute_remote_help(runner: CliRunner) -> None:
    """Test that execute remote --help works without argument conflicts."""
    result = runner.invoke(execute, ["remote", "--help"])
    assert result.exit_code == 0
    assert "After displaying help" in result.output
    # Verify no argparse conflicts with --chain-id
    assert "conflicting option string" not in result.output


def test_execute_recover_help(runner: CliRunner) -> None:
    """Test that execute recover --help works without argument conflicts."""
    result = runner.invoke(execute, ["recover", "--help"])
    assert result.exit_code == 0
    assert "After displaying help" in result.output
    # Verify --chain-id is available
    assert "--chain-id" in result.output
    # Verify no argparse conflicts
    assert "conflicting option string" not in result.output


def test_execute_hive_help(runner: CliRunner) -> None:
    """Test that execute hive --help works without errors."""
    result = runner.invoke(execute, ["hive", "--help"])
    assert result.exit_code == 0
    assert "After displaying help" in result.output


def test_execute_eth_config_help(runner: CliRunner) -> None:
    """Test that execute eth-config --help works without errors."""
    result = runner.invoke(execute, ["eth-config", "--help"])
    assert result.exit_code == 0
    assert "After displaying help" in result.output


def test_all_execute_subcommands_help_no_conflicts(runner: CliRunner) -> None:
    """Test that all execute subcommands --help work without argument conflicts.

    This is a regression test for issue where --chain-id was defined in multiple
    plugins, causing argparse.ArgumentError conflicts.
    """
    subcommands = ["remote", "recover", "hive", "eth-config"]

    for subcommand in subcommands:
        result = runner.invoke(execute, [subcommand, "--help"])
        assert result.exit_code == 0, (
            f"execute {subcommand} --help failed with exit code {result.exit_code}\n"
            f"Output: {result.output}"
        )
        # Ensure no argparse conflicts
        assert "ArgumentError" not in result.output, (
            f"execute {subcommand} --help has ArgumentError\n"
            f"Output: {result.output}"
        )
        assert "conflicting option string" not in result.output, (
            f"execute {subcommand} --help has conflicting option string\n"
            f"Output: {result.output}"
        )
