"""Unit tests for the setup-group merge helpers."""

import json
from pathlib import Path

from ..setup_groups import (
    StatefulSetupGroup,
    merge_partial_setup_group_files,
    write_partial_setup_group,
)


def _partial_paths(folder: Path) -> list[Path]:
    """List partials sorted for stable ordering."""
    return sorted(folder.glob("*.partial.*.json"))


def _final_paths(folder: Path) -> list[Path]:
    """List merged final files, excluding partials."""
    return sorted(
        p for p in folder.glob("*.json") if ".partial." not in p.name
    )


def test_merge_no_folder(tmp_path: Path) -> None:
    """Merging a non-existent folder is a no-op."""
    merge_partial_setup_group_files(tmp_path / "does-not-exist")


def test_merge_empty_folder(tmp_path: Path) -> None:
    """Merging an empty folder is a no-op and creates no files."""
    merge_partial_setup_group_files(tmp_path)
    assert _final_paths(tmp_path) == []


def test_merge_single_hash_multiple_partials(tmp_path: Path) -> None:
    """Partials with the same hash collapse and union their test_ids."""
    group = StatefulSetupGroup(
        network="Prague",
        setup_group_hash="abc",
        test_ids=["test_a"],
        payloads=[],
    )
    write_partial_setup_group(folder=tmp_path, group=group, test_suffix="a")

    group_b = group.model_copy(update={"test_ids": ["test_b"]})
    write_partial_setup_group(folder=tmp_path, group=group_b, test_suffix="b")

    # Duplicate — merge should de-duplicate on test_id.
    write_partial_setup_group(folder=tmp_path, group=group_b, test_suffix="b2")

    merge_partial_setup_group_files(tmp_path)

    # Partials are consumed; exactly one merged file remains.
    assert _partial_paths(tmp_path) == []
    finals = _final_paths(tmp_path)
    assert len(finals) == 1
    assert finals[0].name == "abc.json"

    merged = json.loads(finals[0].read_text())
    assert merged["setupGroupHash"] == "abc"
    assert merged["network"] == "Prague"
    assert sorted(merged["testIds"]) == ["test_a", "test_b"]


def test_merge_multiple_hashes(tmp_path: Path) -> None:
    """Partials with distinct hashes produce one merged file each."""
    group_a = StatefulSetupGroup(
        network="Prague",
        setup_group_hash="hash_a",
        test_ids=["a"],
        payloads=[],
    )
    group_b = StatefulSetupGroup(
        network="Prague",
        setup_group_hash="hash_b",
        test_ids=["b"],
        payloads=[],
    )
    write_partial_setup_group(folder=tmp_path, group=group_a, test_suffix="x")
    write_partial_setup_group(folder=tmp_path, group=group_b, test_suffix="y")

    merge_partial_setup_group_files(tmp_path)

    finals = {p.name for p in _final_paths(tmp_path)}
    assert finals == {"hash_a.json", "hash_b.json"}
    assert _partial_paths(tmp_path) == []


def test_write_partial_creates_folder(tmp_path: Path) -> None:
    """Writing a partial auto-creates a missing folder."""
    target = tmp_path / "nested" / "setup_groups"
    group = StatefulSetupGroup(
        network="Prague",
        setup_group_hash="h",
        test_ids=["t"],
        payloads=[],
    )
    write_partial_setup_group(folder=target, group=group, test_suffix="s")
    assert target.is_dir()
    assert len(list(target.glob("*.partial.*.json"))) == 1
