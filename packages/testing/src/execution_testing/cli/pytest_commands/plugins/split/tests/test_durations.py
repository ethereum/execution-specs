"""Unit tests for the durations helpers."""

from __future__ import annotations

import json
from pathlib import Path

from execution_testing.cli.pytest_commands.plugins.split.durations import (
    load_durations,
    merge_durations,
    normalize_durations,
    strip_xdist_suffix,
    write_durations,
)


class TestStripXdistSuffix:
    """Tests for :func:`strip_xdist_suffix`."""

    def test_strips_t8n_cache_suffix(self) -> None:
        """``@t8n-cache-*`` suffixes are stripped."""
        nid = "tests/t.py::test_fn[fork_A-state_test]@t8n-cache-abc123"
        expected = "tests/t.py::test_fn[fork_A-state_test]"
        assert strip_xdist_suffix(nid) == expected

    def test_preserves_other_group_suffixes(self) -> None:
        """Non-cache group suffixes (e.g. ``@bigmem``) are preserved."""
        nid = "tests/t.py::test_fn[p]@bigmem"
        assert strip_xdist_suffix(nid) == nid

    def test_preserves_custom_group_suffixes(self) -> None:
        """Custom ``xdist_group`` markers are preserved."""
        nid = "tests/t.py::test_fn[p]@custom_group"
        assert strip_xdist_suffix(nid) == nid

    def test_without_suffix_is_idempotent(self) -> None:
        """A nodeid without ``@`` is returned unchanged."""
        nid = "tests/t.py::test_fn[fork_A-state_test]"
        assert strip_xdist_suffix(nid) == nid

    def test_at_in_params_preserved(self) -> None:
        """``@`` inside parametrize values is preserved (rsplit)."""
        nid = "tests/t.py::test_fn[email@example.com]@t8n-cache-abc"
        expected = "tests/t.py::test_fn[email@example.com]"
        assert strip_xdist_suffix(nid) == expected


class TestNormalizeDurations:
    """Tests for :func:`normalize_durations`."""

    def test_strips_cache_suffixes_only(self) -> None:
        """Only ``@t8n-cache-*`` keys are stripped; others kept."""
        raw = {
            "a[p]@t8n-cache-xyz": 1.0,
            "b[q]@bigmem": 2.0,
            "c": 3.0,
        }
        assert normalize_durations(raw) == {
            "a[p]": 1.0,
            "b[q]@bigmem": 2.0,
            "c": 3.0,
        }

    def test_collision_last_wins(self) -> None:
        """Collapsed cache keys resolve to the last input's value."""
        raw = {"a@t8n-cache-x": 1.0, "a@t8n-cache-y": 2.0}
        assert normalize_durations(raw) == {"a": 2.0}

    def test_empty_input(self) -> None:
        """Empty input returns empty output."""
        assert normalize_durations({}) == {}


class TestMergeDurations:
    """Tests for :func:`merge_durations`."""

    def test_disjoint_sources(self) -> None:
        """Disjoint inputs merge to their union."""
        merged = merge_durations(
            [{"a": 1.0}, {"b": 2.0}, {"c": 3.0}],
        )
        assert merged == {"a": 1.0, "b": 2.0, "c": 3.0}

    def test_overlap_last_wins(self) -> None:
        """Overlapping keys resolve to the last source's value."""
        merged = merge_durations([{"a": 1.0}, {"a": 2.0}])
        assert merged == {"a": 2.0}

    def test_empty(self) -> None:
        """Zero sources yield an empty dict."""
        assert merge_durations([]) == {}


class TestLoadAndWriteDurations:
    """Tests for :func:`load_durations` and :func:`write_durations`."""

    def test_round_trip(self, tmp_path: Path) -> None:
        """Writing then reading returns the original dict."""
        path = tmp_path / ".test_durations"
        data = {"a": 1.5, "b": 2.25}
        write_durations(path, data)
        assert load_durations(path) == data

    def test_load_missing_file_is_empty(self, tmp_path: Path) -> None:
        """Missing files load as empty dicts."""
        assert load_durations(tmp_path / "nope") == {}

    def test_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Non-existent parent directories are created on write."""
        path = tmp_path / "nested" / "dir" / ".test_durations"
        write_durations(path, {"x": 1.0})
        assert json.loads(path.read_text()) == {"x": 1.0}
