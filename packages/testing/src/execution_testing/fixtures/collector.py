"""
Fixture collector class used to collect, sort and combine the different types
of generated fixtures.
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    ClassVar,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
)

from filelock import FileLock

from execution_testing.base_types import to_json

from .base import BaseFixture
from .consume import FixtureConsumer
from .file import Fixtures


def merge_partial_fixture_files(output_dir: Path) -> None:
    """
    Merge all partial fixture JSONL files into final JSON fixture files.

    Called at session end after all workers have written their partials.
    Each partial file contains JSONL lines: {"k": fixture_id, "v": json_str}
    """
    # Find all partial files
    partial_files = list(output_dir.rglob("*.partial.*.jsonl"))
    if not partial_files:
        return

    # Group partial files by their target fixture file
    # e.g., "test.partial.gw0.jsonl" -> "test.json"
    partials_by_target: Dict[Path, List[Path]] = {}
    for partial in partial_files:
        # Remove .partial.{worker_id}.jsonl suffix to get target
        name = partial.name
        # Find ".partial." and remove everything after
        idx = name.find(".partial.")
        if idx == -1:
            continue
        target_name = name[:idx] + ".json"
        target_path = partial.parent / target_name
        if target_path not in partials_by_target:
            partials_by_target[target_path] = []
        partials_by_target[target_path].append(partial)

    # Merge each group into its target file
    for target_path, partials in partials_by_target.items():
        entries: Dict[str, str] = {}

        # Read all partial files
        for partial in partials:
            with open(partial) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    entries[entry["k"]] = entry["v"]

        # Write final JSON file
        sorted_keys = sorted(entries.keys())
        parts = ["{\n"]
        last_idx = len(sorted_keys) - 1
        for i, key in enumerate(sorted_keys):
            key_json = json.dumps(key)
            # Add indentation for nesting inside outer JSON object
            value_indented = entries[key].replace("\n", "\n    ")
            parts.append(f"    {key_json}: {value_indented}")
            parts.append(",\n" if i < last_idx else "\n")
        parts.append("}")
        target_path.write_text("".join(parts))

        # Clean up partial files
        for partial in partials:
            partial.unlink()
            # Also remove lock files
            lock_file = partial.with_suffix(".lock")
            if lock_file.exists():
                lock_file.unlink()


@dataclass(kw_only=True, slots=True)
class TestInfo:
    """Contains test information from the current node."""

    name: str  # pytest: Item.name, e.g. test_paris_one[fork_Paris-state_test]
    id: str  # pytest: Item.nodeid, e.g.
    # tests/paris/test_module_paris.py::test_paris_one[...]
    original_name: str  # pytest: Item.originalname, e.g. test_paris_one
    module_path: Path  # pytest: Item.path, e.g.
    # .../tests/paris/test_module_paris.py

    test_prefix: ClassVar[str] = "test_"  # Python test prefix
    filler_suffix: ClassVar[str] = "Filler"  # Static test suffix

    @classmethod
    def strip_test_name(cls, name: str) -> str:
        """Remove test prefix from a python test case name."""
        if name.startswith(cls.test_prefix):
            return name.removeprefix(cls.test_prefix)
        if name.endswith(cls.filler_suffix):
            return name.removesuffix(cls.filler_suffix)
        return name

    def get_name_and_parameters(self) -> Tuple[str, str]:
        """
        Convert test name to a tuple containing the test name and test
        parameters.

        Example: test_push0_key_sstore[fork_Shanghai] -> test_push0_key_sstore,
        fork_Shanghai
        """
        test_name, parameters = self.name.split("[")
        return test_name, re.sub(r"[\[\-]", "_", parameters).replace("]", "")

    def get_single_test_name(
        self, mode: Literal["module", "test"] = "module"
    ) -> str:
        """Convert test name to a single test name."""
        if mode == "module":
            # Use the module name as the test name
            return self.strip_test_name(self.original_name)
        elif mode == "test":
            # Mix the module name and the test name/arguments
            test_name, test_parameters = self.get_name_and_parameters()
            test_name = self.strip_test_name(test_name)
            return f"{test_name}__{test_parameters}"

    def get_dump_dir_path(
        self,
        base_dump_dir: Optional[Path],
        filler_path: Path,
        level: Literal[
            "test_module", "test_function", "test_parameter"
        ] = "test_parameter",
    ) -> Optional[Path]:
        """Path to dump the debug output as defined by the level to dump at."""
        if not base_dump_dir:
            return None
        test_module_relative_dir = self.get_module_relative_output_dir(
            filler_path
        )
        if level == "test_module":
            return Path(base_dump_dir) / Path(
                str(test_module_relative_dir).replace(os.sep, "__")
            )
        test_name, test_parameter_string = self.get_name_and_parameters()
        dir_str = str(test_module_relative_dir).replace(os.sep, "__")
        flat_path = f"{dir_str}__{test_name}"
        if level == "test_function":
            return Path(base_dump_dir) / flat_path
        elif level == "test_parameter":
            return Path(base_dump_dir) / flat_path / test_parameter_string
        raise Exception("Unexpected level.")

    def get_id(self) -> str:
        """Return the test id."""
        return self.id

    def get_module_relative_output_dir(self, filler_path: Path) -> Path:
        """
        Return a directory name for the provided test_module (relative to the
        base ./tests directory) that can be used for output (within the
        configured fixtures output path or the base_dump_dir directory).

        Example: tests/shanghai/eip3855_push0/test_push0.py ->
        shanghai/eip3855_push0/test_push0
        """
        basename = self.module_path.with_suffix("").absolute()
        basename_relative = basename.relative_to(
            os.path.commonpath([filler_path.absolute(), basename])
        )
        module_path = basename_relative.parent / self.strip_test_name(
            basename_relative.stem
        )
        return module_path


@dataclass(kw_only=True)
class FixtureCollector:
    """Collects all fixtures generated by the test cases."""

    output_dir: Path
    fill_static_tests: bool
    single_fixture_per_file: bool
    filler_path: Path
    base_dump_dir: Optional[Path] = None
    flush_interval: int = 1000
    generate_index: bool = True

    # Internal state
    all_fixtures: Dict[Path, Fixtures] = field(default_factory=dict)
    json_path_to_test_item: Dict[Path, TestInfo] = field(default_factory=dict)
    # Store index entries as simple dicts
    # (avoid Pydantic overhead during collection)
    index_entries: List[Dict] = field(default_factory=list)

    def get_fixture_basename(self, info: TestInfo) -> Path:
        """Return basename of the fixture file for a given test case."""
        module_relative_output_dir = info.get_module_relative_output_dir(
            self.filler_path
        )

        # Each legacy test filler has only 1 test per file if it's a !state
        # test! So no need to create directory Add11/add11.json it can be plain
        # add11.json
        if self.fill_static_tests:
            return module_relative_output_dir.parent / info.original_name

        if self.single_fixture_per_file:
            return module_relative_output_dir / info.get_single_test_name(
                mode="test"
            )
        return module_relative_output_dir / info.get_single_test_name(
            mode="module"
        )

    def add_fixture(self, info: TestInfo, fixture: BaseFixture) -> Path:
        """Add fixture to the list of fixtures of a given test case."""
        fixture_basename = self.get_fixture_basename(info)

        fixture_path = (
            self.output_dir
            / fixture.output_base_dir_name()
            / fixture_basename.with_suffix(fixture.output_file_extension)
        )
        # relevant when we group by test function
        if fixture_path not in self.all_fixtures.keys():
            self.all_fixtures[fixture_path] = Fixtures(root={})
            self.json_path_to_test_item[fixture_path] = info

        self.all_fixtures[fixture_path][info.get_id()] = fixture

        # Collect index entry while data is in memory (if indexing enabled)
        # Store as simple dict to avoid Pydantic overhead during collection
        if self.generate_index:
            relative_path = fixture_path.relative_to(self.output_dir)
            fixture_fork = fixture.get_fork()
            index_entry = {
                "id": info.get_id(),
                "json_path": str(relative_path),
                "fixture_hash": str(fixture.hash) if fixture.hash else None,
                "fork": fixture_fork.name() if fixture_fork else None,
                "format": fixture.format_name,
            }
            if (pre_hash := getattr(fixture, "pre_hash", None)) is not None:
                index_entry["pre_hash"] = pre_hash
            self.index_entries.append(index_entry)

        if (
            self.flush_interval > 0
            and len(self.all_fixtures) >= self.flush_interval
        ):
            self.dump_fixtures()

        return fixture_path

    def dump_fixtures(self, worker_id: str | None = None) -> None:
        """Dump all collected fixtures to their respective files."""
        if self.output_dir.name == "stdout":
            combined_fixtures = {
                k: to_json(v)
                for fixture in self.all_fixtures.values()
                for k, v in fixture.items()
            }
            json.dump(combined_fixtures, sys.stdout, indent=4)
            return
        os.makedirs(self.output_dir, exist_ok=True)
        for fixture_path, fixtures in self.all_fixtures.items():
            os.makedirs(fixture_path.parent, exist_ok=True)
            if len({fixture.__class__ for fixture in fixtures.values()}) != 1:
                raise TypeError(
                    "All fixtures in a single file must have the same format."
                )
            self._write_partial_fixtures(fixture_path, fixtures, worker_id)

        self.all_fixtures.clear()

    def _write_partial_fixtures(
        self, file_path: Path, fixtures: Fixtures, worker_id: str | None
    ) -> None:
        """
        Write fixtures to a partial JSONL file (append-only).

        Each line is a JSON object: {"key": "fixture_id", "value": "json_str"}
        This avoids O(n) merge work per worker - just O(1) append.
        Final merge to JSON happens at session end.
        """
        suffix = f".{worker_id}" if worker_id else ".main"
        partial_path = file_path.with_suffix(f".partial{suffix}.jsonl")
        partial_path.parent.mkdir(parents=True, exist_ok=True)
        lock_file_path = partial_path.with_suffix(".lock")

        lines = []
        for name in fixtures:
            value = json.dumps(fixtures[name].json_dict_with_info(), indent=4)
            # Store as JSONL: {"k": key, "v": serialized value string}
            lines.append(json.dumps({"k": name, "v": value}) + "\n")

        with FileLock(lock_file_path):
            with open(partial_path, "a") as f:
                f.writelines(lines)

    def verify_fixture_files(
        self, evm_fixture_verification: FixtureConsumer
    ) -> None:
        """Run `evm [state|block]test` on each fixture."""
        for fixture_path, name_fixture_dict in self.all_fixtures.items():
            for _fixture_name, fixture in name_fixture_dict.items():
                if evm_fixture_verification.can_consume(fixture.__class__):
                    info = self.json_path_to_test_item[fixture_path]
                    consume_direct_dump_dir = (
                        self._get_consume_direct_dump_dir(info)
                    )
                    evm_fixture_verification.consume_fixture(
                        fixture.__class__,
                        fixture_path,
                        fixture_name=None,
                        debug_output_path=consume_direct_dump_dir,
                    )

    def _get_consume_direct_dump_dir(
        self,
        info: TestInfo,
    ) -> Path | None:
        """
        Directory to dump the current test function's fixture.json and fixture
        verification debug output.
        """
        if not self.base_dump_dir:
            return None
        if self.single_fixture_per_file:
            return info.get_dump_dir_path(
                self.base_dump_dir, self.filler_path, level="test_parameter"
            )
        else:
            return info.get_dump_dir_path(
                self.base_dump_dir, self.filler_path, level="test_function"
            )

    def write_partial_index(self, worker_id: str | None = None) -> Path | None:
        """
        Append collected index entries to a partial index file using JSONL
        format.

        Uses append-only JSONL (JSON Lines) format for efficient writes without
        read-modify-write cycles. Each line is a complete JSON object
        representing one index entry.

        Args:
            worker_id: The xdist worker ID (e.g., "gw0"), or None for master.

        Returns:
            Path to the partial index file, or None if indexing is disabled.

        """
        if not self.generate_index or not self.index_entries:
            return None

        suffix = f".{worker_id}" if worker_id else ".master"
        partial_index_path = (
            self.output_dir / ".meta" / f"partial_index{suffix}.jsonl"
        )
        partial_index_path.parent.mkdir(parents=True, exist_ok=True)
        lock_file_path = partial_index_path.with_suffix(".lock")

        # Append entries as JSONL (one JSON object per line)
        # This avoids read-modify-write cycles
        with FileLock(lock_file_path):
            with open(partial_index_path, "a") as f:
                for entry in self.index_entries:
                    f.write(json.dumps(entry) + "\n")

        return partial_index_path
