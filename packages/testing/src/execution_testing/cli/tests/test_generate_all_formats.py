"""Test the --generate-all-formats CLI flag functionality."""

from unittest.mock import patch

import click
import pytest

from execution_testing.cli.pytest_commands.fill import (
    FillCommand,
)


def test_generate_all_formats_creates_two_phase_execution() -> None:
    """Test that --generate-all-formats triggers two-phase execution."""
    command = FillCommand()

    # Mock the argument processing to bypass click context requirements
    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        # Test that --generate-all-formats triggers two-phase execution
        pytest_args = ["--generate-all-formats", "tests/somedir/"]
        executions = command.create_executions(pytest_args)

    assert len(executions) == 2, "Expected two-phase execution"

    # Phase 1: Should have --generate-pre-alloc-groups
    phase1_args = executions[0].args
    assert "--generate-pre-alloc-groups" in phase1_args
    assert "--generate-all-formats" not in phase1_args

    # Phase 2: Should have --use-pre-alloc-groups and --generate-all-formats
    phase2_args = executions[1].args
    assert "--use-pre-alloc-groups" in phase2_args
    assert "--generate-all-formats" in phase2_args
    assert "--generate-pre-alloc-groups" not in phase2_args


def test_generate_all_formats_preserves_other_args() -> None:
    """
    Test that --generate-all-formats preserves other command line arguments.
    """
    command = FillCommand()

    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        pytest_args = [
            "--generate-all-formats",
            "--output=custom-output",
            "--fork=Paris",
            "-v",
            "tests/somedir/",
        ]
        executions = command.create_executions(pytest_args)

    assert len(executions) == 2

    # Both phases should preserve most args
    for execution in executions:
        assert "--output=custom-output" in execution.args
        assert "--fork=Paris" in execution.args
        assert "-v" in execution.args
        assert "tests/somedir/" in execution.args


def test_generate_all_formats_removes_clean_from_phase2() -> None:
    """Test that --clean is removed from phase 2."""
    command = FillCommand()

    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        pytest_args = ["--generate-all-formats", "--clean", "tests/somedir/"]
        executions = command.create_executions(pytest_args)

    assert len(executions) == 2

    # Phase 1: Actually keeps --clean (it's needed for cleaning before phase 1)
    # Note: --clean actually remains in phase 1 args but gets filtered out
    # in _remove_unwanted_phase1_args

    # Phase 2: Should not have --clean (gets removed)
    phase2_args = executions[1].args
    assert "--clean" not in phase2_args


def test_generate_pre_alloc_groups_alone_is_phase_1_only() -> None:
    """
    Test that --generate-pre-alloc-groups without --generate-all-formats
    runs phase 1 only, so CI can populate pre-alloc groups on a
    dedicated runner without wasting time on phase 2.
    """
    command = FillCommand()

    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        pytest_args = ["--generate-pre-alloc-groups", "tests/somedir/"]
        executions = command.create_executions(pytest_args)

    assert len(executions) == 1

    phase1_args = executions[0].args
    assert "--generate-pre-alloc-groups" in phase1_args
    assert "--use-pre-alloc-groups" not in phase1_args
    assert "--generate-all-formats" not in phase1_args


def test_use_pre_alloc_groups_forces_single_phase() -> None:
    """
    Test that --use-pre-alloc-groups always runs a single phase, even
    alongside --generate-all-formats (pre-alloc groups already exist on
    disk from a previous run).
    """
    command = FillCommand()

    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        pytest_args = [
            "--use-pre-alloc-groups",
            "--generate-all-formats",
            "tests/somedir/",
        ]
        executions = command.create_executions(pytest_args)

    assert len(executions) == 1
    assert "--use-pre-alloc-groups" in executions[0].args
    assert "--generate-all-formats" in executions[0].args


def test_use_and_generate_pre_alloc_groups_together_is_rejected() -> None:
    """
    --use-pre-alloc-groups + --generate-pre-alloc-groups are contradictory:
    the first asserts the groups exist, the second regenerates them.
    """
    command = FillCommand()

    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        pytest_args = [
            "--use-pre-alloc-groups",
            "--generate-pre-alloc-groups",
            "tests/somedir/",
        ]
        with pytest.raises(click.UsageError, match="mutually exclusive"):
            command.create_executions(pytest_args)


def test_use_pre_alloc_groups_with_clean_is_rejected() -> None:
    """
    --use-pre-alloc-groups + --clean is contradictory: --clean wipes the
    output directory that holds the pre-alloc groups.
    """
    command = FillCommand()

    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        pytest_args = [
            "--use-pre-alloc-groups",
            "--clean",
            "tests/somedir/",
        ]
        with pytest.raises(click.UsageError, match="--clean"):
            command.create_executions(pytest_args)


def test_single_phase_without_flags() -> None:
    """Test that normal execution without flags creates single phase."""
    command = FillCommand()

    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        pytest_args = ["tests/somedir/"]
        executions = command.create_executions(pytest_args)

    assert len(executions) == 1
    execution = executions[0]

    assert "--generate-pre-alloc-groups" not in execution.args
    assert "--use-pre-alloc-groups" not in execution.args
    assert "--generate-all-formats" not in execution.args


def test_tarball_output_without_flag_stays_single_phase() -> None:
    """
    Test that tarball output without --generate-all-formats is single-phase
    and does not inject the flag.
    """
    command = FillCommand()

    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        pytest_args = ["--output=fixtures.tar.gz", "tests/somedir/"]
        executions = command.create_executions(pytest_args)

    assert len(executions) == 1
    execution = executions[0]

    assert "--generate-pre-alloc-groups" not in execution.args
    assert "--use-pre-alloc-groups" not in execution.args
    assert "--generate-all-formats" not in execution.args
    assert "--output=fixtures.tar.gz" in execution.args


def test_tarball_output_with_explicit_generate_all_formats() -> None:
    """
    Test that explicit --generate-all-formats with tarball output works
    correctly.
    """
    command = FillCommand()

    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        pytest_args = [
            "--output=fixtures.tar.gz",
            "--generate-all-formats",
            "tests/somedir/",
        ]
        executions = command.create_executions(pytest_args)

    # Should trigger two-phase execution
    assert len(executions) == 2

    # Phase 2: Should have --generate-all-formats (explicit, not duplicated)
    phase2_args = executions[1].args
    assert "--generate-all-formats" in phase2_args
    # Ensure no duplicate flags
    assert phase2_args.count("--generate-all-formats") == 1


def test_regular_output_does_not_auto_trigger_two_phase() -> None:
    """
    Test that regular directory output doesn't auto-trigger two-phase
    execution.
    """
    command = FillCommand()

    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        pytest_args = ["--output=fixtures/", "tests/somedir/"]
        executions = command.create_executions(pytest_args)

    # Should remain single-phase execution
    assert len(executions) == 1
    execution = executions[0]

    assert "--generate-pre-alloc-groups" not in execution.args
    assert "--use-pre-alloc-groups" not in execution.args
    assert "--generate-all-formats" not in execution.args
