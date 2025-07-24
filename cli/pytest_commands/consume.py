"""CLI entry point for the `consume` pytest-based command."""

import functools
from pathlib import Path
from typing import Any, Callable, List

import click

from .base import ArgumentProcessor, PytestCommand, common_pytest_options
from .processors import ConsumeCommandProcessor, HelpFlagsProcessor, HiveEnvironmentProcessor


def create_consume_command(
    *,
    command_logic_test_paths: List[Path],
    is_hive: bool = False,
    command_name: str = "",
) -> PytestCommand:
    """Initialize consume command with paths and processors."""
    processors: List[ArgumentProcessor] = [HelpFlagsProcessor("consume")]

    if is_hive:
        processors.extend(
            [
                HiveEnvironmentProcessor(command_name=command_name),
                ConsumeCommandProcessor(is_hive=True),
            ]
        )
    else:
        processors.append(ConsumeCommandProcessor(is_hive=False))

    return PytestCommand(
        config_file="pytest-consume.ini",
        argument_processors=processors,
        command_logic_test_paths=command_logic_test_paths,
    )


def get_command_logic_test_paths(command_name: str, is_hive: bool) -> List[Path]:
    """Determine the command paths based on the command name and hive flag."""
    base_path = Path("pytest_plugins/consume")
    if command_name == "hive":
        commands = ["rlp", "engine"]
        command_logic_test_paths = [
            base_path / "simulators" / "simulator_logic" / f"test_via_{cmd}.py" for cmd in commands
        ]
    elif command_name in ["engine", "rlp"]:
        command_logic_test_paths = [
            base_path / "simulators" / "simulator_logic" / f"test_via_{command_name}.py"
        ]
    elif command_name == "direct":
        command_logic_test_paths = [base_path / "direct" / "test_via_direct.py"]
    else:
        raise ValueError(f"Unexpected command: {command_name}.")
    return command_logic_test_paths


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def consume() -> None:
    """Consume command to aid client consumption of test fixtures."""
    pass


def consume_command(is_hive: bool = False) -> Callable[[Callable[..., Any]], click.Command]:
    """Generate a consume sub-command."""

    def decorator(func: Callable[..., Any]) -> click.Command:
        command_name = func.__name__
        command_help = func.__doc__
        command_logic_test_paths = get_command_logic_test_paths(command_name, is_hive)

        @consume.command(
            name=command_name,
            help=command_help,
            context_settings={"ignore_unknown_options": True},
        )
        @common_pytest_options
        @functools.wraps(func)
        def command(pytest_args: List[str], **kwargs) -> None:
            consume_cmd = create_consume_command(
                command_logic_test_paths=command_logic_test_paths,
                is_hive=is_hive,
                command_name=command_name,
            )
            consume_cmd.execute(list(pytest_args))

        return command

    return decorator


@consume_command(is_hive=False)
def direct() -> None:
    """Clients consume directly via the `blocktest` interface."""
    pass


@consume_command(is_hive=True)
def rlp() -> None:
    """Client consumes RLP-encoded blocks on startup."""
    pass


@consume_command(is_hive=True)
def engine() -> None:
    """Client consumes via the Engine API."""
    pass


@consume_command(is_hive=True)
def hive() -> None:
    """Client consumes via all available hive methods (rlp, engine)."""
    pass


@consume.command(
    context_settings={"ignore_unknown_options": True},
)
@common_pytest_options
def cache(pytest_args: List[str], **kwargs) -> None:
    """Consume command to cache test fixtures."""
    cache_cmd = create_consume_command(command_logic_test_paths=[], is_hive=False)
    cache_cmd.execute(list(pytest_args))
