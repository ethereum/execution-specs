"""Test the filler plugin's output directory handling."""

from pathlib import Path
from typing import Any, Callable
from unittest.mock import patch

import pytest
from pytest import TempPathFactory

from ..fixture_output import FixtureOutput

MINIMAL_TEST_FILE_NAME = "test_example.py"
MINIMAL_TEST_CONTENTS = """
from ethereum_test_tools import Transaction
def test_function(state_test, pre) -> None:
    tx = Transaction(to=0, gas_limit=21_000, sender=pre.fund_eoa())
    state_test(pre=pre, post={}, tx=tx)
"""


@pytest.fixture
def minimal_test_path(pytester: pytest.Pytester) -> Path:
    """
    Minimal test file that's written to a file using pytester and ready to
    fill.
    """
    tests_dir = pytester.mkdir("tests")
    test_file = tests_dir / MINIMAL_TEST_FILE_NAME
    test_file.write_text(MINIMAL_TEST_CONTENTS)
    return test_file


@pytest.fixture(scope="module")
def fill_fork_from() -> str:
    """Specify the value for `fill`'s `--from` argument."""
    return "Paris"


@pytest.fixture(scope="module")
def fill_fork_until() -> str:
    """Specify the value for `fill`'s `--until` argument."""
    return "Cancun"


@pytest.fixture
def run_fill(
    pytester: pytest.Pytester,
    minimal_test_path: Path,
    fill_fork_from: str,
    fill_fork_until: str,
) -> Callable[..., pytest.RunResult]:
    """
    Create a function to run the fill command with various output directory
    scenarios.
    """

    def _run_fill(
        output_dir: Path,
        clean: bool = False,
        expect_failure: bool = False,
        disable_capture_output: bool = False,
    ) -> pytest.RunResult:
        """
        Run the fill command with the specified output directory and clean
        flag.
        """
        pytester.copy_example(
            name="src/cli/pytest_commands/pytest_ini_files/pytest-fill.ini"
        )
        args = [
            "-c",
            "pytest-fill.ini",
            "-m",
            "(not blockchain_test_engine) and (not eip_version_check)",
            f"--from={fill_fork_from}",
            f"--until={fill_fork_until}",
            f"--output={str(output_dir)}",
            str(minimal_test_path),
        ]
        if clean:
            args.append("--clean")
        if disable_capture_output:
            # Required for tests on stdout
            args.append("-s")

        result = pytester.runpytest(*args)

        if expect_failure:
            assert result.ret != 0, (
                "Fill command was expected to fail but succeeded"
            )
        else:
            assert result.ret == 0, f"Fill command failed:\n{result.outlines}"

        return result

    return _run_fill


def test_fill_to_empty_directory(
    tmp_path_factory: TempPathFactory, run_fill: Any
) -> None:
    """Test filling to a new, empty directory."""
    output_dir = tmp_path_factory.mktemp("empty_fixtures")

    run_fill(output_dir)

    assert any(output_dir.glob("state_tests/**/*.json")), (
        "No fixture files were created"
    )
    assert (output_dir / ".meta").exists(), (
        "Metadata directory was not created"
    )


def test_fill_to_nonexistent_directory(
    tmp_path_factory: TempPathFactory, run_fill: Any
) -> None:
    """Test filling to a nonexistent directory."""
    base_dir = tmp_path_factory.mktemp("base")
    output_dir = base_dir / "nonexistent_fixtures"

    run_fill(output_dir)

    assert any(output_dir.glob("state_tests/**/*.json")), (
        "No fixture files were created"
    )
    assert (output_dir / ".meta").exists(), (
        "Metadata directory was not created"
    )


def test_fill_to_nonempty_directory_fails(
    tmp_path_factory: TempPathFactory, run_fill: Any
) -> None:
    """Test filling to a non-empty directory fails without --clean."""
    # Create a directory with a file
    output_dir = tmp_path_factory.mktemp("nonempty_fixtures")
    (output_dir / "existing_file.txt").write_text(
        "This directory is not empty"
    )

    result: pytest.RunResult = run_fill(output_dir, expect_failure=True)
    outlines = result.errlines
    assert isinstance(outlines, list)

    assert any("is not empty" in line for line in outlines), (
        f"Expected error about non-empty directory: {outlines}"
    )
    assert any("Use --clean" in line for line in outlines), (
        f"Expected suggestion to use --clean flag: {outlines}"
    )


def test_fill_to_nonempty_directory_with_clean(
    tmp_path_factory: TempPathFactory, run_fill: Any
) -> None:
    """Test filling to a non-empty directory succeeds with --clean."""
    # Create a directory with a file
    output_dir = tmp_path_factory.mktemp("nonempty_fixtures_clean")
    (output_dir / "existing_file.txt").write_text(
        "This directory will be cleaned"
    )

    run_fill(output_dir, clean=True)

    # Verify the existing file was removed
    assert not (output_dir / "existing_file.txt").exists(), (
        "Existing file was not removed"
    )

    assert any(output_dir.glob("state_tests/**/*.json")), (
        "No fixture files were created"
    )


def test_fill_to_directory_with_meta_fails(
    tmp_path_factory: TempPathFactory, run_fill: Any
) -> None:
    """
    Test filling to a directory with .meta subdirectory fails without --clean.
    """
    # Create a directory with .meta
    output_dir = tmp_path_factory.mktemp("directory_with_meta")
    meta_dir = output_dir / ".meta"
    meta_dir.mkdir()
    (meta_dir / "existing_meta_file.txt").write_text("This is metadata")

    result: pytest.RunResult = run_fill(output_dir, expect_failure=True)

    assert any("is not empty" in line for line in result.errlines), (
        "Expected error about non-empty directory"
    )


