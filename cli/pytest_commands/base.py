"""Base classes and utilities for pytest-based CLI commands."""

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import click
import pytest
from rich.console import Console


@dataclass
class PytestExecution:
    """Configuration for a single pytest execution."""

    config_file: str
    """Path to the pytest configuration file (e.g., 'pytest.ini')."""

    args: List[str]
    """Arguments to pass to pytest."""

    description: Optional[str] = None
    """Optional description for this execution phase."""


class ArgumentProcessor(ABC):
    """Base class for processing command-line arguments."""

    @abstractmethod
    def process_args(self, args: List[str]) -> List[str]:
        """Process the given arguments and return modified arguments."""
        pass


class PytestRunner:
    """Handles execution of pytest commands."""

    def __init__(self):
        """Initialize the pytest runner with a console for output."""
        self.console = Console(highlight=False)

    def run_single(self, config_file: str, args: List[str]) -> int:
        """Run pytest once with the given configuration and arguments."""
        pytest_args = ["-c", config_file] + args

        if self._is_verbose(args):
            pytest_cmd = f"pytest {' '.join(pytest_args)}"
            self.console.print(f"Executing: [bold]{pytest_cmd}[/bold]")

        return pytest.main(pytest_args)

    def _is_verbose(self, args: List[str]) -> bool:
        """Check if verbose output is requested."""
        return any(arg in ["-v", "--verbose", "-vv", "-vvv"] for arg in args)

    def run_multiple(self, executions: List[PytestExecution]) -> int:
        """
        Run multiple pytest executions in sequence.

        Returns the exit code of the final execution, or the first non-zero exit code.
        """
        for i, execution in enumerate(executions):
            if execution.description and len(executions) > 1:
                self.console.print(
                    f"Phase {i + 1}/{len(executions)}: [italic]{execution.description}[/italic]"
                )

            result = self.run_single(execution.config_file, execution.args)
            if result != 0:
                return result

        return 0


class PytestCommand:
    """
    Base class for pytest-based CLI commands.

    Provides a standard structure for commands that execute pytest
    with specific configurations and argument processing.
    """

    def __init__(
        self,
        config_file: str,
        argument_processors: Optional[List[ArgumentProcessor]] = None,
    ):
        """
        Initialize the pytest command.

        Args:
            config_file: Pytest configuration file to use
            argument_processors: List of processors to apply to arguments

        """
        self.config_file = config_file
        self.argument_processors = argument_processors or []
        self.runner = PytestRunner()

    def execute(self, pytest_args: List[str]) -> None:
        """Execute the command with the given pytest arguments."""
        executions = self.create_executions(pytest_args)
        result = self.runner.run_multiple(executions)
        sys.exit(result)

    def create_executions(self, pytest_args: List[str]) -> List[PytestExecution]:
        """
        Create the list of pytest executions for this command.

        This method can be overridden by subclasses to implement
        multi-phase execution (e.g., for future fill command).
        """
        processed_args = self.process_arguments(pytest_args)

        return [
            PytestExecution(
                config_file=self.config_file,
                args=processed_args,
            )
        ]

    def process_arguments(self, args: List[str]) -> List[str]:
        """Apply all argument processors to the given arguments."""
        processed_args = args[:]

        for processor in self.argument_processors:
            processed_args = processor.process_args(processed_args)

        return processed_args


def common_pytest_options(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Apply common Click options for pytest-based commands.

    This decorator adds the standard help options that all pytest commands use.
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


def create_pytest_command_decorator(
    config_file: str,
    argument_processors: Optional[List[ArgumentProcessor]] = None,
    context_settings: Optional[Dict[str, Any]] = None,
) -> Callable[[Callable[..., Any]], click.Command]:
    """
    Create a Click command decorator for a pytest-based command.

    Args:
        config_file: Pytest configuration file to use
        argument_processors: List of argument processors to apply
        context_settings: Additional Click context settings

    Returns:
        A decorator that creates a Click command executing pytest

    """
    default_context_settings = {"ignore_unknown_options": True}
    if context_settings:
        default_context_settings.update(context_settings)

    def decorator(func: Callable[..., Any]) -> click.Command:
        command = PytestCommand(config_file, argument_processors)

        @click.command(
            context_settings=default_context_settings,
        )
        @common_pytest_options
        @wraps(func)
        def wrapper(pytest_args: List[str], **kwargs) -> None:
            command.execute(list(pytest_args))

        return wrapper

    return decorator
