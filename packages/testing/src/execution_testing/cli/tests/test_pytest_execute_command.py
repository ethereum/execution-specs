"""Tests for execute command click CLI."""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from ...test_types.chain_config_types import (
    DEFAULT_CHAIN_ID,
    ChainConfigDefaults,
)
from ...test_types.transaction_types import Transaction
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
    """
    Test that all execute subcommands --help work without argument conflicts.

    This is a regression test for issue where --chain-id was defined in
    multiple plugins, causing argparse.ArgumentError conflicts.
    """
    subcommands = ["remote", "recover", "hive", "eth-config"]

    for subcommand in subcommands:
        result = runner.invoke(execute, [subcommand, "--help"])
        assert result.exit_code == 0, (
            f"execute {subcommand} --help failed with exit code "
            f"{result.exit_code}\nOutput: {result.output}"
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


def test_execute_remote_leaks_chain_id_into_later_defaults(
    runner: CliRunner, tmp_path: Path
) -> None:
    """Demonstrate that an in-process execute session leaks chain ID."""
    inner_test = tmp_path / "test_inner.py"
    inner_test.write_text(
        "\n".join(
            [
                "from execution_testing import (",
                "    Account,",
                "    Environment,",
                "    TestAddress,",
                "    Transaction,",
                ")",
                "",
                "def test_noop(state_test) -> None:",
                "    state_test(",
                "        env=Environment(),",
                "        pre={TestAddress: Account(balance=1_000_000)},",
                "        post={},",
                "        tx=Transaction(),",
                "    )",
            ]
        )
    )

    ChainConfigDefaults.chain_id = DEFAULT_CHAIN_ID
    with patch(
        "execution_testing.cli.pytest_commands.plugins.execute.rpc.remote.EthRPC"
    ) as mock_eth_rpc:
        mock_eth_rpc.return_value.chain_id.return_value = 12345
        result = runner.invoke(
            execute,
            [
                "remote",
                "--rpc-endpoint=http://localhost:12345",
                "--chain-id=12345",
                "--collect-only",
                "-q",
                str(inner_test),
            ],
        )

    assert result.exit_code == 0, result.output
    assert Transaction().chain_id == DEFAULT_CHAIN_ID
