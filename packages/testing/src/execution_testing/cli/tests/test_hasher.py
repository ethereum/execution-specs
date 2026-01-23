"""Tests for the hasher CLI tool and module."""

import json
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from click.testing import CliRunner

from execution_testing.base_types import HexNumber
from execution_testing.cli.hasher import HashableItem, hasher
from execution_testing.fixtures.consume import TestCaseIndexFile


def create_fixture(path: Path, test_name: str, hash_value: str) -> None:
    """Create a test fixture JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({test_name: {"_info": {"hash": hash_value}}}))


class TestCompareIdenticalDirectories:
    """Test comparing identical directories."""

    def test_compare_identical_directories(self, tmp_path: Path) -> None:
        """Same content in both dirs should exit 0 with no output."""
        dir_a = tmp_path / "dir_a" / "state_tests"
        dir_b = tmp_path / "dir_b" / "state_tests"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")
        create_fixture(dir_b / "test.json", "test1", "0xabc123")

        runner = CliRunner()
        result = runner.invoke(
            hasher, ["compare", str(dir_a.parent), str(dir_b.parent)]
        )
        assert result.exit_code == 0
        assert result.output == ""


class TestCompareDifferentDirectories:
    """Test comparing different directories."""

    def test_compare_different_directories(self, tmp_path: Path) -> None:
        """Different hashes should exit 1 with diff in stdout."""
        dir_a = tmp_path / "dir_a" / "state_tests"
        dir_b = tmp_path / "dir_b" / "state_tests"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")
        create_fixture(dir_b / "test.json", "test1", "0xdef456")

        runner = CliRunner()
        result = runner.invoke(
            hasher, ["compare", str(dir_a.parent), str(dir_b.parent)]
        )
        assert result.exit_code == 1
        assert "Fixture Hash Differences" in result.output
        # Verify the new format shows the path and both hashes
        assert "test1" in result.output
        assert "0xabc123" in result.output
        assert "0xdef456" in result.output


class TestCompareMissingDirectory:
    """Test comparing when a directory doesn't exist."""

    def test_compare_missing_directory(self, tmp_path: Path) -> None:
        """One path doesn't exist should exit 2 with error in stderr."""
        dir_a = tmp_path / "dir_a" / "state_tests"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")

        runner = CliRunner()
        result = runner.invoke(
            hasher,
            ["compare", str(dir_a.parent), str(tmp_path / "nonexistent")],
        )
        assert result.exit_code == 2


class TestCompareFlagParity:
    """Test that flags work consistently between hash and compare commands."""

    def test_compare_flag_parity_files(self, tmp_path: Path) -> None:
        """Hasher -f X vs hasher compare -f X X should exit 0."""
        dir_a = tmp_path / "dir_a" / "state_tests"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")

        runner = CliRunner()
        # Compare same directory with -f flag
        result = runner.invoke(
            hasher, ["compare", "-f", str(dir_a.parent), str(dir_a.parent)]
        )
        assert result.exit_code == 0

    def test_compare_flag_parity_tests(self, tmp_path: Path) -> None:
        """Hasher -t X vs hasher compare -t X X should exit 0."""
        dir_a = tmp_path / "dir_a" / "state_tests"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")

        runner = CliRunner()
        # Compare same directory with -t flag
        result = runner.invoke(
            hasher, ["compare", "-t", str(dir_a.parent), str(dir_a.parent)]
        )
        assert result.exit_code == 0

    def test_compare_flag_parity_root(self, tmp_path: Path) -> None:
        """Hasher -r X vs hasher compare -r X X should exit 0."""
        dir_a = tmp_path / "dir_a" / "state_tests"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")

        runner = CliRunner()
        # Compare same directory with -r flag
        result = runner.invoke(
            hasher, ["compare", "-r", str(dir_a.parent), str(dir_a.parent)]
        )
        assert result.exit_code == 0


