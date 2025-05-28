"""CLI entry point for the `fill` pytest-based command."""

from typing import List

import click

from .base import PytestCommand, PytestExecution, common_pytest_options
from .processors import HelpFlagsProcessor, StdoutFlagsProcessor


class FillCommand(PytestCommand):
    """Pytest command for the fill operation."""

    def __init__(self):
        """Initialize fill command with processors."""
        super().__init__(
            config_file="pytest.ini",
            argument_processors=[
                HelpFlagsProcessor("fill"),
                StdoutFlagsProcessor(),
            ],
        )


class PhilCommand(FillCommand):
    """Friendly fill command with emoji reporting."""

    def create_executions(self, pytest_args: List[str]) -> List[PytestExecution]:
        """Create execution with emoji report options."""
        processed_args = self.process_arguments(pytest_args)

        emoji_args = processed_args + [
            "-o",
            "report_passed=🦄",
            "-o",
            "report_xpassed=🌈",
            "-o",
            "report_failed=👾",
            "-o",
            "report_xfailed=🦺",
            "-o",
            "report_skipped=🦘",
            "-o",
            "report_error=🚨",
        ]

        return [
            PytestExecution(
                config_file=self.config_file,
                args=emoji_args,
            )
        ]


@click.command(
    context_settings={
        "ignore_unknown_options": True,
    }
)
@common_pytest_options
def fill(pytest_args: List[str], **kwargs) -> None:
    """Entry point for the fill command."""
    command = FillCommand()
    command.execute(list(pytest_args))


@click.command(
    context_settings={
        "ignore_unknown_options": True,
    }
)
@common_pytest_options
def phil(pytest_args: List[str], **kwargs) -> None:
    """Friendly alias for the fill command."""
    command = PhilCommand()
    command.execute(list(pytest_args))
