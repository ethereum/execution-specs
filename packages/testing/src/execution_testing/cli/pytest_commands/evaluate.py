"""CLI entry point for the `evaluate` pytest-based command."""

from typing import Any, List

import click

from .base import PytestCommand, common_pytest_options


def create_evaluate_command() -> PytestCommand:
    """Initialize the evaluate command."""
    return PytestCommand(config_file="pytest-evaluate.ini")


@click.command(
    name="evaluate",
    context_settings={
        "help_option_names": ["-h", "--help"],
        "ignore_unknown_options": True,
    },
)
@common_pytest_options
def evaluate(
    pytest_args: List[str],
    help_flag: bool,
    pytest_help_flag: bool,
    **kwargs: Any,
) -> None:
    """Run evaluation tests (`eval_*.py`) against the spec (no fixtures)."""
    del kwargs

    args = list(pytest_args)
    if help_flag or pytest_help_flag:
        args.append("--help")
    cmd = create_evaluate_command()
    cmd.execute(args)
