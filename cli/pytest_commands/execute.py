"""CLI entry point for the `execute` pytest-based command."""

import sys
from typing import Tuple

import click
import pytest

from .common import common_click_options, handle_help_flags


@click.group(
    context_settings={
        "help_option_names": ["-h", "--help"],
    }
)
def execute() -> None:
    """Execute command to run tests in hive or live networks."""
    pass


@execute.command(
    context_settings={
        "ignore_unknown_options": True,
    }
)
@common_click_options
def hive(
    pytest_args: Tuple[str, ...],
    **kwargs,
) -> None:
    """
    Execute tests using hive in dev-mode as backend, requires hive to be running
    (using command: `./hive --dev`).
    """
    pytest_type = "execute-hive"
    args = handle_help_flags(list(pytest_args), pytest_type=pytest_type)
    ini_file = "pytest-execute-hive.ini"
    args = ["-c", ini_file] + args
    result = pytest.main(args)
    sys.exit(result)


@execute.command(
    context_settings={
        "ignore_unknown_options": True,
    }
)
@common_click_options
def remote(
    pytest_args: Tuple[str, ...],
    **kwargs,
) -> None:
    """Execute tests using a remote RPC endpoint."""
    pytest_type = "execute"
    args = handle_help_flags(list(pytest_args), pytest_type=pytest_type)
    ini_file = "pytest-execute.ini"
    args = ["-c", ini_file] + args
    result = pytest.main(args)
    sys.exit(result)


@execute.command(
    context_settings={
        "ignore_unknown_options": True,
    }
)
@common_click_options
def recover(
    pytest_args: Tuple[str, ...],
    **kwargs,
) -> None:
    """Recover funds from a failed test execution using a remote RPC endpoint."""
    pytest_type = "execute-recover"
    args = handle_help_flags(list(pytest_args), pytest_type=pytest_type)
    ini_file = "pytest-execute-recover.ini"
    args = ["-c", ini_file] + args
    result = pytest.main(args)
    sys.exit(result)
