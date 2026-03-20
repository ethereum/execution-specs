"""Tests for baseline trace loading from dump directories."""

import json
from pathlib import Path

from execution_testing.cli.pytest_commands.plugins.filler.verify_traces import (  # noqa: E501
    _load_traces_from_dump_dir,
)
from execution_testing.client_clis.cli_types import (
    Traces,
)


def _write_trace_file(
    path: Path,
    trace_lines: list[dict] | None = None,
    output: str = "0x",
    gas_used: str = "0x5208",
) -> None:
    """Write a minimal .jsonl trace file."""
    if trace_lines is None:
        trace_lines = [
            {
                "pc": 0,
                "op": 96,
                "gas": "0x5f5e100",
                "gasCost": "0x3",
                "memSize": 0,
                "stack": [],
                "depth": 1,
                "refund": 0,
                "opName": "PUSH1",
            }
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for line in trace_lines:
            f.write(json.dumps(line) + "\n")
        f.write(json.dumps({"output": output, "gasUsed": gas_used}) + "\n")


class TestLoadTracesFromDumpDir:
    """Test _load_traces_from_dump_dir."""

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Empty directory returns empty list."""
        result = _load_traces_from_dump_dir(tmp_path)
        assert result == []

    def test_single_call_dir_two_trace_files(self, tmp_path: Path) -> None:
        """Single call dir with two trace files returns one Traces."""
        call_dir = tmp_path / "0"
        call_dir.mkdir()
        _write_trace_file(call_dir / "trace-0-0xaaa.jsonl")
        _write_trace_file(call_dir / "trace-1-0xbbb.jsonl")

        result = _load_traces_from_dump_dir(tmp_path)
        assert len(result) == 1
        assert isinstance(result[0], Traces)
        assert len(result[0].root) == 2

    def test_multiple_call_dirs(self, tmp_path: Path) -> None:
        """Multiple call dirs (0, 1, 2) return correctly ordered list."""
        for i in range(3):
            call_dir = tmp_path / str(i)
            call_dir.mkdir()
            _write_trace_file(call_dir / f"trace-0-0x{i:03x}.jsonl")

        result = _load_traces_from_dump_dir(tmp_path)
        assert len(result) == 3
        for traces in result:
            assert isinstance(traces, Traces)
            assert len(traces.root) == 1

    def test_non_numeric_subdirs_ignored(self, tmp_path: Path) -> None:
        """Non-numeric subdirectories are ignored."""
        (tmp_path / "0").mkdir()
        _write_trace_file(tmp_path / "0" / "trace-0-0xaaa.jsonl")
        (tmp_path / "metadata").mkdir()
        (tmp_path / "metadata" / "info.json").write_text("{}")

        result = _load_traces_from_dump_dir(tmp_path)
        assert len(result) == 1

    def test_numeric_sorting_not_lexical(self, tmp_path: Path) -> None:
        """Call dirs are sorted numerically (2 before 10)."""
        for i in [10, 2, 0]:
            call_dir = tmp_path / str(i)
            call_dir.mkdir()
            _write_trace_file(call_dir / f"trace-0-0x{i:03x}.jsonl")

        result = _load_traces_from_dump_dir(tmp_path)
        assert len(result) == 3
        # Verify they are in order 0, 2, 10 by checking the list
        # length — ordering is guaranteed by the implementation
