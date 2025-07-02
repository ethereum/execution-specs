"""
Compare two fixture folders and remove duplicates based on fixture hashes.

This tool reads the .meta/index.json files from two fixture directories and identifies
fixtures with identical hashes on a test case basis, then removes the duplicates from
both of the folders. Used within the coverage workflow.
"""

import json
import shutil
import sys
from pathlib import Path
from typing import Set

import click

from ethereum_test_base_types import HexNumber
from ethereum_test_fixtures.consume import IndexFile, TestCaseIndexFile


def get_index_path(folder: Path) -> Path:
    """Get the path to an index in a given folder."""
    return folder / ".meta" / "index.json"


def load_index(folder: Path) -> IndexFile:
    """Load the index.json file from a fixture folder."""
    index_path = get_index_path(folder)
    if not index_path.exists():
        raise FileNotFoundError(f"Index file not found: {index_path}")

    return IndexFile.model_validate_json(index_path.read_text())


def get_fixture_hashes(index: IndexFile) -> Set[HexNumber]:
    """Extract fixture hashes and their corresponding file paths from index."""
    hash_set = set()

    for test_case in index.test_cases:
        if test_case.fixture_hash is None:
            continue
        hash_set.add(test_case.fixture_hash)

    return hash_set


def find_duplicates(base_hashes: Set[HexNumber], patch_hashes: Set[HexNumber]) -> Set[HexNumber]:
    """Find fixture hashes that exist in both base and patch."""
    return base_hashes & patch_hashes


def pop_by_hash(index: IndexFile, fixture_hash: HexNumber) -> TestCaseIndexFile:
    """Pops a single test case from an index file by its hash."""
    for i in range(len(index.test_cases)):
        if index.test_cases[i].fixture_hash == fixture_hash:
            return index.test_cases.pop(i)
    raise Exception(f"Hash {fixture_hash} not found in index.")


def remove_fixture_from_file(file: Path, test_case_id: str):
    """Remove a single fixture by its ID from a generic fixture file."""
    try:
        # Load from json to a dict
        full_file = json.loads(file.read_text())
        full_file.pop(test_case_id)
        file.write_text(json.dumps(full_file, indent=2))
    except FileNotFoundError:
        raise FileNotFoundError(f"Fixture file not found: {file}") from None
    except KeyError:
        raise KeyError(f"Test case {test_case_id} not found in {file}") from None


def remove_fixture(
    folder: Path,
    index: IndexFile,
    fixture_hash: HexNumber,
    dry_run: bool,
):
    """Remove a single fixture from a folder that matches the given hash."""
    test_case = pop_by_hash(index, fixture_hash)
    test_case_file = folder / test_case.json_path
    if dry_run:
        print(f"Remove {test_case.id} from {test_case_file}")
    else:
        remove_fixture_from_file(test_case_file, test_case.id)


def rewrite_index(folder: Path, index: IndexFile, dry_run: bool):
    """
    Rewrite the index to the correct index file, or if the test count was reduced to zero,
    the entire directory is deleted.
    """
    if len(index.test_cases) > 0:
        # Just rewrite the index
        if not dry_run:
            with open(get_index_path(folder), "w") as f:
                f.write(index.model_dump_json(exclude_none=False, indent=2))
        else:
            print(f"Would rewrite index for {folder}")
    else:
        # Delete the folder
        if not dry_run:
            shutil.rmtree(folder)
        else:
            print(f"Would delete {folder}")


@click.command()
@click.argument("base", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.argument("patch", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--dry-run", is_flag=True, help="Show what would be removed without actually removing"
)
@click.option(
    "--abort-on-empty-patch",
    is_flag=True,
    help="Abort if the patch folder would be empty after fixture removal.",
)
def main(
    base: Path,
    patch: Path,
    dry_run: bool,
    abort_on_empty_patch: bool,
):
    """Compare two fixture folders and remove duplicates based on fixture hashes."""
    try:
        # Load indices
        base_index = load_index(base)
        base_hashes = get_fixture_hashes(base_index)

        patch_index = load_index(patch)
        patch_hashes = get_fixture_hashes(patch_index)

        # Find duplicates
        duplicate_hashes = find_duplicates(base_hashes, patch_hashes)

        if not duplicate_hashes:
            click.echo("No duplicates found.")
            sys.exit(0)
        else:
            click.echo(f"Found {len(duplicate_hashes)} duplicates.")

        if abort_on_empty_patch and duplicate_hashes == patch_hashes:
            click.echo("Patch folder would be empty after fixture removal.")
            sys.exit(0)

        for duplicate_hash in duplicate_hashes:
            # Remove from both folders
            remove_fixture(base, base_index, duplicate_hash, dry_run)
            remove_fixture(patch, patch_index, duplicate_hash, dry_run)

        # Rewrite indices if necessary
        rewrite_index(base, base_index, dry_run)
        rewrite_index(patch, patch_index, dry_run)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
