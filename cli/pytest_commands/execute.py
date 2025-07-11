"""CLI entry point for the `execute` pytest-based command."""

from pathlib import Path
from typing import List

import click

from .base import PytestCommand, common_pytest_options
from .processors import HelpFlagsProcessor


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
    }
)
def execute() -> None:
    """Execute command to run tests in hive or live networks."""
    pass


def _create_execute_subcommand(
    command_name: str,
    config_file: str,
    help_text: str,
    required_args: List[str] | None = None,
    static_test_paths: List[Path] | None = None,
) -> click.Command:
    """Create an execute subcommand with standardized structure."""
    pytest_command = PytestCommand(
        config_file=config_file,
        argument_processors=[HelpFlagsProcessor(f"execute-{command_name}", required_args)],
        static_test_paths=static_test_paths,
    )

    @execute.command(
        name=command_name,
        help=help_text,
        context_settings={"ignore_unknown_options": True},
    )
    @common_pytest_options
    def command(pytest_args: List[str], **_kwargs) -> None:
        pytest_command.execute(list(pytest_args))

    command.__doc__ = help_text
    return command


# Create the subcommands
hive = _create_execute_subcommand(
    "hive",
    "pytest-execute-hive.ini",
    "Execute tests using hive as a backend (`./hive --dev`).",
)

remote = _create_execute_subcommand(
    "remote",
    "pytest-execute.ini",
    "Execute tests using a remote RPC endpoint.",
    required_args=[
        "--rpc-endpoint=http://localhost:8545",
        "--rpc-chain-id=1",
        "--rpc-seed-key=1",
    ],
)

eth_config = _create_execute_subcommand(
    "eth-config",
    "pytest-execute-eth-config.ini",
    "Test a client's configuration using the `eth_config` RPC endpoint.",
    required_args=["--network=Mainnet", "--rpc-endpoint=http://localhost:8545"],
    static_test_paths=[Path("pytest_plugins/execute/eth_config/execute_eth_config.py")],
)

recover = _create_execute_subcommand(
    "recover",
    "pytest-execute-recover.ini",
    "Recover funds from test executions using a remote RPC endpoint.",
    required_args=[
        "--rpc-endpoint=http://localhost:8545",
        "--rpc-chain-id=1",
        "--start-eoa-index=1",
        "--destination=0x0000000000000000000000000000000000000000",
    ],
    static_test_paths=[Path("pytest_plugins/execute/execute_recover.py")],
)