class TestBackwardsCompatibility:
    """Test backwards compatibility with existing hasher FOLDER syntax."""

    def test_backwards_compat(self, tmp_path: Path) -> None:
        """Hasher FOLDER without subcommand should work as before."""
        dir_a = tmp_path / "dir_a" / "state_tests"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")

        runner = CliRunner()
        # Old syntax without subcommand
        result = runner.invoke(hasher, [str(dir_a.parent)])
        assert result.exit_code == 0
        assert "0x" in result.output

    def test_explicit_hash_subcommand(self, tmp_path: Path) -> None:
        """Hasher hash FOLDER should work."""
        dir_a = tmp_path / "dir_a" / "state_tests"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")

        runner = CliRunner()
        # Explicit hash subcommand
        result = runner.invoke(hasher, ["hash", str(dir_a.parent)])
        assert result.exit_code == 0
        assert "0x" in result.output

    def test_hash_output_matches_between_syntaxes(
        self, tmp_path: Path
    ) -> None:
        """Both syntaxes should produce identical output."""
        dir_a = tmp_path / "dir_a" / "state_tests"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")

        runner = CliRunner()
        # Old syntax
        result_old = runner.invoke(hasher, [str(dir_a.parent)])
        # New syntax
        result_new = runner.invoke(hasher, ["hash", str(dir_a.parent)])

        assert result_old.exit_code == result_new.exit_code
        assert result_old.output == result_new.output


class TestCompareEmptyDirectories:
    """Test comparing empty directories."""

    def test_compare_empty_directories(self, tmp_path: Path) -> None:
        """Both dirs empty should exit 0."""
        dir_a = tmp_path / "dir_a"
        dir_b = tmp_path / "dir_b"
        dir_a.mkdir(parents=True)
        dir_b.mkdir(parents=True)

        runner = CliRunner()
        result = runner.invoke(hasher, ["compare", str(dir_a), str(dir_b)])
        assert result.exit_code == 0


class TestErrorToStderr:
    """Test that errors go to stderr."""

    def test_error_to_stderr(self, tmp_path: Path) -> None:
        """Invalid fixture JSON should produce error message."""
        dir_a = tmp_path / "dir_a"
        dir_a.mkdir(parents=True)
        (dir_a / "invalid.json").write_text("not valid json")

        runner = CliRunner()
        result = runner.invoke(hasher, ["compare", str(dir_a), str(dir_a)])
        assert result.exit_code == 2
        assert "Error" in result.output


class TestHashCommandFlags:
    """Test hash command with various flags."""

    def test_hash_with_files_flag(self, tmp_path: Path) -> None:
        """Hasher hash -f FOLDER should work."""
        dir_a = tmp_path / "dir_a" / "state_tests"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")

        runner = CliRunner()
        result = runner.invoke(hasher, ["hash", "-f", str(dir_a.parent)])
        assert result.exit_code == 0
        assert "test.json" in result.output

    def test_hash_with_tests_flag(self, tmp_path: Path) -> None:
        """Hasher hash -t FOLDER should work."""
        dir_a = tmp_path / "dir_a" / "state_tests"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")

        runner = CliRunner()
        result = runner.invoke(hasher, ["hash", "-t", str(dir_a.parent)])
        assert result.exit_code == 0
        assert "test1" in result.output

    def test_hash_with_root_flag(self, tmp_path: Path) -> None:
        """Hasher hash -r FOLDER should only print root hash."""
        dir_a = tmp_path / "dir_a" / "state_tests"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")

        runner = CliRunner()
        result = runner.invoke(hasher, ["hash", "-r", str(dir_a.parent)])
        assert result.exit_code == 0
        # Should only have one line with the hash
        lines = [line for line in result.output.strip().split("\n") if line]
        assert len(lines) == 1
        assert lines[0].startswith("0x")


class TestCompareDepthFlag:
    """Test --depth flag for compare command."""

    def test_depth_limits_output(self, tmp_path: Path) -> None:
        """--depth should limit how deep the comparison goes."""
        dir_a = tmp_path / "dir_a" / "folder" / "subfolder"
        dir_b = tmp_path / "dir_b" / "folder" / "subfolder"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")
        create_fixture(dir_b / "test.json", "test1", "0xdef456")

        runner = CliRunner()

        # depth=1 should show folder but not subfolder
        result = runner.invoke(
            hasher,
            [
                "compare",
                "--depth",
                "1",
                str(dir_a.parent.parent),
                str(dir_b.parent.parent),
            ],
        )
        assert result.exit_code == 1
        assert "folder" in result.output
        assert "subfolder" not in result.output

    def test_depth_2_shows_subfolders(self, tmp_path: Path) -> None:
        """--depth 2 should show subfolders."""
        dir_a = tmp_path / "dir_a" / "folder" / "subfolder"
        dir_b = tmp_path / "dir_b" / "folder" / "subfolder"
        create_fixture(dir_a / "test.json", "test1", "0xabc123")
        create_fixture(dir_b / "test.json", "test1", "0xdef456")

        runner = CliRunner()

        result = runner.invoke(
            hasher,
            [
                "compare",
                "-d",
                "2",
                str(dir_a.parent.parent),
                str(dir_b.parent.parent),
            ],
        )
        assert result.exit_code == 1
        assert "folder" in result.output
        assert "subfolder" in result.output


