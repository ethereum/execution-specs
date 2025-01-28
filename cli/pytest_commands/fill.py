"""CLI entry point for the `fill` pytest-based command."""

import sys
from typing import List

import click
import pytest

from .common import common_click_options, handle_help_flags


def handle_stdout_flags(args: List[str]) -> List[str]:
    """
    If the user has requested to write to stdout, add pytest arguments in order
    to suppress pytest's test session header and summary output.
    """
    writing_to_stdout = False
    if any(arg == "--output=stdout" for arg in args):
        writing_to_stdout = True
    elif "--output" in args:
        output_index = args.index("--output")
        if args[output_index + 1] == "stdout":
            writing_to_stdout = True
    if writing_to_stdout:
        if any(arg == "-n" or arg.startswith("-n=") for arg in args):
            sys.exit("error: xdist-plugin not supported with --output=stdout (remove -n args).")
        args.extend(["-qq", "-s", "--no-html"])
    return args


def handle_fill_command_flags(fill_args: List[str]) -> List[str]:
    """Handle all fill CLI flag pre-processing."""
    args = handle_help_flags(fill_args, pytest_type="fill")
    args = handle_stdout_flags(args)
    return args


@click.command(
    context_settings={
        "ignore_unknown_options": True,
    }
)
@common_click_options
def fill(pytest_args: List[str], **kwargs) -> None:
    """Entry point for the fill command."""
    result = pytest.main(
        handle_fill_command_flags(list(pytest_args)),
    )
    sys.exit(result)


@click.command(
    context_settings={
        "ignore_unknown_options": True,
    }
)
@common_click_options
def phil(pytest_args: List[str], **kwargs) -> None:
    """Friendly alias for the fill command."""
    args = handle_fill_command_flags(list(pytest_args))
    result = pytest.main(
        args
        + [
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
        ],
    )
    sys.exit(result)