def test_fill_to_directory_with_meta_with_clean(
    tmp_path_factory: TempPathFactory, run_fill: Any
) -> None:
    """Test filling to a directory with .meta succeeds with --clean."""
    # Create a directory with .meta
    output_dir = tmp_path_factory.mktemp("directory_with_meta_clean")
    meta_dir = output_dir / ".meta"
    meta_dir.mkdir()
    (meta_dir / "existing_meta_file.txt").write_text("This is metadata")

    run_fill(output_dir, clean=True)

    assert any(output_dir.glob("state_tests/**/*.json")), (
        "No fixture files were created"
    )
    assert not (meta_dir / "existing_meta_file.txt").exists(), (
        "Existing meta file was not removed"
    )


def test_fill_stdout_always_works(
    tmp_path_factory: TempPathFactory, run_fill: Any
) -> None:
    """Test filling to stdout always works regardless of output state."""
    stdout_path = Path("stdout")
    # create a directory called "stdout" - it should not have any effect
    output_dir = tmp_path_factory.mktemp(stdout_path.name, numbered=False)
    assert str(output_dir.stem) == "stdout"
    meta_dir = output_dir / ".meta"
    meta_dir.mkdir()
    (meta_dir / "existing_meta_file.txt").write_text("This is metadata")

    result: pytest.RunResult = run_fill(
        stdout_path, disable_capture_output=True
    )

    assert any(
        "test_example.py::test_function[fork_Cancun-state_test]" in line
        for line in result.outlines
    ), f"Expected JSON output for state test: {result.outlines}"
    assert not any(stdout_path.glob("*.json")), (
        "Fixture files were created when stdout is used"
    )


def test_fill_to_tarball_directory(
    tmp_path_factory: TempPathFactory, run_fill: Any
) -> None:
    """Test filling to a tarball output."""
    output_dir = tmp_path_factory.mktemp("tarball_fixtures")
    tarball_path = output_dir / "fixtures.tar.gz"

    run_fill(tarball_path)

    assert tarball_path.exists(), "Tarball was not created"
    extracted_dir = output_dir / "fixtures"
    assert extracted_dir.exists(), "Extracted directory doesn't exist"

    assert any(extracted_dir.glob("state_tests/**/*.json")), (
        "No fixture files were created"
    )


# New tests for the is_master functionality
def test_create_directories_skips_when_not_master() -> None:
    """
    Test that create_directories skips operations when not the master process.
    """
    fixture_output = FixtureOutput(
        output_path=Path("/fake/path"),
        clean=True,
    )

    # Mock directory operations to ensure they aren't called
    with (
        patch.object(FixtureOutput, "is_directory_empty") as mock_is_empty,
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "mkdir") as mock_mkdir,
        patch("shutil.rmtree") as mock_rmtree,
    ):
        # Call with is_master=False (worker process)
        fixture_output.create_directories(is_master=False)

        # Verify no directory operations occurred
        mock_is_empty.assert_not_called()
        mock_mkdir.assert_not_called()
        mock_rmtree.assert_not_called()


def test_create_directories_operates_when_master() -> None:
    """
    Test that create_directories performs operations when is the master
    process.
    """
    fixture_output = FixtureOutput(
        output_path=Path("/fake/path"),
        clean=True,
    )

    # Mock directory operations
    with (
        patch.object(FixtureOutput, "is_directory_empty", return_value=True),
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "mkdir") as mock_mkdir,
        patch("shutil.rmtree") as mock_rmtree,
    ):
        # Call with is_master=True (master process)
        fixture_output.create_directories(is_master=True)

        # Verify directory operations occurred
        mock_rmtree.assert_called_once()
        mock_mkdir.assert_called()


def test_create_directories_checks_empty_when_master() -> None:
    """Test that directory emptiness is checked only when is_master=True."""
    fixture_output = FixtureOutput(
        output_path=Path("/fake/path"),
        clean=False,  # Don't clean, so we'll check if empty
    )

    # Mock directory operations
    with (
        patch.object(
            FixtureOutput, "is_directory_empty", return_value=False
        ) as mock_is_empty,
        patch.object(
            FixtureOutput, "get_directory_summary", return_value="not empty"
        ) as mock_summary,
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "mkdir"),
    ):
        # Call with is_master=True and expect an error about non-empty
        # directory
        with pytest.raises(ValueError, match="not empty"):
            fixture_output.create_directories(is_master=True)

        # Verify emptiness check was performed
        mock_is_empty.assert_called_once()
        mock_summary.assert_called_once()


def test_stdout_skips_directory_operations_regardless_of_master() -> None:
    """
    Test that stdout output skips directory operations regardless of is_master
    value.
    """
    fixture_output = FixtureOutput(
        output_path=Path("stdout"),
        clean=True,
    )

    # Mock directory operations to ensure they aren't called
    with (
        patch.object(FixtureOutput, "is_directory_empty") as mock_is_empty,
        patch.object(Path, "exists") as mock_exists,
        patch.object(Path, "mkdir") as mock_mkdir,
        patch("shutil.rmtree") as mock_rmtree,
    ):
        # Should skip operations even with is_master=True
        fixture_output.create_directories(is_master=True)

        # Verify no directory operations occurred
        mock_is_empty.assert_not_called()
        mock_exists.assert_not_called()
        mock_mkdir.assert_not_called()
        mock_rmtree.assert_not_called()
