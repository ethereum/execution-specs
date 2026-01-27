"""Tests for the hasher CLI tool, module, and merge_partial_indexes."""

import json
import tempfile
from pathlib import Path
from typing import Generator, List

import pytest
from click.testing import CliRunner

from execution_testing.base_types import HexNumber
from execution_testing.cli.gen_index import merge_partial_indexes
from execution_testing.cli.hasher import HashableItem, hasher
from execution_testing.fixtures.consume import IndexFile, TestCaseIndexFile

HASH_1 = 0x1111111111111111111111111111111111111111111111111111111111111111
HASH_2 = 0x2222222222222222222222222222222222222222222222222222222222222222
HASH_3 = 0x3333333333333333333333333333333333333333333333333333333333333333
HASH_4 = 0x4444444444444444444444444444444444444444444444444444444444444444
HASH_9 = 0x9999999999999999999999999999999999999999999999999999999999999999


def _hex_str(h: int) -> str:
    """Convert an integer hash to its 0x-prefixed hex string."""
    return f"0x{h:064x}"


def _make_entry(
    test_id: str,
    json_path: str,
    fixture_hash: int,
    fork: str | None = None,
    fmt: str | None = None,
) -> TestCaseIndexFile:
    """Create a TestCaseIndexFile for testing."""
    return TestCaseIndexFile(
        id=test_id,
        json_path=Path(json_path),
        fixture_hash=HexNumber(fixture_hash),
        fork=fork,
        format=fmt,
    )


