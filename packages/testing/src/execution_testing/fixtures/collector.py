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
    IO,
    ClassVar,
    Dict,
    Iterator,
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

#: Suffix of a per-fixture part file. Each fixture is written to its own file
#: containing nothing but that fixture's indented JSON, so neither the write
#: nor the merge ever holds a whole fixture in memory.
PART_SUFFIX = ".fixture.json"

#: Characters copied per read when streaming a part file into the merged
#: output. Deliberately small: a single fixture line can itself be megabytes
#: (one payload's transactions, or a block access list, is one hex string on
#: one line), so copying line-by-line would still scale with the longest line.
COPY_CHUNK_SIZE = 1 << 16

#: A top-level key line in a document this module wrote. `json.dumps(...,
#: indent=4)` puts top-level keys at exactly four spaces, and JSON escapes
#: newlines inside strings, so a line can only start this way at depth one.
_TOP_LEVEL_KEY = re.compile(r'^ {4}("(?:[^"\\]|\\.)*"): ')


def _copy_indented(src: Path, out: IO[str]) -> None:
    r"""
    Append `src` to `out`, indenting every line but the first by four spaces.

    Reproduces `value.replace("\\n", "\\n    ")` byte for byte without
    materialising either the value or the indented copy. Copying proceeds in
    fixed-size chunks rather than by line: chunk-wise replacement is exact
    because the pattern is the single character "\\n", which can never be
    split across a boundary, and a chunk never spans more than
    `COPY_CHUNK_SIZE` characters however long the line is.
    """
    with open(src) as f:
        while True:
            chunk = f.read(COPY_CHUNK_SIZE)
            if not chunk:
                break
            out.write(chunk.replace("\n", "\n    "))


def _copy_range(src: IO[str], out: IO[str], start: int, end: int) -> None:
    """Copy `src[start:end]` to `out` in bounded chunks."""
    src.seek(start)
    remaining = end - start
    while remaining > 0:
        chunk = src.read(min(COPY_CHUNK_SIZE, remaining))
        if not chunk:
            break
        out.write(chunk)
        remaining -= len(chunk)


def _iter_document_entries(path: Path) -> Iterator[Tuple[str, int, int]]:
    """
    Yield `(key, value_start, value_end)` for each top-level entry of a
    fixture document previously written by this module.

    Used to fold an existing target file into a new merge without parsing it,
    so re-running a session against an existing output stays O(1) in memory.
    The byte range is the value exactly as written, already indented for
    re-emission at depth one.
    """
    with open(path) as f:
        pending = None
        offset = 0
        for line in f:
            match = _TOP_LEVEL_KEY.match(line)
            if match:
                if pending is not None:
                    # The previous value ended before this line, minus ",\n".
                    yield pending[0], pending[1], offset - 2
                pending = (json.loads(match.group(1)), offset + match.end())
            offset += len(line)
        if pending is not None:
            # The last value ends before the document's closing "\n}".
            yield pending[0], pending[1], offset - 2


def merge_partial_fixture_files(output_dir: Path) -> None:
    """
    Merge per-fixture part files into final JSON fixture files.

    Called at session end after all workers have written their parts. Each
    worker appends one tiny JSONL line per fixture -- {"k": fixture_id,
    "p": part_filename} -- to a per-target index, and writes the fixture
    itself to `part_filename`.

    Memory is O(number of fixtures) for the index plus one copy chunk: a
    single fixture is never held in memory, however large it is. Output is
    byte-identical to `json.dumps(dict(sorted(...)), indent=4)`.
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
        # `sources` maps a fixture id to where its already-formatted value
        # lives, never to the value itself. Two shapes:
        #   ("part", path)        -- a per-fixture part file
        #   ("seed", start, end)  -- a byte range of the existing target
        sources: Dict[str, Tuple] = {}
        part_files: List[Path] = []

        # Fold in the existing target (if any) so repeated single-test
        # sessions accumulate into one file, as before. Recorded as byte
        # ranges rather than parsed, so a huge target costs nothing.
        seed_path: Optional[Path] = None
        if target_path.exists():
            seed_path = target_path.with_suffix(".seed.json")
            target_path.replace(seed_path)
            try:
                for key, start, end in _iter_document_entries(seed_path):
                    sources[key] = ("seed", start, end)
            except (OSError, ValueError):
                sources.clear()

        for partial in partials:
            with open(partial) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    entry = json.loads(line)
                    part_path = partial.parent / entry["p"]
                    sources[entry["k"]] = ("part", part_path)
                    part_files.append(part_path)

        # Write sorted entries, streaming each value from its source.
        seed_handle = open(seed_path) if seed_path is not None else None
        try:
            with open(target_path, "w") as out_f:
                out_f.write("{\n")
                sorted_keys = sorted(sources.keys())
                last_idx = len(sorted_keys) - 1
                for i, key in enumerate(sorted_keys):
                    out_f.write(f"    {json.dumps(key)}: ")
                    source = sources[key]
                    if source[0] == "part":
                        _copy_indented(source[1], out_f)
                    else:
                        assert seed_handle is not None
                        _copy_range(seed_handle, out_f, source[1], source[2])
                    out_f.write(",\n" if i < last_idx else "\n")
                out_f.write("}")
        finally:
            if seed_handle is not None:
                seed_handle.close()

        sources.clear()

        # Clean up index files, their part files, and the seed copy.
        for partial in partials:
            partial.unlink()
            # Also remove lock files
            lock_file = partial.with_suffix(".lock")
            if lock_file.exists():
                lock_file.unlink()
        for part in part_files:
            if part.exists():
                part.unlink()
        if seed_path is not None and seed_path.exists():
            seed_path.unlink()


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
    # Monotonic per-collector counter making part-file names unique.
    _part_counter: int = field(default=0)
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

    def add_fixture(
        self,
        info: TestInfo,
        fixture: BaseFixture,
        output_subdir: Path | None = None,
    ) -> Path:
        """Add fixture and immediately stream to partial JSONL file."""
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
        """
        Write a fixture to its own part file and index it.

        `json.dump` serialises straight into the file, so the fixture's JSON
        is never materialised as a string. The previous approach built the
        whole document with `json.dumps` and then embedded it, escaped, in a
        JSONL envelope -- two full-size copies on write and three more on
        merge, i.e. ~7x the fixture size. Benchmark prestate fixtures reach
        7 GB, where that reliably exhausted a 60 GB host.
        """
        part_path = self._next_part_path(fixture_path)
        part_path.parent.mkdir(parents=True, exist_ok=True)
        with open(part_path, "w") as part_f:
            json.dump(fixture.json_dict_with_info(), part_f, indent=4)

        f = self._get_partial_fixture_file(fixture_path)
        f.write(json.dumps({"k": fixture_id, "p": part_path.name}) + "\n")
        f.flush()  # Ensure data is written immediately

    def _next_part_path(self, fixture_path: Path) -> Path:
        """Return a unique part-file path for the next fixture of a target."""
        worker_id = self._get_worker_id()
        suffix = f".{worker_id}" if worker_id else ".main"
        stem = fixture_path.name[: -len(fixture_path.suffix)]
        seq = self._part_counter
        self._part_counter += 1
        return (
            fixture_path.parent / f"{stem}.partial{suffix}.{seq}{PART_SUFFIX}"
        )

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
