"""
CLI entry point for the `consume` pytest-based command.
"""

import os
import sys
import warnings
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, List

import click
import pytest

from .common import common_click_options, handle_help_flags


def handle_hive_env_flags(args: List[str]) -> List[str]:
    """
    Convert hive environment variables into pytest flags.
    """
    env_var_mappings = {
        # TODO: Align `--sim.limit` regex with pytest -k.
        "HIVE_TEST_PATTERN": ["-k"],
        "HIVE_PARALLELISM": ["-n"],
    }
    for env_var, pytest_flag in env_var_mappings.items():
        value = os.getenv(env_var)
        if value is not None:
            args.extend(pytest_flag + [value])
    if os.getenv("HIVE_RANDOM_SEED") is not None:
        warnings.warn("HIVE_RANDOM_SEED is not yet supported.")
    if os.getenv("HIVE_LOGLEVEL") is not None:
        warnings.warn("HIVE_LOG_LEVEL is not yet supported.")
    return args


def handle_consume_command_flags(
    consume_args: List[str],
    help_flag: bool,
    pytest_help_flag: bool,
    is_hive: bool,
) -> List[str]:
    """
    Handle all consume CLI flag pre-processing.
    """
    args = handle_help_flags(consume_args, help_flag, pytest_help_flag)
    args += ["-c", "pytest-consume.ini"]
    if is_hive:
        args = handle_hive_env_flags(args)
        args += ["-p", "pytest_plugins.pytest_hive.pytest_hive"]
    # Pipe input using stdin if no --input is provided and stdin is not a terminal.
    if not any(arg.startswith("--input") for arg in args) and not sys.stdin.isatty():
        args.extend(["-s", "--input=stdin"])
    # Ensure stdout is captured when timing data is enabled.
    if "--timing-data" in args and "-s" not in args:
        args.append("-s")
    return args


def get_command_paths(command_name: str, is_hive: bool) -> List[Path]:
    """
    Determine the command paths based on the command name and hive flag.
    """
    base_path = Path("src/pytest_plugins/consume")
    if command_name == "hive":
        commands = ["rlp", "engine"]
    else:
        commands = [command_name]

    command_paths = [
        base_path / ("hive_simulators" if is_hive else "") / cmd / f"test_via_{cmd}.py"
        for cmd in commands
    ]
    return command_paths


def consume_command(is_hive: bool = False) -> Callable[[Callable[..., Any]], click.Command]:
    """
    Decorator to generate a consume sub-command.
    """

    def create_command(
        func: Callable[..., Any], command_name: str, command_paths: List[Path], is_hive: bool
    ) -> click.Command:
        """
        Create the command function to be decorated.
        """

        @consume.command(name=command_name, context_settings=dict(ignore_unknown_options=True))
        @common_click_options
        def command(pytest_args: List[str], help_flag: bool, pytest_help_flag: bool) -> None:
            args = handle_consume_command_flags(
                pytest_args,
                help_flag,
                pytest_help_flag,
                is_hive,
            )
            args += [str(p) for p in command_paths]

            if is_hive and not any(arg.startswith("--hive-session-temp-folder") for arg in args):
                with TemporaryDirectory() as temp_dir:
                    args.extend(["--hive-session-temp-folder", temp_dir])
                    result = pytest.main(args)
            else:
                result = pytest.main(args)
            sys.exit(result)

        command.__doc__ = func.__doc__
        return command

    def decorator(func: Callable[..., Any]) -> click.Command:
        command_name = func.__name__
        command_paths = get_command_paths(command_name, is_hive)
        return create_command(func, command_name, command_paths, is_hive)

    return decorator


@click.group()
def consume() -> None:
    """
    Entry point group to aid client consumption of test fixtures.
    """
    pass


@consume_command(is_hive=False)
def direct() -> None:
    """
    Clients consume directly via the `blocktest` interface.
    """
    pass


@consume_command(is_hive=True)
def rlp() -> None:
    """
    Clients consume RLP-encoded blocks on startup.
    """
    pass


@consume_command(is_hive=True)
def engine() -> None:
    """
    Clients consume via the Engine API.
    """
    pass


@consume_command(is_hive=True)
def hive() -> None:
    """
    Clients consume via all available hive methods (rlp, engine).
    """
    pass
