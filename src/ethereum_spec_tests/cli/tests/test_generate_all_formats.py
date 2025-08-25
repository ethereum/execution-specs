"""Test the --generate-all-formats CLI flag functionality."""

from unittest.mock import patch

from cli.pytest_commands.fill import FillCommand


def test_generate_all_formats_creates_two_phase_execution():
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


def test_generate_all_formats_preserves_other_args():
    """Test that --generate-all-formats preserves other command line arguments."""
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


def test_generate_all_formats_removes_clean_from_phase2():
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


def test_legacy_generate_pre_alloc_groups_still_works():
    """Test that the legacy --generate-pre-alloc-groups flag still works."""
    command = FillCommand()

    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        pytest_args = ["--generate-pre-alloc-groups", "tests/somedir/"]
        executions = command.create_executions(pytest_args)

    assert len(executions) == 2

    # Phase 1: Should have --generate-pre-alloc-groups
    phase1_args = executions[0].args
    assert "--generate-pre-alloc-groups" in phase1_args

    # Phase 2: Should have --use-pre-alloc-groups but NOT --generate-all-formats
    phase2_args = executions[1].args
    assert "--use-pre-alloc-groups" in phase2_args
    assert "--generate-all-formats" not in phase2_args
    assert "--generate-pre-alloc-groups" not in phase2_args


def test_single_phase_without_flags():
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


def test_tarball_output_auto_enables_generate_all_formats():
    """Test that tarball output automatically enables --generate-all-formats."""
    command = FillCommand()

    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        pytest_args = ["--output=fixtures.tar.gz", "tests/somedir/"]
        executions = command.create_executions(pytest_args)

    # Should trigger two-phase execution due to tarball output
    assert len(executions) == 2

    # Phase 1: Should have --generate-pre-alloc-groups
    phase1_args = executions[0].args
    assert "--generate-pre-alloc-groups" in phase1_args

    # Phase 2: Should have --generate-all-formats (auto-added) and --use-pre-alloc-groups
    phase2_args = executions[1].args
    assert "--generate-all-formats" in phase2_args
    assert "--use-pre-alloc-groups" in phase2_args
    assert "--output=fixtures.tar.gz" in phase2_args


def test_tarball_output_with_explicit_generate_all_formats():
    """Test that explicit --generate-all-formats with tarball output works correctly."""
    command = FillCommand()

    with patch.object(command, "process_arguments", side_effect=lambda x: x):
        pytest_args = ["--output=fixtures.tar.gz", "--generate-all-formats", "tests/somedir/"]
        executions = command.create_executions(pytest_args)

    # Should trigger two-phase execution
    assert len(executions) == 2

    # Phase 2: Should have --generate-all-formats (explicit, not duplicated)
    phase2_args = executions[1].args
    assert "--generate-all-formats" in phase2_args
    # Ensure no duplicate flags
    assert phase2_args.count("--generate-all-formats") == 1


def test_regular_output_does_not_auto_trigger_two_phase():
    """Test that regular directory output doesn't auto-trigger two-phase execution."""
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


def test_tarball_output_detection_various_formats():
    """Test tarball output detection with various argument formats."""
    command = FillCommand()

    # Test --output=file.tar.gz format
    args1 = ["--output=test.tar.gz", "tests/somedir/"]
    assert command._is_tarball_output(args1) is True

    # Test --output file.tar.gz format
    args2 = ["--output", "test.tar.gz", "tests/somedir/"]
    assert command._is_tarball_output(args2) is True

    # Test regular directory
    args3 = ["--output=test/", "tests/somedir/"]
    assert command._is_tarball_output(args3) is False

    # Test no output argument
    args4 = ["tests/somedir/"]
    assert command._is_tarball_output(args4) is False
