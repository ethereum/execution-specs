"""CLI entry point for the `checklist` pytest-based command."""

from typing import List

import click

from .base import PytestCommand


class ChecklistCommand(PytestCommand):
    """Pytest command for generating EIP checklists."""

    def __init__(self):
        """Initialize checklist command with processors."""
        super().__init__(
            config_file="pytest.ini",
        )

    def process_arguments(self, pytest_args: List[str]) -> List[str]:
        """Process arguments, ensuring checklist generation is enabled."""
        processed_args = super().process_arguments(pytest_args)

        # Add collect-only flag to avoid running tests
        processed_args.extend(["-p", "pytest_plugins.filler.eip_checklist"])

        return processed_args


@click.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=False, dir_okay=True, writable=True),
    default="./checklists",
    help="Directory to output the generated checklists (default: ./checklists)",
)
@click.option(
    "--eip",
    "-e",
    type=int,
    multiple=True,
    help="Generate checklist only for specific EIP(s)",
)
def checklist(output: str, eip: tuple, **kwargs) -> None:
    """
    Generate EIP test checklists based on pytest.mark.eip_checklist markers.

    This command scans test files for eip_checklist markers and generates
    filled checklists showing which checklist items have been implemented.

    Examples:
        # Generate checklists for all EIPs
        uv run checklist

        # Generate checklist for specific EIP
        uv run checklist --eip 7702

        # Generate checklists for specific test path
        uv run checklist tests/prague/eip7702*

        # Specify output directory
        uv run checklist --output ./my-checklists

    """
    # Add output directory to pytest args
    args = ["--checklist-output", output]

    # Add EIP filter if specified
    for eip_num in eip:
        args.extend(["--checklist-eip", str(eip_num)])

    command = ChecklistCommand()
    command.execute(args)


if __name__ == "__main__":
    checklist()