class TestCompareHierarchy:
    """Test that diff output preserves hierarchy."""

    def test_full_paths_in_output(self, tmp_path: Path) -> None:
        """Diff should show full paths to disambiguate items with same name."""
        # Create two folders each with a "shanghai" subfolder
        dir_a = tmp_path / "dir_a"
        dir_b = tmp_path / "dir_b"
        create_fixture(
            dir_a / "blockchain_tests" / "shanghai" / "test.json",
            "test1",
            "0xaaa111",
        )
        create_fixture(
            dir_a / "state_tests" / "shanghai" / "test.json",
            "test1",
            "0xbbb222",
        )
        create_fixture(
            dir_b / "blockchain_tests" / "shanghai" / "test.json",
            "test1",
            "0xccc333",
        )
        create_fixture(
            dir_b / "state_tests" / "shanghai" / "test.json",
            "test1",
            "0xddd444",
        )

        runner = CliRunner()
        result = runner.invoke(
            hasher, ["compare", "--depth", "2", str(dir_a), str(dir_b)]
        )

        assert result.exit_code == 1
        # Should show full paths, not just "shanghai" twice
        assert "blockchain_tests/shanghai" in result.output
        assert "state_tests/shanghai" in result.output


class TestHelpOptions:
    """Test help options."""

    def test_help_short(self) -> None:
        """-h should show help."""
        runner = CliRunner()
        result = runner.invoke(hasher, ["-h"])
        assert result.exit_code == 0
        assert "Hash folders of JSON fixtures" in result.output

    def test_help_long(self) -> None:
        """--help should show help."""
        runner = CliRunner()
        result = runner.invoke(hasher, ["--help"])
        assert result.exit_code == 0
        assert "Hash folders of JSON fixtures" in result.output

    def test_compare_help(self) -> None:
        """Compare --help should show compare help."""
        runner = CliRunner()
        result = runner.invoke(hasher, ["compare", "--help"])
        assert result.exit_code == 0
        assert "Compare two fixture directories" in result.output

    def test_hash_help(self) -> None:
        """Hash --help should show hash help."""
        runner = CliRunner()
        result = runner.invoke(hasher, ["hash", "--help"])
        assert result.exit_code == 0
        assert "Hash folders of JSON fixtures" in result.output


