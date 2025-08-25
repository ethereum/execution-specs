"""CLI entry point for the EIP version checker pytest-based command."""

from typing import List

import click

from config.check_eip_versions import CheckEipVersionsConfig

from .base import PytestCommand, common_pytest_options
from .processors import HelpFlagsProcessor


@click.command(context_settings={"ignore_unknown_options": True})
@common_pytest_options
def check_eip_versions(pytest_args: List[str], **kwargs) -> None:
    """Run pytest with the `spec_version_checker` plugin."""
    command = PytestCommand(
        config_file="pytest-check-eip-versions.ini",
        argument_processors=[HelpFlagsProcessor("check-eip-versions")],
    )

    args_with_until = ["--until", CheckEipVersionsConfig().UNTIL_FORK] + list(pytest_args)
    command.execute(args_with_until)
