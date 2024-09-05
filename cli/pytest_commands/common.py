"""
Common functions for CLI pytest-based entry points.
"""

from typing import Any, Callable, List

import click

Decorator = Callable[[Callable[..., Any]], Callable[..., Any]]


def common_click_options(func: Callable[..., Any]) -> Decorator:
    """
    Define common click options for fill and other pytest-based commands.

    Note that we don't verify any other options here, rather pass them
    directly to the pytest command for processing.
    """
    func = click.option(
        "-h",
        "--help",
        "help_flag",
        is_flag=True,
        default=False,
        expose_value=True,
        help="Show help message.",
    )(func)

    func = click.option(
        "--pytest-help",
        "pytest_help_flag",
        is_flag=True,
        default=False,
        expose_value=True,
        help="Show pytest's help message.",
    )(func)

    return click.argument("pytest_args", nargs=-1, type=click.UNPROCESSED)(func)


def handle_help_flags(pytest_args: List[str], pytest_type: str) -> List[str]:
    """
    Modifies the help arguments passed to the click CLI command before forwarding to
    the pytest command.

    This is to make `--help` more useful because `pytest --help` is extremely
    verbose and lists all flags from pytest and pytest plugins.
    """
    ctx = click.get_current_context()

    if ctx.params.get("help_flag"):
        return [f"--{pytest_type}-help"] if pytest_type in {"consume", "fill"} else pytest_args
    elif ctx.params.get("pytest_help_flag"):
        return ["--help"]

    return pytest_args
