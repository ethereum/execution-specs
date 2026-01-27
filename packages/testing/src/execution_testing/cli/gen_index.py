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
    append-only writes during fill. Entries are validated with Pydantic here.

    Args:
        output_dir: The fixture output directory.
        quiet_mode: If True, don't print status messages.

    """
    meta_dir = output_dir / ".meta"
    partial_files = list(meta_dir.glob("partial_index*.jsonl"))

    if not partial_files:
        raise Exception("No partial indexes found.")

    # Merge all partial indexes (JSONL format: one entry per line)
    # Read as raw dicts — the data was already validated when collected
    # from live Pydantic fixture objects in add_fixture().
    all_raw_entries: list[dict] = []
    all_forks: set = set()
    all_formats: set = set()

    for partial_file in partial_files:
        with open(partial_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry_data = json.loads(line)
                all_raw_entries.append(entry_data)
                # Collect forks and formats from raw strings
                if entry_data.get("fork"):
                    all_forks.add(entry_data["fork"])
                if entry_data.get("format"):
                    all_formats.add(entry_data["format"])

    # Compute root hash from raw dicts (no Pydantic needed)
    root_hash = HashableItem.from_raw_entries(all_raw_entries).hash()

    # Build final index — Pydantic validates the entire structure once
    # via model_validate(), not 96k individual model_validate() calls.
    index = IndexFile.model_validate(
        {
            "test_cases": all_raw_entries,
            "root_hash": HexNumber(root_hash),
            "created_at": datetime.datetime.now(),
            "test_count": len(all_raw_entries),
            "forks": list(all_forks),
            "fixture_formats": list(all_formats),
        }
    )

    # Write final index
    index_path = meta_dir / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(index.model_dump_json(exclude_none=True, indent=2))

    if not quiet_mode:
        rich.print(
            f"[green]Merged {len(partial_files)} partial indexes "
            f"({len(all_raw_entries)} test cases) into {index_path}[/]"
        )

    # Cleanup partial files
    for partial_file in partial_files:
        partial_file.unlink()


if __name__ == "__main__":
    generate_fixtures_index_cli()
