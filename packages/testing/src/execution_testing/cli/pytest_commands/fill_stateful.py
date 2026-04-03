"""CLI entry point for the `fill-stateful` pytest-based command."""

from typing import Any, List

import click

from .base import PytestCommand, common_pytest_options


def create_fill_stateful_command() -> PytestCommand:
    """Initialize the fill-stateful command."""
    return PytestCommand(
        config_file="pytest-fill-stateful.ini",
    )


@click.command(
    name="fill-stateful",
    context_settings={
        "help_option_names": ["-h", "--help"],
        "ignore_unknown_options": True,
    },
)
@common_pytest_options
def fill_stateful(pytest_args: List[str], **kwargs: Any) -> None:
    """Fill stateful fixtures via testing_buildBlockV1."""
    del kwargs

    cmd = create_fill_stateful_command()
    cmd.execute(list(pytest_args))
