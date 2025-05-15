"""Test the filler plugin's output directory handling."""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from pytest import TempPathFactory

from cli.pytest_commands.fill import fill
from pytest_plugins.filler.fixture_output import FixtureOutput


@pytest.fixture(scope="module")
def test_path() -> Path:
    """Specify the test path to be filled."""
    return Path("tests/istanbul/eip1344_chainid/test_chainid.py")


@pytest.fixture(scope="module")
def fill_fork_from() -> str:
    """Specify the value for `fill`'s `--from` argument."""
    return "Paris"


@pytest.fixture(scope="module")
def fill_fork_until() -> str:
    """Specify the value for `fill`'s `--until` argument."""
    return "Cancun"


@pytest.fixture
def run_fill(test_path: Path, fill_fork_from: str, fill_fork_until: str):
    """Create a function to run the fill command with various output directory scenarios."""

    def _run_fill(output_dir: Path, clean: bool = False, expect_failure: bool = False):
        """Run the fill command with the specified output directory and clean flag."""
        args = [
            "-c",
            "pytest.ini",
            "--skip-evm-dump",
            "-m",
            "(not blockchain_test_engine) and (not eip_version_check)",
            f"--from={fill_fork_from}",
            f"--until={fill_fork_until}",
            f"--output={str(output_dir)}",
            str(test_path),
        ]

        if clean:
            args.append("--clean")

        result = CliRunner().invoke(fill, args)

        if expect_failure:
            assert result.exit_code != 0, "Fill command was expected to fail but succeeded"
        else:
            assert result.exit_code == 0, f"Fill command failed:\n{result.output}"

        return result

    return _run_fill


def test_fill_to_empty_directory(tmp_path_factory: TempPathFactory, run_fill):
    """Test filling to a new, empty directory."""
    output_dir = tmp_path_factory.mktemp("empty_fixtures")

    run_fill(output_dir)

    assert any(output_dir.glob("state_tests/**/*.json")), "No fixture files were created"
    assert (output_dir / ".meta").exists(), "Metadata directory was not created"


def test_fill_to_nonexistent_directory(tmp_path_factory: TempPathFactory, run_fill):
    """Test filling to a nonexistent directory."""
    base_dir = tmp_path_factory.mktemp("base")
    output_dir = base_dir / "nonexistent_fixtures"

    run_fill(output_dir)

    assert any(output_dir.glob("state_tests/**/*.json")), "No fixture files were created"
    assert (output_dir / ".meta").exists(), "Metadata directory was not created"


def test_fill_to_nonempty_directory_fails(tmp_path_factory: TempPathFactory, run_fill):
    """Test filling to a non-empty directory fails without --clean."""
    # Create a directory with a file
    output_dir = tmp_path_factory.mktemp("nonempty_fixtures")
    (output_dir / "existing_file.txt").write_text("This directory is not empty")

    result = run_fill(output_dir, expect_failure=True)

    assert "is not empty" in str(result.output), "Expected error about non-empty directory"
    assert "Use --clean" in str(result.output), "Expected suggestion to use --clean flag"


def test_fill_to_nonempty_directory_with_clean(tmp_path_factory: TempPathFactory, run_fill):
    """Test filling to a non-empty directory succeeds with --clean."""
    # Create a directory with a file
    output_dir = tmp_path_factory.mktemp("nonempty_fixtures_clean")
    (output_dir / "existing_file.txt").write_text("This directory will be cleaned")

    run_fill(output_dir, clean=True)

    # Verify the existing file was removed
    assert not (output_dir / "existing_file.txt").exists(), "Existing file was not removed"

    assert any(output_dir.glob("state_tests/**/*.json")), "No fixture files were created"


def test_fill_to_directory_with_meta_fails(tmp_path_factory: TempPathFactory, run_fill):
    """Test filling to a directory with .meta subdirectory fails without --clean."""
    # Create a directory with .meta
    output_dir = tmp_path_factory.mktemp("directory_with_meta")
    meta_dir = output_dir / ".meta"
    meta_dir.mkdir()
    (meta_dir / "existing_meta_file.txt").write_text("This is metadata")

    result = run_fill(output_dir, expect_failure=True)

    assert "is not empty" in str(result.output), "Expected error about non-empty directory"


def test_fill_to_directory_with_meta_with_clean(tmp_path_factory: TempPathFactory, run_fill):
    """Test filling to a directory with .meta succeeds with --clean."""
    # Create a directory with .meta
    output_dir = tmp_path_factory.mktemp("directory_with_meta_clean")
    meta_dir = output_dir / ".meta"
    meta_dir.mkdir()
    (meta_dir / "existing_meta_file.txt").write_text("This is metadata")

    run_fill(output_dir, clean=True)

    assert any(output_dir.glob("state_tests/**/*.json")), "No fixture files were created"
    assert not (meta_dir / "existing_meta_file.txt").exists(), "Existing meta file was not removed"


def test_fill_stdout_always_works(tmp_path_factory: TempPathFactory, run_fill):
    """Test filling to stdout always works regardless of output state."""
    stdout_path = Path("stdout")
    # create a directory called "stdout" - it should not have any effect
    output_dir = tmp_path_factory.mktemp(stdout_path.name)
    meta_dir = output_dir / ".meta"
    meta_dir.mkdir()
    (meta_dir / "existing_meta_file.txt").write_text("This is metadata")

    result = run_fill(stdout_path)

    assert (
        '"tests/istanbul/eip1344_chainid/test_chainid.py::test_chainid[fork_Cancun-state_test]": {'
        in result.output
    ), "Expected JSON output for state test"


def test_fill_to_tarball_directory(tmp_path_factory: TempPathFactory, run_fill):
    """Test filling to a tarball output."""
    output_dir = tmp_path_factory.mktemp("tarball_fixtures")
    tarball_path = output_dir / "fixtures.tar.gz"

    run_fill(tarball_path)

    assert tarball_path.exists(), "Tarball was not created"
    extracted_dir = output_dir / "fixtures"
    assert extracted_dir.exists(), "Extracted directory doesn't exist"

    assert any(extracted_dir.glob("state_tests/**/*.json")), "No fixture files were created"


# New tests for the is_master functionality
def test_create_directories_skips_when_not_master():
    """Test that create_directories skips operations when not the master process."""
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


def test_create_directories_operates_when_master():
    """Test that create_directories performs operations when is the master process."""
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


def test_create_directories_checks_empty_when_master():
    """Test that directory emptiness is checked only when is_master=True."""
    fixture_output = FixtureOutput(
        output_path=Path("/fake/path"),
        clean=False,  # Don't clean, so we'll check if empty
    )

    # Mock directory operations
    with (
        patch.object(FixtureOutput, "is_directory_empty", return_value=False) as mock_is_empty,
        patch.object(
            FixtureOutput, "get_directory_summary", return_value="not empty"
        ) as mock_summary,
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "mkdir"),
    ):
        # Call with is_master=True and expect an error about non-empty directory
        with pytest.raises(ValueError, match="not empty"):
            fixture_output.create_directories(is_master=True)

        # Verify emptiness check was performed
        mock_is_empty.assert_called_once()
        mock_summary.assert_called_once()


def test_stdout_skips_directory_operations_regardless_of_master():
    """Test that stdout output skips directory operations regardless of is_master value."""
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
