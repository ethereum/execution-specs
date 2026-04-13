"""CLI entry point for the `checklist` pytest-based command."""

from typing import Any, ClassVar, List

import click
import pytest

from ...forks import get_development_forks
from .base import PytestCommand


class ChecklistCommand(PytestCommand):
    """
    Pytest command to generate checklist documentation.

    The checklist command only collects tests to analyze markers and does
    not run them, so ``NO_TESTS_COLLECTED`` is treated as success.
    """

    allowed_exit_codes: ClassVar[List[pytest.ExitCode]] = [
        pytest.ExitCode.OK,
        pytest.ExitCode.NO_TESTS_COLLECTED,
    ]

    def __init__(self, **kwargs: Any) -> None:
        """Initialize checklist command."""
        super().__init__(config_file="pytest-fill.ini", **kwargs)


def _last_development_fork() -> str | None:
    """Return the name of the last development fork, if any."""
    dev_forks = get_development_forks()
    return dev_forks[-1].name() if dev_forks else None


@click.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    default="./checklists",
    help="Directory to output checklists (default: ./checklists)",
)
@click.option(
    "--eip",
    "-e",
    type=int,
    multiple=True,
    help="Generate checklist only for specific EIP(s)",
)
@click.option(
    "--until",
    "-u",
    type=str,
    default=None,
    help="Include upcoming forks up to and including this fork",
)
def checklist(
    output: str, eip: tuple[int, ...], until: str | None, **kwargs: Any
) -> None:
    """
    Generate EIP test checklists based on pytest.mark.eip_checklist markers.

    This command scans test files for eip_checklist markers and generates
    filled checklists showing which checklist items have been implemented.

    By default, includes all development forks so that checklists for
    upcoming EIPs are generated without needing --until.

    Examples:
        # Generate checklists for all EIPs
        uv run checklist

        # Generate checklist for specific EIP
        uv run checklist --eip 7702

        # Generate checklists for specific test path
        uv run checklist tests/prague/eip7702*

        # Limit to a specific fork
        uv run checklist --until Prague

        # Specify output directory
        uv run checklist --output ./my-checklists

    """
    del kwargs

    # Add output directory to pytest args
    args = ["--checklist-output", output]

    # Add EIP filter if specified
    for eip_num in eip:
        args.extend(["--checklist-eip", str(eip_num)])

    # Default --until to the last development fork so checklists for
    # upcoming EIPs are generated without requiring the flag explicitly.
    if until is None:
        until = _last_development_fork()
    if until:
        args.extend(["--until", until])

    command = ChecklistCommand(
        plugins=[
            "execution_testing.cli.pytest_commands.plugins.filler.eip_checklist"
        ],
    )
    command.execute(args)


if __name__ == "__main__":
    checklist()
