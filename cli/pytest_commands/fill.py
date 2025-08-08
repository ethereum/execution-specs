"""CLI entry point for the `fill` pytest-based command."""

from typing import List

import click

from .base import PytestCommand, PytestExecution, common_pytest_options
from .processors import HelpFlagsProcessor, StdoutFlagsProcessor


class FillCommand(PytestCommand):
    """Pytest command for the fill operation."""

    def __init__(self, **kwargs):
        """Initialize fill command with processors."""
        super().__init__(
            config_file="pytest-fill.ini",
            argument_processors=[
                HelpFlagsProcessor("fill"),
                StdoutFlagsProcessor(),
            ],
            **kwargs,
        )

    def create_executions(self, pytest_args: List[str]) -> List[PytestExecution]:
        """
        Create execution plan that supports two-phase pre-allocation group generation.

        Returns single execution for normal filling, or two-phase execution
        when --generate-pre-alloc-groups or --generate-all-formats is specified.
        """
        processed_args = self.process_arguments(pytest_args)

        # Check if we need two-phase execution
        if self._should_use_two_phase_execution(processed_args):
            processed_args = self._ensure_generate_all_formats_for_tarball(processed_args)
            return self._create_two_phase_executions(processed_args)
        elif "--use-pre-alloc-groups" in processed_args:
            # Only phase 2: using existing pre-allocation groups
            return self._create_single_phase_with_pre_alloc_groups(processed_args)
        else:
            # Normal single-phase execution
            return [
                PytestExecution(
                    config_file=self.config_path,
                    args=processed_args,
                )
            ]

    def _create_two_phase_executions(self, args: List[str]) -> List[PytestExecution]:
        """Create two-phase execution: pre-allocation group generation + fixture filling."""
        # Phase 1: Pre-allocation group generation (clean and minimal output)
        phase1_args = self._create_phase1_args(args)

        # Phase 2: Main fixture generation (full user options)
        phase2_args = self._create_phase2_args(args)

        return [
            PytestExecution(
                config_file=self.config_path,
                args=phase1_args,
                description="generating pre-allocation groups",
            ),
            PytestExecution(
                config_file=self.config_path,
                args=phase2_args,
                description="filling test fixtures",
            ),
        ]

    def _create_single_phase_with_pre_alloc_groups(self, args: List[str]) -> List[PytestExecution]:
        """Create single execution using existing pre-allocation groups."""
        return [
            PytestExecution(
                config_file=self.config_path,
                args=args,
            )
        ]

    def _create_phase1_args(self, args: List[str]) -> List[str]:
        """Create arguments for phase 1 (pre-allocation group generation)."""
        # Start with all args, then remove what we don't want for phase 1
        filtered_args = self._remove_unwanted_phase1_args(args)

        # Add required phase 1 flags (with quiet output by default)
        phase1_args = [
            "--generate-pre-alloc-groups",
            "-qq",  # Quiet pytest output by default (user -v/-vv/-vvv can override)
        ] + filtered_args

        return phase1_args

    def _create_phase2_args(self, args: List[str]) -> List[str]:
        """Create arguments for phase 2 (fixture filling)."""
        # Remove --generate-pre-alloc-groups and --clean, then add --use-pre-alloc-groups
        phase2_args = self._remove_generate_pre_alloc_groups_flag(args)
        phase2_args = self._remove_clean_flag(phase2_args)
        phase2_args = self._add_use_pre_alloc_groups_flag(phase2_args)
        return phase2_args

    def _remove_unwanted_phase1_args(self, args: List[str]) -> List[str]:
        """Remove arguments we don't want in phase 1 (pre-state generation)."""
        unwanted_flags = {
            # Output format flags
            "--html",
            # Report flags (we'll add our own -qq)
            "-q",
            "--quiet",
            "-qq",
            "--tb",
            # Pre-allocation group flags (we'll add our own)
            "--generate-pre-alloc-groups",
            "--use-pre-alloc-groups",
            "--generate-all-formats",
        }

        filtered_args = []
        i = 0
        while i < len(args):
            arg = args[i]

            # Skip unwanted flags
            if arg in unwanted_flags:
                # Skip flag and its value if it takes one
                if arg in ["--html", "--tb", "-n"] and i + 1 < len(args):
                    i += 2  # Skip flag and value
                else:
                    i += 1  # Skip just the flag
            # Skip unwanted flags with = format
            elif any(arg.startswith(f"{flag}=") for flag in unwanted_flags):
                i += 1
            else:
                filtered_args.append(arg)
                i += 1

        return filtered_args

    def _remove_generate_pre_alloc_groups_flag(self, args: List[str]) -> List[str]:
        """Remove --generate-pre-alloc-groups flag but keep --generate-all-formats for phase 2."""
        return [arg for arg in args if arg != "--generate-pre-alloc-groups"]

    def _remove_clean_flag(self, args: List[str]) -> List[str]:
        """Remove --clean flag from argument list."""
        return [arg for arg in args if arg != "--clean"]

    def _add_use_pre_alloc_groups_flag(self, args: List[str]) -> List[str]:
        """Add --use-pre-alloc-groups flag to argument list."""
        return args + ["--use-pre-alloc-groups"]

    def _should_use_two_phase_execution(self, args: List[str]) -> bool:
        """Determine if two-phase execution is needed."""
        return (
            "--generate-pre-alloc-groups" in args
            or "--generate-all-formats" in args
            or self._is_tarball_output(args)
        )

    def _ensure_generate_all_formats_for_tarball(self, args: List[str]) -> List[str]:
        """Auto-add --generate-all-formats for tarball output."""
        if self._is_tarball_output(args) and "--generate-all-formats" not in args:
            return args + ["--generate-all-formats"]
        return args

    def _is_tarball_output(self, args: List[str]) -> bool:
        """Check if output argument specifies a tarball (.tar.gz) path."""
        from pathlib import Path

        for i, arg in enumerate(args):
            if arg.startswith("--output="):
                output_path = Path(arg.split("=", 1)[1])
                return str(output_path).endswith(".tar.gz")
            elif arg == "--output" and i + 1 < len(args):
                output_path = Path(args[i + 1])
                return str(output_path).endswith(".tar.gz")
        return False


class PhilCommand(FillCommand):
    """Friendly fill command with emoji reporting."""

    def create_executions(self, pytest_args: List[str]) -> List[PytestExecution]:
        """Create execution with emoji report options."""
        processed_args = self.process_arguments(pytest_args)

        emoji_args = processed_args + [
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
        ]

        return [
            PytestExecution(
                config_file=self.config_path,
                args=emoji_args,
            )
        ]


@click.command(
    context_settings={
        "ignore_unknown_options": True,
    }
)
@common_pytest_options
def fill(pytest_args: List[str], **kwargs) -> None:
    """Entry point for the fill command."""
    command = FillCommand()
    command.execute(list(pytest_args))


@click.command(
    context_settings={
        "ignore_unknown_options": True,
    }
)
@common_pytest_options
def phil(pytest_args: List[str], **kwargs) -> None:
    """Friendly alias for the fill command."""
    command = PhilCommand()
    command.execute(list(pytest_args))


if __name__ == "__main__":
    # to allow debugging in vscode: in launch config, set "module": "cli.pytest_commands.fill"
    fill(prog_name="fill")
