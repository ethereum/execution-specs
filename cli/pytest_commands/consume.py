"""CLI entry point for the `consume` pytest-based command."""

import functools
from pathlib import Path
from typing import Any, Callable, List

import click

from .base import ArgumentProcessor, PytestCommand, PytestExecution, common_pytest_options
from .processors import ConsumeCommandProcessor, HelpFlagsProcessor, HiveEnvironmentProcessor


class ConsumeCommand(PytestCommand):
    """Pytest command for consume operations."""

    def __init__(self, command_paths: List[Path], is_hive: bool = False):
        """Initialize consume command with paths and processors."""
        processors: List[ArgumentProcessor] = [HelpFlagsProcessor("consume")]

        if is_hive:
            processors.extend(
                [
                    HiveEnvironmentProcessor(),
                    ConsumeCommandProcessor(is_hive=True),
                ]
            )
        else:
            processors.append(ConsumeCommandProcessor(is_hive=False))

        super().__init__(
            config_file="pytest-consume.ini",
            argument_processors=processors,
        )
        self.command_paths = command_paths

    def create_executions(self, pytest_args: List[str]) -> List[PytestExecution]:
        """Create execution with test paths prepended."""
        processed_args = self.process_arguments(pytest_args)

        # Prepend test paths to arguments
        test_path_args = [str(p) for p in self.command_paths]
        final_args = test_path_args + processed_args

        return [
            PytestExecution(
                config_file=self.config_file,
                args=final_args,
            )
        ]


def get_command_paths(command_name: str, is_hive: bool) -> List[Path]:
    """Determine the command paths based on the command name and hive flag."""
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


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def consume() -> None:
    """Consume command to aid client consumption of test fixtures."""
    pass


def consume_command(is_hive: bool = False) -> Callable[[Callable[..., Any]], click.Command]:
    """Generate a consume sub-command."""

    def decorator(func: Callable[..., Any]) -> click.Command:
        command_name = func.__name__
        command_help = func.__doc__
        command_paths = get_command_paths(command_name, is_hive)

        @consume.command(
            name=command_name,
            help=command_help,
            context_settings={"ignore_unknown_options": True},
        )
        @common_pytest_options
        @functools.wraps(func)
        def command(pytest_args: List[str], **kwargs) -> None:
            consume_cmd = ConsumeCommand(command_paths, is_hive)
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
    cache_cmd = ConsumeCommand([], is_hive=False)
    cache_cmd.execute(list(pytest_args))
