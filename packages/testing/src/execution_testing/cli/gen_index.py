"""
Generate an index file of all the json fixtures in the specified directory.
"""

import datetime
import json
import os
from pathlib import Path
from typing import List

import click
import rich
from rich.progress import (
    BarColumn,
    Column,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from execution_testing.base_types import HexNumber
from execution_testing.fixtures.consume import (
    IndexFile,
    TestCaseIndexFile,
)
from execution_testing.fixtures.file import Fixtures

from .hasher import HashableItem

# Files and directories to exclude from index generation
INDEX_EXCLUDED_FILES = frozenset({"index.json"})
INDEX_EXCLUDED_PATH_PARTS = frozenset({".meta", "pre_alloc"})


def count_json_files_exclude_index(start_path: Path) -> int:
    """Return the number of fixture json files in the specified directory."""
    json_file_count = sum(
        1
        for file in start_path.rglob("*.json")
        if file.name not in INDEX_EXCLUDED_FILES
        and not any(part in INDEX_EXCLUDED_PATH_PARTS for part in file.parts)
    )
    return json_file_count


@click.command(
    help=(
        "Generate an index file of all the json fixtures in the specified "
        "directory. The index file is saved as 'index.json' in the specified "
        "directory."
    )
)
@click.option(
    "--input",
    "-i",
    "input_dir",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, readable=True
    ),
    required=True,
    help="The input directory",
)
@click.option(
    "--quiet",
    "-q",
    "quiet_mode",
    is_flag=True,
    default=False,
    expose_value=True,
    help="Don't show the progress bar while processing fixture files.",
)
@click.option(
    "--force",
    "-f",
    "force_flag",
    is_flag=True,
    default=False,
    expose_value=True,
    help="Force re-generation of the index file, even if it already exists.",
)
def generate_fixtures_index_cli(
    input_dir: str, quiet_mode: bool, force_flag: bool
) -> None:
    """
    CLI wrapper to an index of all the fixtures in the specified directory.
    """
    generate_fixtures_index(
        Path(input_dir),
        quiet_mode=quiet_mode,
        force_flag=force_flag,
    )


def generate_fixtures_index(
    input_path: Path,
    quiet_mode: bool = False,
    force_flag: bool = False,
) -> None:
    """
    Generate an index file (index.json) of all the fixtures in specified dir.
    """
    total_files = 0
    if not os.path.isdir(input_path):  # caught by click if using via cli
        raise FileNotFoundError(f"The directory {input_path} does not exist.")
    if not quiet_mode:
        total_files = count_json_files_exclude_index(input_path)

    output_file = Path(f"{input_path}/.meta/index.json")
    output_file.parent.mkdir(
        parents=True, exist_ok=True
    )  # no meta dir in <=v3.0.0
    try:
        root_hash = HashableItem.from_folder(folder_path=input_path).hash()
    except (KeyError, TypeError):
        root_hash = b""  # just regenerate a new index file

    if not force_flag and output_file.exists():
        index_data: IndexFile
        try:
            with open(output_file, "r") as f:
                index_data = IndexFile(**json.load(f))
            if index_data.root_hash and index_data.root_hash == HexNumber(
                root_hash
            ):
                if not quiet_mode:
                    rich.print(
                        f"Index file [bold cyan]{output_file}[/] "
                        "is up-to-date."
                    )
                return
        except Exception as e:
            rich.print(f"Ignoring exception {e}")
            rich.print(
                f"...generating a new index file [bold cyan]{output_file}[/]"
            )

    filename_display_width = 25
    with Progress(
        TextColumn(
            "[bold cyan]"
            f"{{task.fields[filename]:<{filename_display_width}}}"
            "[/]",
            justify="left",
            table_column=Column(ratio=1),
        ),
        BarColumn(
            complete_style="green3",
            finished_style="bold green3",
            table_column=Column(ratio=2),
        ),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        expand=False,
        disable=quiet_mode,
    ) as progress:  # type: Progress
        task_id = progress.add_task(
            "[cyan]Processing files...", total=total_files, filename="..."
        )
        forks = set()
        fixture_formats = set()
        test_cases: List[TestCaseIndexFile] = []
        for file in input_path.rglob("*.json"):
            if file.name in INDEX_EXCLUDED_FILES or any(
                part in INDEX_EXCLUDED_PATH_PARTS for part in file.parts
            ):
                continue

            try:
                fixtures: Fixtures = Fixtures.model_validate_json(
                    file.read_text()
                )
            except Exception as e:
                rich.print(f"[red]Error loading fixtures from {file}[/red]")
                raise e

            relative_file_path = (
                Path(file).absolute().relative_to(Path(input_path).absolute())
            )
            for fixture_name, fixture in fixtures.items():
                fixture_fork = fixture.get_fork()
                test_cases.append(
                    TestCaseIndexFile(
                        id=fixture_name,
                        json_path=relative_file_path,
                        # eest uses hash; ethereum/tests uses generatedTestHash
                        fixture_hash=fixture.info.get("hash")
                        or f"0x{fixture.info.get('generatedTestHash')}",
                        fork=fixture_fork,
                        format=fixture.__class__,
                        pre_hash=getattr(fixture, "pre_hash", None),
                    )
                )
                if fixture_fork:
                    forks.add(fixture_fork)
                fixture_formats.add(fixture.format_name)

            display_filename = file.name
            if len(display_filename) > filename_display_width:
                display_filename = (
                    display_filename[: filename_display_width - 3] + "..."
                )
            else:
                display_filename = display_filename.ljust(
                    filename_display_width
                )

            progress.update(task_id, advance=1, filename=display_filename)

        progress.update(
            task_id,
            completed=total_files,
            filename="Indexing complete 🦄".ljust(filename_display_width),
        )

    index = IndexFile(
        test_cases=test_cases,
        root_hash=root_hash,
        created_at=datetime.datetime.now(),
        test_count=len(test_cases),
        forks=list(forks),
        fixture_formats=list(fixture_formats),
    )

    with open(output_file, "w") as f:
        f.write(index.model_dump_json(exclude_none=False, indent=2))


