"""CLI entry point for the `build-block` pytest-based command."""

from pathlib import Path
from typing import Any, List

import click

from .base import PytestCommand, common_pytest_options
from .processors import (
    ConsumeCommandProcessor,
    HelpFlagsProcessor,
    HiveEnvironmentProcessor,
)


def create_build_block_command() -> PytestCommand:
    """Initialize the build-block command with paths and processors."""
    base_path = Path("cli/pytest_commands/plugins/consume")
    command_logic_test_paths = [
        base_path / "simulators" / "simulator_logic" / "test_via_build.py"
    ]
    return PytestCommand(
        config_file="pytest-consume.ini",
        argument_processors=[
            HelpFlagsProcessor("consume"),
            HiveEnvironmentProcessor(command_name="build_block"),
            ConsumeCommandProcessor(is_hive=True),
        ],
        command_logic_test_paths=command_logic_test_paths,
    )


@click.command(
    name="build-block",
    context_settings={"ignore_unknown_options": True},
)
@common_pytest_options
def build_block(pytest_args: List[str], **kwargs: Any) -> None:
    """Test block building via testing_buildBlockV1."""
    del kwargs

    cmd = create_build_block_command()
    cmd.execute(list(pytest_args))
