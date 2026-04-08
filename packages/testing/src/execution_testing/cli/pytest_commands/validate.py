"""CLI entry point for the `validate` pytest-based command."""

from pathlib import Path
from typing import Any, List

import click

from .base import ArgumentProcessor, PytestCommand, common_pytest_options
from .processors import ConsumeCommandProcessor, HelpFlagsProcessor


def get_validate_test_paths(command_name: str) -> List[Path]:
    """Determine test paths based on the validate subcommand name."""
    base_path = Path("cli/pytest_commands/plugins/validate")
    if command_name in ("state", "block", "engine"):
        return [base_path / "test_validate.py"]
    elif command_name == "health":
        return [base_path / "health" / "test_health.py"]
    else:
        raise ValueError(f"Unexpected validate command: {command_name}.")


def create_validate_command(
    *,
    command_logic_test_paths: List[Path],
) -> PytestCommand:
    """Initialize validate command with paths and processors."""
    processors: List[ArgumentProcessor] = [
        HelpFlagsProcessor("validate"),
        ConsumeCommandProcessor(is_hive=False),
    ]
    return PytestCommand(
        config_file="pytest-validate.ini",
        argument_processors=processors,
        command_logic_test_paths=command_logic_test_paths,
    )


class SectionedGroup(click.Group):
    """Click group that displays commands in sections."""

    sections = {
        "Test Types": ["state", "block", "engine"],
        "Utilities": ["health"],
    }

    def format_commands(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        """Write commands in sections."""
        for section, names in self.sections.items():
            cmds = []
            for name in names:
                cmd = self.get_command(ctx, name)
                if cmd is None:
                    continue
                help_text = cmd.get_short_help_str(limit=150)
                cmds.append((name, help_text))
            if cmds:
                with formatter.section(section):
                    formatter.write_dl(cmds)


@click.group(
    cls=SectionedGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.pass_context
def validate(ctx: click.Context) -> None:
    """Validate client EVM implementations against test fixtures."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


def _run_validate(
    test_type: str,
    clients: tuple[str, ...],
    pytest_args: List[str],
    help_flag: bool = False,
) -> None:
    """Common logic for state/block/engine subcommands."""
    if not clients:
        click.echo(
            f"Note: --client is required. "
            f"Example: validate {test_type} --client geth\n"
        )
        help_flag = True
    if help_flag:
        # Show filtered help via --validate-help
        args = ["--validate-help"]
        cmd = create_validate_command(
            command_logic_test_paths=get_validate_test_paths(test_type),
        )
        cmd.execute(args)
        return
    args = list(pytest_args)
    args.extend(["--validate-type", test_type])
    args.extend(["--validate-clients", ",".join(clients)])
    cmd = create_validate_command(
        command_logic_test_paths=get_validate_test_paths(test_type),
    )
    cmd.execute(args)


@validate.command(
    name="state",
    context_settings={"ignore_unknown_options": True, "help_option_names": ["-h", "--help"]},
)
@click.option(
    "--client",
    "clients",
    multiple=True,
    help="Client name (e.g. geth, besu). Can be used multiple times.",
)
@common_pytest_options
def state(
    clients: tuple[str, ...], pytest_args: List[str], **kwargs: Any
) -> None:
    """Validate client state test implementations."""
    _run_validate("state", clients, list(pytest_args), kwargs.get("help_flag", False))


@validate.command(
    name="block",
    context_settings={"ignore_unknown_options": True, "help_option_names": ["-h", "--help"]},
)
@click.option(
    "--client",
    "clients",
    multiple=True,
    help="Client name (e.g. geth, besu). Can be used multiple times.",
)
@common_pytest_options
def block(
    clients: tuple[str, ...], pytest_args: List[str], **kwargs: Any
) -> None:
    """Validate client block test implementations."""
    _run_validate("block", clients, list(pytest_args), kwargs.get("help_flag", False))


@validate.command(
    name="engine",
    context_settings={"ignore_unknown_options": True, "help_option_names": ["-h", "--help"]},
)
@click.option(
    "--client",
    "clients",
    multiple=True,
    help="Client name (e.g. geth, besu). Can be used multiple times.",
)
@common_pytest_options
def engine(
    clients: tuple[str, ...], pytest_args: List[str], **kwargs: Any
) -> None:
    """Validate client engine test implementations."""
    _run_validate("engine", clients, list(pytest_args), kwargs.get("help_flag", False))


@validate.command(
    name="health",
    context_settings={"ignore_unknown_options": True, "help_option_names": ["-h", "--help"]},
)
@click.option(
    "--client",
    "clients",
    multiple=True,
    default=(),
    help="Filter health checks to specific client(s).",
)
@common_pytest_options
def health(
    clients: tuple[str, ...], pytest_args: List[str], **kwargs: Any
) -> None:
    """Run health checks for configured client binaries."""
    del kwargs
    args = list(pytest_args)
    if "-v" not in args and "--verbose" not in args:
        args.insert(0, "-v")
    if clients:
        k_expr = " or ".join(clients)
        args.extend(["-k", k_expr])
    cmd = create_validate_command(
        command_logic_test_paths=get_validate_test_paths("health"),
    )
    cmd.execute(args)
