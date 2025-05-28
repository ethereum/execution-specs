"""CLI entry point for the `execute` pytest-based command."""

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
) -> click.Command:
    """Create an execute subcommand with standardized structure."""

    @execute.command(
        name=command_name,
        context_settings={"ignore_unknown_options": True},
    )
    @common_pytest_options
    def command(pytest_args: List[str], **kwargs) -> None:
        pytest_command = PytestCommand(
            config_file=config_file,
            argument_processors=[HelpFlagsProcessor(f"execute-{command_name}")],
        )
        pytest_command.execute(list(pytest_args))

    command.__doc__ = help_text
    return command


# Create the subcommands
hive = _create_execute_subcommand(
    "hive",
    "pytest-execute-hive.ini",
    (
        "Execute tests using hive in dev-mode as backend, requires hive to be running "
        "(using command: `./hive --dev`)."
    ),
)

remote = _create_execute_subcommand(
    "remote",
    "pytest-execute.ini",
    "Execute tests using a remote RPC endpoint.",
)

recover = _create_execute_subcommand(
    "recover",
    "pytest-execute-recover.ini",
    "Recover funds from a failed test execution using a remote RPC endpoint.",
)