def _make_json_fixture(test_names_and_hashes: dict[str, int]) -> str:
    """Create a JSON fixture file matching from_folder expectations."""
    data = {}
    for name, h in test_names_and_hashes.items():
        data[name] = {
            "_info": {"hash": _hex_str(h)},
            "pre": {},
            "post": {},
        }
    return json.dumps(data)


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

            # state_tests/cancun/test.json (two tests)
            state_tests = base / "state_tests" / "cancun"
            state_tests.mkdir(parents=True)
            (state_tests / "test.json").write_text(
                _make_json_fixture({"test_one": HASH_1, "test_two": HASH_2})
            )

            # blockchain_tests/cancun/test.json (one test)
            blockchain_tests = base / "blockchain_tests" / "cancun"
            blockchain_tests.mkdir(parents=True)
            (blockchain_tests / "test.json").write_text(
                _make_json_fixture({"test_three": HASH_3})
            )

            yield base

    @pytest.fixture
    def index_entries(self) -> List[TestCaseIndexFile]:
        """Create index entries matching the fixture_dir structure."""
        return [
            _make_entry("test_one", "state_tests/cancun/test.json", HASH_1),
            _make_entry("test_two", "state_tests/cancun/test.json", HASH_2),
            _make_entry(
                "test_three", "blockchain_tests/cancun/test.json", HASH_3
            ),
        ]

    def test_hash_matches_from_folder(
        self,
        fixture_dir: Path,
        index_entries: List[TestCaseIndexFile],
    ) -> None:
        """Verify from_index_entries produces same hash as from_folder."""
        hash_from_folder = HashableItem.from_folder(
            folder_path=fixture_dir
        ).hash()
        hash_from_entries = HashableItem.from_index_entries(
            index_entries
        ).hash()
        assert hash_from_folder == hash_from_entries

    def test_hash_changes_with_different_entries(
        self, index_entries: List[TestCaseIndexFile]
    ) -> None:
        """Verify hash changes when entries change."""
        hash1 = HashableItem.from_index_entries(index_entries).hash()

        modified = index_entries.copy()
        modified[0] = _make_entry(
            "test_one", "state_tests/cancun/test.json", HASH_9
        )
        hash2 = HashableItem.from_index_entries(modified).hash()

        assert hash1 != hash2

    def test_empty_entries(self) -> None:
        """Verify empty entries produces a valid hash."""
        result = HashableItem.from_index_entries([]).hash()
        assert result is not None
        assert len(result) == 32

    def test_multiple_files_in_same_folder(self) -> None:
        """Verify hash with multiple JSON files in the same folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            folder = base / "tests" / "cancun"
            folder.mkdir(parents=True)

            (folder / "test_a.json").write_text(
                _make_json_fixture({"a1": HASH_1})
            )
            (folder / "test_b.json").write_text(
                _make_json_fixture({"b1": HASH_2})
            )

            entries = [
                _make_entry("a1", "tests/cancun/test_a.json", HASH_1),
                _make_entry("b1", "tests/cancun/test_b.json", HASH_2),
            ]

            hash_from_folder = HashableItem.from_folder(
                folder_path=base
            ).hash()
            hash_from_entries = HashableItem.from_index_entries(entries).hash()
            assert hash_from_folder == hash_from_entries

    def test_deeply_nested_paths(self) -> None:
        """Verify hash with deeply nested folder structures (3+ levels)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            deep = base / "a" / "b" / "c" / "d"
            deep.mkdir(parents=True)

            (deep / "test.json").write_text(
                _make_json_fixture({"t1": HASH_1, "t2": HASH_2})
            )

            entries = [
                _make_entry("t1", "a/b/c/d/test.json", HASH_1),
                _make_entry("t2", "a/b/c/d/test.json", HASH_2),
            ]

            hash_from_folder = HashableItem.from_folder(
                folder_path=base
            ).hash()
            hash_from_entries = HashableItem.from_index_entries(entries).hash()
            assert hash_from_folder == hash_from_entries

    def test_single_file_single_test(self) -> None:
        """Verify degenerate case: one folder, one file, one test."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            folder = base / "tests"
            folder.mkdir()

            (folder / "only.json").write_text(
                _make_json_fixture({"solo": HASH_4})
            )

            entries = [_make_entry("solo", "tests/only.json", HASH_4)]

            hash_from_folder = HashableItem.from_folder(
                folder_path=base
            ).hash()
            hash_from_entries = HashableItem.from_index_entries(entries).hash()
            assert hash_from_folder == hash_from_entries

    def test_entries_with_none_fixture_hash_skipped(self) -> None:
        """Verify entries with fixture_hash=None are skipped."""
        entries_with_none = [
            _make_entry("t1", "tests/a.json", HASH_1),
            TestCaseIndexFile(
                id="t_null",
                json_path=Path("tests/a.json"),
                fixture_hash=None,
                fork=None,
                format=None,
            ),
        ]
        entries_without_none = [
            _make_entry("t1", "tests/a.json", HASH_1),
        ]

        hash_with = HashableItem.from_index_entries(entries_with_none).hash()
        hash_without = HashableItem.from_index_entries(
            entries_without_none
        ).hash()
        assert hash_with == hash_without


class TestMergePartialIndexes:
    """Test the JSONL partial index merge pipeline end-to-end."""

    def _write_jsonl(self, path: Path, entries: list[dict]) -> None:
        """Write a list of dicts as JSONL lines."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

    def _make_entry_dict(
        self,
        test_id: str,
        json_path: str,
        fixture_hash: int,
        fork: str | None = None,
        fmt: str | None = None,
    ) -> dict:
        """Create a dict matching what collector.py writes to JSONL."""
        return {
            "id": test_id,
            "json_path": json_path,
            "fixture_hash": _hex_str(fixture_hash),
            "fork": fork,
            "format": fmt,
            "pre_hash": None,
        }

    def test_merge_produces_valid_index(self) -> None:
        """Verify merging JSONL partials produces a valid index.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            meta_dir = output_dir / ".meta"
            meta_dir.mkdir(parents=True)

            entries = [
                self._make_entry_dict(
                    "test_a",
                    "state_tests/cancun/test.json",
                    HASH_1,
                    fork="Cancun",
                    fmt="state_test",
                ),
                self._make_entry_dict(
                    "test_b",
                    "blockchain_tests/cancun/test.json",
                    HASH_2,
                    fork="Cancun",
                    fmt="blockchain_test",
                ),
            ]

            self._write_jsonl(
                meta_dir / "partial_index.gw0.jsonl", entries[:1]
            )
            self._write_jsonl(
                meta_dir / "partial_index.gw1.jsonl", entries[1:]
            )

            merge_partial_indexes(output_dir, quiet_mode=True)

            index_path = meta_dir / "index.json"
            assert index_path.exists()

            index = IndexFile.model_validate_json(index_path.read_text())
            assert index.test_count == 2
            assert index.root_hash is not None
            assert index.root_hash != 0

    def test_merge_fixture_formats_uses_format_name(self) -> None:
        """
        Verify fixture_formats contains format_name values (e.g.
        'state_test') not class names (e.g. 'StateFixture').

        This is the exact bug that format.__name__ would have caused.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            meta_dir = output_dir / ".meta"

            entries = [
                self._make_entry_dict(
                    "t1",
                    "state_tests/test.json",
                    HASH_1,
                    fork="Cancun",
                    fmt="state_test",
                ),
                self._make_entry_dict(
                    "t2",
                    "blockchain_tests/test.json",
                    HASH_2,
                    fork="Cancun",
                    fmt="blockchain_test",
                ),
            ]
            self._write_jsonl(meta_dir / "partial_index.gw0.jsonl", entries)

            merge_partial_indexes(output_dir, quiet_mode=True)

            index = IndexFile.model_validate_json(
                (meta_dir / "index.json").read_text()
            )
            assert index.fixture_formats is not None
            assert sorted(index.fixture_formats) == [
                "blockchain_test",
                "state_test",
            ]

    def test_merge_forks_collected_correctly(self) -> None:
        """Verify forks are collected from validated entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            meta_dir = output_dir / ".meta"

            entries = [
                self._make_entry_dict(
                    "t1",
                    "state_tests/test.json",
                    HASH_1,
                    fork="Cancun",
                    fmt="state_test",
                ),
                self._make_entry_dict(
                    "t2",
                    "state_tests/test2.json",
                    HASH_2,
                    fork="Shanghai",
                    fmt="state_test",
                ),
            ]
            self._write_jsonl(meta_dir / "partial_index.gw0.jsonl", entries)

            merge_partial_indexes(output_dir, quiet_mode=True)

            index = IndexFile.model_validate_json(
                (meta_dir / "index.json").read_text()
            )
            assert index.forks is not None
            assert sorted(str(f) for f in index.forks) == [
                "Cancun",
                "Shanghai",
            ]

    def test_merge_cleans_up_partial_files(self) -> None:
        """Verify partial JSONL files are deleted after merge."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            meta_dir = output_dir / ".meta"

            entries = [
                self._make_entry_dict(
                    "t1",
                    "state_tests/test.json",
                    HASH_1,
                    fmt="state_test",
                ),
            ]
            self._write_jsonl(meta_dir / "partial_index.gw0.jsonl", entries)
            self._write_jsonl(meta_dir / "partial_index.gw1.jsonl", entries)

            merge_partial_indexes(output_dir, quiet_mode=True)

            remaining = list(meta_dir.glob("partial_index*.jsonl"))
            assert remaining == []

    def test_merge_multiple_workers_same_hash_as_single(self) -> None:
        """Verify hash is the same regardless of how entries are split."""
        entry_dicts = [
            self._make_entry_dict(
                "t1", "state_tests/a.json", HASH_1, fmt="state_test"
            ),
            self._make_entry_dict(
                "t2", "state_tests/a.json", HASH_2, fmt="state_test"
            ),
            self._make_entry_dict(
                "t3", "blockchain_tests/b.json", HASH_3, fmt="blockchain_test"
            ),
        ]

        # Single worker: all entries in one file
        with tempfile.TemporaryDirectory() as tmpdir1:
            output1 = Path(tmpdir1)
            meta1 = output1 / ".meta"
            self._write_jsonl(meta1 / "partial_index.gw0.jsonl", entry_dicts)
            merge_partial_indexes(output1, quiet_mode=True)
            index1 = IndexFile.model_validate_json(
                (meta1 / "index.json").read_text()
            )

        # Multiple workers: entries split across files
        with tempfile.TemporaryDirectory() as tmpdir2:
            output2 = Path(tmpdir2)
            meta2 = output2 / ".meta"
            self._write_jsonl(
                meta2 / "partial_index.gw0.jsonl", entry_dicts[:1]
            )
            self._write_jsonl(
                meta2 / "partial_index.gw1.jsonl", entry_dicts[1:2]
            )
            self._write_jsonl(
                meta2 / "partial_index.gw2.jsonl", entry_dicts[2:]
            )
            merge_partial_indexes(output2, quiet_mode=True)
            index2 = IndexFile.model_validate_json(
                (meta2 / "index.json").read_text()
            )

        assert index1.root_hash == index2.root_hash
        assert index1.test_count == index2.test_count

    def test_merge_raises_when_no_partial_files(self) -> None:
        """Verify merge_partial_indexes raises when no partials exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            meta_dir = output_dir / ".meta"
            meta_dir.mkdir(parents=True)

            with pytest.raises(Exception, match="No partial indexes found"):
                merge_partial_indexes(output_dir, quiet_mode=True)