class TestHashableItemFromIndexEntries:
    """Test that from_index_entries produces same hash as from_folder."""

    @pytest.fixture
    def fixture_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory with test fixtures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)

            # Create structure: state_tests/cancun/test.json
            state_tests = base / "state_tests" / "cancun"
            state_tests.mkdir(parents=True)

            # Create a fixture file with two tests
            fixture_file = state_tests / "test.json"
            fixture_data = {
                "test_one": {
                    "_info": {
                        "hash": "0x1111111111111111111111111111111111111111111111111111111111111111"  # noqa: E501
                    },
                    "pre": {},
                    "post": {},
                },
                "test_two": {
                    "_info": {
                        "hash": "0x2222222222222222222222222222222222222222222222222222222222222222"  # noqa: E501
                    },
                    "pre": {},
                    "post": {},
                },
            }
            fixture_file.write_text(json.dumps(fixture_data))

            # Create another fixture file in a different folder
            blockchain_tests = base / "blockchain_tests" / "cancun"
            blockchain_tests.mkdir(parents=True)

            fixture_file2 = blockchain_tests / "test.json"
            fixture_data2 = {
                "test_three": {
                    "_info": {
                        "hash": "0x3333333333333333333333333333333333333333333333333333333333333333"  # noqa: E501
                    },
                    "pre": {},
                    "post": {},
                },
            }
            fixture_file2.write_text(json.dumps(fixture_data2))

            yield base

    @pytest.fixture
    def index_entries(self) -> list[TestCaseIndexFile]:
        """Create index entries matching the fixture_dir structure."""
        return [
            TestCaseIndexFile(
                id="test_one",
                json_path=Path("state_tests/cancun/test.json"),
                fixture_hash=HexNumber(
                    0x1111111111111111111111111111111111111111111111111111111111111111
                ),
                fork=None,
                format=None,
            ),
            TestCaseIndexFile(
                id="test_two",
                json_path=Path("state_tests/cancun/test.json"),
                fixture_hash=HexNumber(
                    0x2222222222222222222222222222222222222222222222222222222222222222
                ),
                fork=None,
                format=None,
            ),
            TestCaseIndexFile(
                id="test_three",
                json_path=Path("blockchain_tests/cancun/test.json"),
                fixture_hash=HexNumber(
                    0x3333333333333333333333333333333333333333333333333333333333333333
                ),
                fork=None,
                format=None,
            ),
        ]

    def test_hash_matches_from_folder(
        self, fixture_dir: Path, index_entries: list[TestCaseIndexFile]
    ) -> None:
        """Verify from_index_entries produces same hash as from_folder."""
        # Get hash using from_folder (reads files)
        hash_from_folder = HashableItem.from_folder(
            folder_path=fixture_dir
        ).hash()

        # Get hash using from_index_entries (no file I/O)
        hash_from_entries = HashableItem.from_index_entries(
            index_entries
        ).hash()

        assert hash_from_folder == hash_from_entries

    def test_hash_changes_with_different_entries(
        self, index_entries: list[TestCaseIndexFile]
    ) -> None:
        """Verify hash changes when entries change."""
        hash1 = HashableItem.from_index_entries(index_entries).hash()

        # Modify one entry's hash
        modified_entries = index_entries.copy()
        modified_entries[0] = TestCaseIndexFile(
            id="test_one",
            json_path=Path("state_tests/cancun/test.json"),
            fixture_hash=HexNumber(
                0x9999999999999999999999999999999999999999999999999999999999999999
            ),
            fork=None,
            format=None,
        )

        hash2 = HashableItem.from_index_entries(modified_entries).hash()

        assert hash1 != hash2

    def test_empty_entries(self) -> None:
        """Verify empty entries produces a valid hash."""
        hash_result = HashableItem.from_index_entries([]).hash()
        # Empty tree should still produce a hash (sha256 of empty string)
        assert hash_result is not None
        assert len(hash_result) == 32  # SHA256 produces 32 bytes

    def test_multiple_files_in_same_folder(self) -> None:
        """Verify multiple files in same folder are handled correctly."""
        entries = [
            TestCaseIndexFile(
                id="test_a",
                json_path=Path("state_tests/cancun/file1.json"),
                fixture_hash=HexNumber(
                    0x1111111111111111111111111111111111111111111111111111111111111111
                ),
                fork=None,
                format=None,
            ),
            TestCaseIndexFile(
                id="test_b",
                json_path=Path("state_tests/cancun/file2.json"),
                fixture_hash=HexNumber(
                    0x2222222222222222222222222222222222222222222222222222222222222222
                ),
                fork=None,
                format=None,
            ),
        ]
        item = HashableItem.from_index_entries(entries)
        hash_result = item.hash()
        assert hash_result is not None
        assert len(hash_result) == 32

    def test_deeply_nested_paths(self) -> None:
        """Verify deeply nested paths are handled correctly."""
        entries = [
            TestCaseIndexFile(
                id="test_deep",
                json_path=Path("a/b/c/d/test.json"),
                fixture_hash=HexNumber(
                    0x1111111111111111111111111111111111111111111111111111111111111111
                ),
                fork=None,
                format=None,
            ),
        ]
        item = HashableItem.from_index_entries(entries)
        hash_result = item.hash()
        assert hash_result is not None
        assert len(hash_result) == 32

    def test_single_file_single_test(self) -> None:
        """Verify single file with single test works."""
        entries = [
            TestCaseIndexFile(
                id="only_test",
                json_path=Path("tests/test.json"),
                fixture_hash=HexNumber(
                    0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
                ),
                fork=None,
                format=None,
            ),
        ]
        item = HashableItem.from_index_entries(entries)
        hash_result = item.hash()
        assert hash_result is not None
        assert len(hash_result) == 32

    def test_entries_with_none_fixture_hash_skipped(self) -> None:
        """Verify entries with None fixture_hash are skipped."""
        entries = [
            TestCaseIndexFile(
                id="test_with_hash",
                json_path=Path("tests/test.json"),
                fixture_hash=HexNumber(
                    0x1111111111111111111111111111111111111111111111111111111111111111
                ),
                fork=None,
                format=None,
            ),
            TestCaseIndexFile(
                id="test_without_hash",
                json_path=Path("tests/test.json"),
                fixture_hash=None,
                fork=None,
                format=None,
            ),
        ]
        item = HashableItem.from_index_entries(entries)
        # Should still work, just skip the None entry
        hash_result = item.hash()
        assert hash_result is not None
        assert len(hash_result) == 32