def merge_partial_indexes(output_dir: Path, quiet_mode: bool = False) -> None:
    """
    Merge partial index files from all workers into final index.json.

    This is called by pytest_sessionfinish on the master process after all
    workers have finished and written their partial indexes.

    Partial indexes use JSONL format (one JSON object per line) for efficient
    append-only writes during fill.

    Memory-optimized: Builds hash trie directly while streaming entries,
    avoiding accumulation of all entries in a single list. Writes final
    JSON by re-reading partials (2x I/O but ~50% less peak memory).

    Args:
        output_dir: The fixture output directory.
        quiet_mode: If True, don't print status messages.

    """
    meta_dir = output_dir / ".meta"
    partial_files = list(meta_dir.glob("partial_index*.jsonl"))

    if not partial_files:
        raise Exception("No partial indexes found.")

    # Pass 1: Build hash trie directly while streaming (no intermediate list)
    # Only keep what's needed for hash computation: path parts and fixture_hash
    root_trie: dict = {}
    all_forks: set = set()
    all_formats: set = set()
    test_count = 0

    for partial_file in partial_files:
        with open(partial_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                test_count += 1

                # Collect metadata
                if entry.get("fork"):
                    all_forks.add(entry["fork"])
                if entry.get("format"):
                    all_formats.add(entry["format"])

                # Insert directly into trie for hash computation
                fixture_hash = entry.get("fixture_hash")
                if not fixture_hash:
                    continue

                path_parts = Path(entry["json_path"]).parts
                current = root_trie

                # Navigate to parent folder, creating nodes as needed
                for part in path_parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

                # Add test entry to file node
                file_name = path_parts[-1]
                if file_name not in current:
                    current[file_name] = []

                hash_bytes = int(fixture_hash, 16).to_bytes(32, "big")
                current[file_name].append((entry["id"], hash_bytes))

    # Compute root hash from trie (reusing hasher's trie_to_hashable logic)
    root_hash = _trie_to_hash(root_trie)

    # Free trie memory before pass 2
    del root_trie

    # Pass 2: Stream entries to final JSON file (re-read partials)
    # This avoids keeping all entries in memory simultaneously
    index_path = meta_dir / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)

    with open(index_path, "w") as out_f:
        # Write header
        out_f.write("{\n")
        out_f.write(f'  "root_hash": "0x{root_hash.hex()}",\n')
        out_f.write(
            f'  "created_at": "{datetime.datetime.now().isoformat()}",\n'
        )
        out_f.write(f'  "test_count": {test_count},\n')
        out_f.write(f'  "forks": {json.dumps(sorted(all_forks))},\n')
        out_f.write(
            f'  "fixture_formats": {json.dumps(sorted(all_formats))},\n'
        )
        out_f.write('  "test_cases": [\n')

        # Stream test cases from partials (second read)
        first_entry = True
        for partial_file in partial_files:
            with open(partial_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if not first_entry:
                        out_f.write(",\n")
                    first_entry = False
                    # Write entry with indentation
                    entry = json.loads(line)
                    entry_json = json.dumps(entry, indent=2)
                    # Indent each line of the entry
                    indented = "\n".join(
                        "    " + ln for ln in entry_json.split("\n")
                    )
                    out_f.write(indented)

        out_f.write("\n  ]\n")
        out_f.write("}")

    if not quiet_mode:
        rich.print(
            f"[green]Merged {len(partial_files)} partial indexes "
            f"({test_count} test cases) into {index_path}[/]"
        )

    # Cleanup partial files
    for partial_file in partial_files:
        partial_file.unlink()


def _trie_to_hash(root_trie: dict) -> bytes:
    """
    Compute hash from trie structure built during streaming.

    Mirrors HashableItem.from_raw_entries logic but works on pre-built trie.
    """
    import hashlib

    def hash_node(node: dict) -> bytes:
        """Recursively hash a trie node."""
        hash_parts: list[bytes] = []

        for name in sorted(node.keys()):
            child = node[name]
            if isinstance(child, list):
                # File node: child is list of (test_id, hash_bytes)
                # Hash = sha256(sorted test hashes concatenated)
                test_hashes = [h for _, h in sorted(child, key=lambda x: x[0])]
                file_hash = hashlib.sha256(b"".join(test_hashes)).digest()
                hash_parts.append(file_hash)
            else:
                # Folder node: recurse
                hash_parts.append(hash_node(child))

        return hashlib.sha256(b"".join(hash_parts)).digest()

    return hash_node(root_trie)


if __name__ == "__main__":
    generate_fixtures_index_cli()
