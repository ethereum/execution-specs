"""
Fixture collector class used to collect, sort and combine the different types
of generated fixtures.
"""

import heapq
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    IO,
    ClassVar,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
    Tuple,
)

from execution_testing.base_types import to_json

from .base import BaseFixture
from .consume import FixtureConsumer
from .file import Fixtures


def _sorted_entries_from_partial(
    partial_path: Path,
) -> Generator[Tuple[str, str], None, None]:
    """
    Generator yielding (key, value) pairs from a partial file, sorted by key.

    Loads one partial file into memory at a time (not all partials together).
    Each worker's partial file is typically small relative to the total.
    """
    entries = []
    with open(partial_path) as f:
        for line in f:
            line = line.strip()
            if line:
                entry = json.loads(line)
                entries.append((entry["k"], entry["v"]))
    entries.sort(key=lambda x: x[0])
    yield from entries


def merge_partial_fixture_files(output_dir: Path) -> None:
    """
    Merge all partial fixture JSONL files into final JSON fixture files.

    Called at session end after all workers have written their partials.
    Each partial file contains JSONL lines: {"k": fixture_id, "v": json_str}

    Uses k-way merge: each partial file is sorted individually, then merged
    using heapq.merge. This keeps memory usage proportional to the largest
    single partial file, not the total of all partials.
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
        # K-way merge: sort each partial individually, then merge streams
        # Memory = O(largest single partial), not O(sum of all partials)
        sorted_iterators = [_sorted_entries_from_partial(p) for p in partials]
        merged = heapq.merge(*sorted_iterators, key=lambda x: x[0])

        # Stream merged entries to output file
        with open(target_path, "w") as out_f:
            out_f.write("{\n")
            first = True
            for key, value in merged:
                if not first:
                    out_f.write(",\n")
                first = False
                key_json = json.dumps(key)
                value_indented = value.replace("\n", "\n    ")
                out_f.write(f"    {key_json}: {value_indented}")
            if not first:
                out_f.write("\n")
            out_f.write("}")

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
    generate_index: bool = True
    # Worker ID for partial files. None = read from env var.
    worker_id: Optional[str] = None

    # Internal state (only used for stdout mode)
    all_fixtures: Dict[Path, Fixtures] = field(default_factory=dict)

    # Streaming file handles - kept open for module duration
    _partial_fixture_files: Dict[Path, IO[str]] = field(default_factory=dict)
    _partial_index_file: Optional[IO[str]] = field(default=None)
    _worker_id_cached: bool = field(default=False, init=False)

    # Lightweight tracking for verification (path, format class, debug_path)
    # Only stores metadata, not fixture data - memory efficient
    _fixtures_to_verify: List[Tuple[Path, type, Optional[Path]]] = field(
        default_factory=list
    )

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

    def _get_worker_id(self) -> str | None:
        """Get the worker ID (from constructor or environment)."""
        if self.worker_id is not None:
            return self.worker_id
        if not self._worker_id_cached:
            # Cache the env var lookup
            env_worker_id = os.environ.get("PYTEST_XDIST_WORKER")
            if env_worker_id:
                self.worker_id = env_worker_id
            self._worker_id_cached = True
        return self.worker_id

    def add_fixture(self, info: TestInfo, fixture: BaseFixture) -> Path:
        """Add fixture and immediately stream to partial JSONL file."""
        fixture_basename = self.get_fixture_basename(info)

        fixture_path = (
            self.output_dir
            / fixture.output_base_dir_name()
            / fixture_basename.with_suffix(fixture.output_file_extension)
        )

        # Stream fixture directly to partial JSONL (no memory accumulation)
        if self.output_dir.name != "stdout":
            self._stream_fixture_to_partial(
                fixture_path, info.get_id(), fixture
            )
            # Track for verification (lightweight - only path and format class)
            debug_path = self._get_consume_direct_dump_dir(info)
            self._fixtures_to_verify.append(
                (fixture_path, fixture.__class__, debug_path)
            )
        else:
            # stdout mode: accumulate for final JSON dump
            if fixture_path not in self.all_fixtures:
                self.all_fixtures[fixture_path] = Fixtures(root={})
            self.all_fixtures[fixture_path][info.get_id()] = fixture

        # Stream index entry directly to partial JSONL
        if self.generate_index and self.output_dir.name != "stdout":
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
            self._stream_index_entry_to_partial(index_entry)

        return fixture_path

    def _get_partial_fixture_file(self, fixture_path: Path) -> "IO[str]":
        """Get or create a file handle for streaming fixtures."""
        worker_id = self._get_worker_id()
        suffix = f".{worker_id}" if worker_id else ".main"
        partial_path = fixture_path.with_suffix(f".partial{suffix}.jsonl")

        if partial_path not in self._partial_fixture_files:
            partial_path.parent.mkdir(parents=True, exist_ok=True)
            self._partial_fixture_files[partial_path] = open(partial_path, "a")

        return self._partial_fixture_files[partial_path]

    def _stream_fixture_to_partial(
        self,
        fixture_path: Path,
        fixture_id: str,
        fixture: BaseFixture,
    ) -> None:
        """Stream a single fixture to its partial JSONL file."""
        value = json.dumps(fixture.json_dict_with_info(), indent=4)
        line = json.dumps({"k": fixture_id, "v": value}) + "\n"

        f = self._get_partial_fixture_file(fixture_path)
        f.write(line)
        f.flush()  # Ensure data is written immediately

    def _get_partial_index_file(self) -> "IO[str]":
        """Get or create the file handle for streaming index entries."""
        if self._partial_index_file is None:
            worker_id = self._get_worker_id()
            suffix = f".{worker_id}" if worker_id else ".main"
            partial_index_path = (
                self.output_dir / ".meta" / f"partial_index{suffix}.jsonl"
            )
            partial_index_path.parent.mkdir(parents=True, exist_ok=True)
            self._partial_index_file = open(partial_index_path, "a")

        return self._partial_index_file

    def _stream_index_entry_to_partial(self, entry: Dict) -> None:
        """Stream a single index entry to partial JSONL file."""
        f = self._get_partial_index_file()
        f.write(json.dumps(entry) + "\n")
        f.flush()  # Ensure data is written immediately

    def close_streaming_files(self) -> None:
        """Close all open streaming file handles."""
        for f in self._partial_fixture_files.values():
            f.close()
        self._partial_fixture_files.clear()

        if self._partial_index_file is not None:
            self._partial_index_file.close()
            self._partial_index_file = None

    def dump_fixtures(self) -> None:
        """Dump collected fixtures (only used for stdout mode)."""
        if self.output_dir.name == "stdout":
            combined_fixtures = {
                k: to_json(v)
                for fixture in self.all_fixtures.values()
                for k, v in fixture.items()
            }
            json.dump(combined_fixtures, sys.stdout, indent=4)
            self.all_fixtures.clear()
        # For file output, fixtures are already streamed in add_fixture()

    def _get_consume_direct_dump_dir(self, info: TestInfo) -> Path | None:
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

    def verify_fixture_files(
        self, evm_fixture_verification: FixtureConsumer
    ) -> None:
        """
        Run `evm [state|block]test` on each fixture.

        For streaming mode, uses lightweight tracking of fixture paths/formats
        rather than keeping full fixtures in memory.
        """
        if self.output_dir.name == "stdout":
            # stdout mode: fixtures are in memory
            for fixture_path, name_fixture_dict in self.all_fixtures.items():
                for _fixture_name, fixture in name_fixture_dict.items():
                    if evm_fixture_verification.can_consume(fixture.__class__):
                        evm_fixture_verification.consume_fixture(
                            fixture.__class__,
                            fixture_path,
                            fixture_name=None,
                            debug_output_path=None,
                        )
        else:
            # Streaming mode: use tracked fixture metadata
            for entry in self._fixtures_to_verify:
                fixture_path, fixture_format, debug_path = entry
                if evm_fixture_verification.can_consume(fixture_format):
                    evm_fixture_verification.consume_fixture(
                        fixture_format,
                        fixture_path,
                        fixture_name=None,
                        debug_output_path=debug_path,
                    )
            # Clear tracking after verification
            self._fixtures_to_verify.clear()
