"""Tests for the checklist command click CLI."""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from ..pytest_commands.checklist import checklist


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Click CliRunner for invoking command-line interfaces."""
    return CliRunner()


def _captured_execute_args(runner: CliRunner, *cli_args: str) -> list[str]:
    """Invoke `checklist` and return the args passed to ChecklistCommand."""
    with patch(
        "execution_testing.cli.pytest_commands.checklist.ChecklistCommand"
    ) as mock_cls:
        result = runner.invoke(checklist, list(cli_args))
    assert result.exit_code == 0, result.output
    instance = mock_cls.return_value
    instance.execute.assert_called_once()
    (execute_args,) = instance.execute.call_args.args
    return execute_args


def test_checklist_default_injects_include_benchmark(
    runner: CliRunner,
) -> None:
    """Default invocation passes `tests` plus `--include-benchmark`."""
    args = _captured_execute_args(runner)

    assert "--include-benchmark" in args
    assert args[-1] == "tests"


def test_checklist_explicit_paths_skip_include_benchmark(
    runner: CliRunner,
) -> None:
    """Explicit paths scope collection and drop `--include-benchmark`."""
    args = _captured_execute_args(runner, "tests/prague/eip7702_set_code_tx")

    assert "--include-benchmark" not in args
    assert "tests/prague/eip7702_set_code_tx" in args
    assert "tests" not in args
