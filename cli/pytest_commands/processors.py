"""Argument processors for different pytest command types."""

import os
import sys
import warnings
from typing import List

import click

from .base import ArgumentProcessor


class HelpFlagsProcessor(ArgumentProcessor):
    """Processes help-related flags to provide cleaner help output."""

    def __init__(self, command_type: str):
        """
        Initialize the help processor.

        Args:
            command_type: The type of command (e.g., "fill", "consume", "execute")

        """
        self.command_type = command_type

    def process_args(self, args: List[str]) -> List[str]:
        """
        Modify help arguments to provide cleaner help output.

        This makes `--help` more useful because `pytest --help` is extremely
        verbose and lists all flags from pytest and pytest plugins.
        """
        ctx = click.get_current_context()

        if ctx.params.get("help_flag"):
            return [f"--{self.command_type}-help"]
        elif ctx.params.get("pytest_help_flag"):
            return ["--help"]

        return args


class StdoutFlagsProcessor(ArgumentProcessor):
    """Processes stdout-related flags for the fill command."""

    def process_args(self, args: List[str]) -> List[str]:
        """
        If the user has requested to write to stdout, add pytest arguments
        to suppress pytest's test session header and summary output.
        """
        if not self._is_writing_to_stdout(args):
            return args

        # Check for incompatible xdist plugin
        if any(arg == "-n" or arg.startswith("-n=") for arg in args):
            sys.exit("error: xdist-plugin not supported with --output=stdout (remove -n args).")

        # Add flags to suppress pytest output when writing to stdout
        return args + ["-qq", "-s", "--no-html"]

    def _is_writing_to_stdout(self, args: List[str]) -> bool:
        """Check if the command is configured to write to stdout."""
        if any(arg == "--output=stdout" for arg in args):
            return True

        if "--output" in args:
            output_index = args.index("--output")
            if output_index + 1 < len(args) and args[output_index + 1] == "stdout":
                return True

        return False


class HiveEnvironmentProcessor(ArgumentProcessor):
    """Processes Hive environment variables for consume commands."""

    def process_args(self, args: List[str]) -> List[str]:
        """Convert hive environment variables into pytest flags."""
        modified_args = args[:]

        hive_test_pattern = os.getenv("HIVE_TEST_PATTERN")
        if hive_test_pattern and not self._has_regex_or_sim_limit(args):
            modified_args.extend(["--sim.limit", hive_test_pattern])

        hive_parallelism = os.getenv("HIVE_PARALLELISM")
        if hive_parallelism not in [None, "", "1"] and not self._has_parallelism_flag(args):
            modified_args.extend(["-n", str(hive_parallelism)])

        if os.getenv("HIVE_RANDOM_SEED") is not None:
            warnings.warn("HIVE_RANDOM_SEED is not yet supported.", stacklevel=2)

        if os.getenv("HIVE_LOGLEVEL") is not None:
            warnings.warn("HIVE_LOG_LEVEL is not yet supported.", stacklevel=2)

        modified_args.extend(["-p", "pytest_plugins.pytest_hive.pytest_hive"])

        return modified_args

    def _has_regex_or_sim_limit(self, args: List[str]) -> bool:
        """Check if args already contain --regex or --sim.limit."""
        return "--regex" in args or "--sim.limit" in args

    def _has_parallelism_flag(self, args: List[str]) -> bool:
        """Check if args already contain parallelism flag."""
        return "-n" in args


class ConsumeCommandProcessor(ArgumentProcessor):
    """Processes consume-specific command arguments."""

    def __init__(self, is_hive: bool = False):
        """
        Initialize the consume processor.

        Args:
            is_hive: Whether this is a hive-based consume command

        """
        self.is_hive = is_hive

    def process_args(self, args: List[str]) -> List[str]:
        """Process consume-specific arguments."""
        if self.is_hive:
            return self._handle_timing_data_stdout(args)
        return args

    def _handle_timing_data_stdout(self, args: List[str]) -> List[str]:
        """Ensure stdout is captured when timing data is enabled."""
        if "--timing-data" in args and "-s" not in args:
            return args + ["-s"]
        return args
