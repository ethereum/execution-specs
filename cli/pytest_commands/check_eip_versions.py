"""CLI entry point for the EIP version checker pytest-based command."""

import sys
from typing import List

import click
import pytest

from config.check_eip_versions import CheckEipVersionsConfig

from .common import common_click_options, handle_help_flags


@click.command(context_settings={"ignore_unknown_options": True})
@common_click_options
def check_eip_versions(pytest_args: List[str], **kwargs) -> None:
    """Run pytest with the `spec_version_checker` plugin."""
    args = ["-c", "pytest-check-eip-versions.ini"]
    args += ["--until", CheckEipVersionsConfig().UNTIL_FORK]
    args += handle_help_flags(list(pytest_args), pytest_type="check-eip-versions")
    result = pytest.main(args)
    sys.exit(result)
