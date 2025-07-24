"""Base classes and utilities for pytest-based CLI commands."""

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from os.path import realpath
from pathlib import Path
from typing import Any, Callable, List, Optional

import click
import pytest
from rich.console import Console

CURRENT_FOLDER = Path(realpath(__file__)).parent
PACKAGE_INSTALL_FOLDER = CURRENT_FOLDER.parent.parent
PYTEST_INI_FOLDER = CURRENT_FOLDER / "pytest_ini_files"


@dataclass
class PytestExecution:
    """Configuration for a single pytest execution."""

    config_file: Path
    """Path to the pytest configuration file (e.g., 'pytest-fill.ini')."""

    command_logic_test_paths: List[str] = field(default_factory=list)
    """List of tests that have to be appended to the start of pytest command arguments."""

    args: List[str] = field(default_factory=list)
    """Arguments to pass to pytest."""

    description: Optional[str] = None
    """Optional description for this execution phase."""


class ArgumentProcessor(ABC):
    """Base class for processing command-line arguments."""

    @abstractmethod
    def process_args(self, args: List[str]) -> List[str]:
        """Process the given arguments and return modified arguments."""
        pass


@dataclass(kw_only=True)
class PytestRunner:
    """Handles execution of pytest commands."""

    console: Console = field(default_factory=lambda: Console(highlight=False))
    """Console to use for output."""

    def run_single(self, execution: PytestExecution) -> int:
        """Run pytest once with the given configuration and arguments."""
        root_dir_arg = ["--rootdir", "."]
        pytest_args = (
            ["-c", str(execution.config_file)]
            + root_dir_arg
            + [
                str(PACKAGE_INSTALL_FOLDER / test_path)
                for test_path in execution.command_logic_test_paths
            ]
            + execution.args
        )
        if execution.command_logic_test_paths:
            pytest_args += [
                "-p",
                "pytest_plugins.fix_package_test_path",
            ]
        if self._is_verbose(execution.args):
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
                phase_text = (
                    f"[bold blue]phase {i + 1}/{len(executions)}: "
                    f"{execution.description}[/bold blue]"
                )
                self.console.rule(phase_text, style="bold blue")

            result = self.run_single(execution)
            if result != 0:
                return result

        return 0


@dataclass(kw_only=True)
class PytestCommand:
    """
    Base class for pytest-based CLI commands.

    Provides a standard structure for commands that execute pytest
    with specific configurations and argument processing.
    """

    config_file: str
    """File name of the pytest configuration file (e.g., 'pytest-fill.ini')."""

    argument_processors: List[ArgumentProcessor] = field(default_factory=list)
    """Processors to apply to the pytest arguments."""

    runner: PytestRunner = field(default_factory=PytestRunner)
    """Runner to execute the pytest command."""

    plugins: List[str] = field(default_factory=list)
    """Plugins to load for the pytest command."""

    command_logic_test_paths: List[Path] | None = None
    """Path to test files that contain the command logic."""

    pytest_ini_folder: Path = PYTEST_INI_FOLDER
    """Folder where the pytest configuration files are located."""

    @property
    def config_path(self) -> Path:
        """Path to the pytest configuration file."""
        return self.pytest_ini_folder / self.config_file

    def execute(self, pytest_args: List[str]) -> None:
        """Execute the command with the given pytest arguments."""
        executions = self.create_executions(pytest_args)
        result = self.runner.run_multiple(executions)
        sys.exit(result)

    @property
    def test_args(self) -> List[str]:
        """
        Return the test-path arguments that have to be appended to all PytestExecution
        instances.
        """
        if self.command_logic_test_paths:
            return [str(path) for path in self.command_logic_test_paths]
        return []

    def create_executions(self, pytest_args: List[str]) -> List[PytestExecution]:
        """
        Create the list of pytest executions for this command.

        This method can be overridden by subclasses to implement
        multi-phase execution (e.g., for future fill command).
        """
        processed_args = self.process_arguments(pytest_args)
        return [
            PytestExecution(
                config_file=self.config_path,
                command_logic_test_paths=self.test_args,
                args=processed_args,
            )
        ]

    def process_arguments(self, args: List[str]) -> List[str]:
        """Apply all argument processors to the given arguments."""
        processed_args = args[:]

        for processor in self.argument_processors:
            processed_args = processor.process_args(processed_args)

        for plugin in self.plugins:
            processed_args.extend(["-p", plugin])

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
