"""
Fixture collector class used to collect, sort and combine the different types
of generated fixtures.
"""

import itertools
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
    List,
    Literal,
    Optional,
    Tuple,
)

from execution_testing.base_types import to_json
from execution_testing.cli.pytest_commands.plugins.shared.fixture_output import (  # noqa: E501
    SUBFOLDER_LEVEL_SEPARATOR,
)

from .base import BaseFixture
from .consume import FixtureConsumer, TestCaseIndexFile
from .file import Fixtures

COPY_CHUNK_SIZE = 1 << 16

# Not ".json": a part file left behind by a killed worker must never be
# picked up as a fixture file by `consume` or `gen_index`.
PART_SUFFIX = ".part"

# Process-wide, not per collector: a worker builds one collector per test
# module under the same worker id, and two collectors reusing a sequence
# number would name the same part file.
_part_counter = itertools.count()


def _copy_indented(src: Path, out: IO[str]) -> None:
    """
    Append `src` to `out`, indenting every line after the first by four
    spaces.

    Copies fixed-size chunks rather than lines: a single fixture line (a
    transaction's calldata, a block access list) can be gigabytes. A newline
    is one character, so it can never straddle a chunk boundary.
    """
    with open(src) as f:
        while chunk := f.read(COPY_CHUNK_SIZE):
            out.write(chunk.replace("\n", "\n    "))


def merge_partial_fixture_files(output_dir: Path) -> None:
    """
    Merge all partial fixture files into final JSON fixture files.

    Called at session end after all workers have written their partials.
    Each partial JSONL file contains one line per fixture,
    {"k": fixture_id, "p": part_file_name}, pointing at a part file that
    holds that fixture's indented JSON.

    Fixture contents are streamed from the part files into the target, so
    memory is bounded by the number of fixtures, not by their size. An
    existing target is overwritten: the output directory is empty when a
    session starts, so one can only be left over from an interrupted merge.
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
        part_by_id: Dict[str, Path] = {}
        # Every part file, including any superseded by a later entry.
        part_files: List[Path] = []

        for partial in partials:
            with open(partial) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry = json.loads(line)
                        part_path = partial.parent / entry["p"]
                        part_by_id[entry["k"]] = part_path
                        part_files.append(part_path)

        # Write sorted entries to output file, streaming each part
        with open(target_path, "w") as out_f:
            out_f.write("{\n")
            sorted_keys = sorted(part_by_id.keys())
            last_idx = len(sorted_keys) - 1
            for i, key in enumerate(sorted_keys):
                out_f.write(f"    {json.dumps(key)}: ")
                _copy_indented(part_by_id[key], out_f)
                out_f.write(",\n" if i < last_idx else "\n")
            out_f.write("}")

        # Partials go first: an interrupted cleanup must never leave an index
        # line pointing at a deleted part, only orphan parts.
        for partial in partials:
            partial.unlink()
            # Also remove lock files
            lock_file = partial.with_suffix(".lock")
            if lock_file.exists():
                lock_file.unlink()
        for part_path in part_files:
            part_path.unlink()


@dataclass(kw_only=True, slots=True)
class TestInfo:
    """Contains test information from the current node."""

    __test__ = False  # stop pytest from collecting this class as a test

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

    def _worker_suffix(self) -> str:
        """Return the worker tag used in partial file names, e.g. ".gw0"."""
        worker_id = self._get_worker_id()
        return f".{worker_id}" if worker_id else ".main"

    def add_fixture(
        self,
        info: TestInfo,
        fixture: BaseFixture,
        output_subdir: Path | None = None,
    ) -> Path:
        """Add fixture and immediately write it to a part file."""
        fixture_basename = self.get_fixture_basename(info)
        if (
            output_subdir is not None
            and SUBFOLDER_LEVEL_SEPARATOR in output_subdir.name
        ):
            parts = fixture_basename.parts
            if parts and parts[0] == "benchmark":
                # Strip the "benchmark/" prefix from the fixture path so
                # files land directly under the gas-limit subdirectory.
                fixture_basename = Path(*parts[1:])

        format_output_dir = self.output_dir / fixture.output_base_dir_name()
        if output_subdir is not None and self.output_dir.name != "stdout":
            format_output_dir = format_output_dir / output_subdir

        fixture_path = format_output_dir / fixture_basename.with_suffix(
            fixture.output_file_extension
        )

        # File mode: write the fixture to disk now.
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
            index_entry = TestCaseIndexFile(
                id=info.get_id(),
                json_path=relative_path,
                fixture_hash=fixture.hash,
                fork=fixture_fork,
                format=fixture.format_class(),
                pre_hash=getattr(fixture, "pre_hash", None),
            )
            self._stream_index_entry_to_partial(index_entry)

        return fixture_path

    def _get_partial_fixture_file(self, fixture_path: Path) -> "IO[str]":
        """Get or create this worker's partial JSONL file for a target."""
        partial_path = fixture_path.with_suffix(
            f".partial{self._worker_suffix()}.jsonl"
        )

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
        """
        Write a fixture to its own part file and index it in the partial
        JSONL file.

        `json.dump` serialises straight into the file, so the fixture is
        never held as a single string. The part is created exclusively: a
        name clash with a part left over from an earlier session, whose
        index would still point at it, fails here rather than merging the
        wrong fixture.
        """
        partial_f = self._get_partial_fixture_file(fixture_path)
        part_path = self._next_part_path(fixture_path)
        with open(part_path, "x") as part_f:
            json.dump(fixture.json_dict_with_info(), part_f, indent=4)

        partial_f.write(
            json.dumps({"k": fixture_id, "p": part_path.name}) + "\n"
        )
        partial_f.flush()  # Ensure data is written immediately

    def _next_part_path(self, fixture_path: Path) -> Path:
        """Return the next part file path next to the target fixture file."""
        return fixture_path.with_suffix(
            f".partial{self._worker_suffix()}.{next(_part_counter)}"
            f"{PART_SUFFIX}"
        )

    def _get_partial_index_file(self) -> "IO[str]":
        """Get or create the file handle for streaming index entries."""
        if self._partial_index_file is None:
            partial_index_path = (
                self.output_dir
                / ".meta"
                / f"partial_index{self._worker_suffix()}.jsonl"
            )
            partial_index_path.parent.mkdir(parents=True, exist_ok=True)
            self._partial_index_file = open(partial_index_path, "a")

        return self._partial_index_file

    def _stream_index_entry_to_partial(self, entry: TestCaseIndexFile) -> None:
        """Stream a single index entry to partial JSONL file."""
        f = self._get_partial_index_file()
        f.write(entry.model_dump_json(exclude_none=True) + "\n")
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
