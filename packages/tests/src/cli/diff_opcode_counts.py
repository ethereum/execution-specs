#!/usr/bin/env python
"""
Compare opcode counts between two folders of JSON fixtures.

This script crawls two folders for JSON files, parses them using the Fixtures
model, and compares the opcode_count field from the info section between
fixtures with the same name.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

import click

from ethereum_clis.cli_types import OpcodeCount
from ethereum_test_fixtures.file import Fixtures


def find_json_files(directory: Path) -> List[Path]:
    """Find all JSON files in a directory, excluding index.json files."""
    json_files = []
    if directory.is_dir():
        for file_path in directory.rglob("*.json"):
            if file_path.name != "index.json":
                json_files.append(file_path)
    return json_files


def load_fixtures_from_file(
    file_path: Path, remove_from_fixture_names: List[str]
) -> Optional[Fixtures]:
    """Load fixtures from a JSON file using the Fixtures model."""
    try:
        fixtures = Fixtures.model_validate_json(file_path.read_text())
        renames = []
        for k in fixtures.root:
            new_name = None
            for s in remove_from_fixture_names:
                if s in k:
                    if new_name is None:
                        new_name = k.replace(s, "")
                    else:
                        new_name = new_name.replace(s, "")
            if new_name is not None:
                renames.append((k, new_name))
        for old_name, new_name in renames:
            fixtures.root[new_name] = fixtures.root.pop(old_name)
        return fixtures
    except Exception as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
        return None


def extract_opcode_counts_from_fixtures(
    fixtures: Fixtures,
) -> Dict[str, OpcodeCount]:
    """Extract opcode_count from info field for each fixture."""
    opcode_counts = {}
    for fixture_name, fixture in fixtures.items():
        if (
            hasattr(fixture, "info")
            and fixture.info
            and "opcode_count" in fixture.info
        ):
            try:
                opcode_count = OpcodeCount.model_validate(
                    fixture.info["opcode_count"]
                )
                opcode_counts[fixture_name] = opcode_count
            except Exception as e:
                print(
                    f"Error parsing opcode_count for {fixture_name}: {e}",
                    file=sys.stderr,
                )
    return opcode_counts


def load_all_opcode_counts(
    directory: Path, remove_from_fixture_names: List[str]
) -> Dict[str, OpcodeCount]:
    """Load all opcode counts from all JSON files in a directory."""
    all_opcode_counts = {}
    json_files = find_json_files(directory)

    for json_file in json_files:
        fixtures = load_fixtures_from_file(
            json_file, remove_from_fixture_names=remove_from_fixture_names
        )
        if fixtures:
            file_opcode_counts = extract_opcode_counts_from_fixtures(fixtures)
            # Use fixture name as key, if there are conflicts, choose the last
            all_opcode_counts.update(file_opcode_counts)

    return all_opcode_counts


def compare_opcode_counts(
    count1: OpcodeCount, count2: OpcodeCount
) -> Dict[str, int]:
    """Compare two opcode counts and return the differences."""
    differences = {}

    # Get all unique opcodes from both counts
    all_opcodes = set(count1.root.keys()) | set(count2.root.keys())

    for opcode in all_opcodes:
        val1 = count1.root.get(opcode, 0)
        val2 = count2.root.get(opcode, 0)
        diff = val2 - val1
        if diff != 0:
            differences[str(opcode)] = diff

    return differences


@click.command()
@click.argument(
    "base", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.argument(
    "patch", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option(
    "--show-common",
    is_flag=True,
    help="Print fixtures that contain identical opcode counts.",
)
@click.option(
    "--show-missing",
    is_flag=True,
    help="Print fixtures only found in one of the folders.",
)
@click.option(
    "--remove-from-fixture-names",
    "-r",
    multiple=True,
    help="String to be removed from the fixture name, in case the fixture names have changed, "
    "in order to make the comparison easier. "
    "Can be specified multiple times.",
)
def main(
    base: Path,
    patch: Path,
    show_common: bool,
    show_missing: bool,
    remove_from_fixture_names: List[str],
) -> None:
    """Crawl two folders, compare and print opcode count diffs."""
    print(f"Loading opcode counts from {base}...")
    opcode_counts1 = load_all_opcode_counts(base, remove_from_fixture_names)
    print(f"Found {len(opcode_counts1)} fixtures with opcode counts")

    print(f"Loading opcode counts from {patch}...")
    opcode_counts2 = load_all_opcode_counts(patch, remove_from_fixture_names)
    print(f"Found {len(opcode_counts2)} fixtures with opcode counts")

    # Find common fixture names
    common_names = set(opcode_counts1.keys()) & set(opcode_counts2.keys())
    only_in_1 = set(opcode_counts1.keys()) - set(opcode_counts2.keys())
    only_in_2 = set(opcode_counts2.keys()) - set(opcode_counts1.keys())

    print("\nSummary:")
    print(f"  Common fixtures: {len(common_names)}")
    print(f"  Only in {base.name}: {len(only_in_1)}")
    print(f"  Only in {patch.name}: {len(only_in_2)}")

    # Show missing fixtures if requested
    if show_missing:
        if only_in_1:
            print(f"\nFixtures only in {base.name}:")
            for name in sorted(only_in_1):
                print(f"  {name}")

        if only_in_2:
            print(f"\nFixtures only in {patch.name}:")
            for name in sorted(only_in_2):
                print(f"  {name}")

    # Compare common fixtures
    differences_found = False
    common_with_same_counts = 0

    for fixture_name in sorted(common_names):
        count1 = opcode_counts1[fixture_name]
        count2 = opcode_counts2[fixture_name]

        differences = compare_opcode_counts(count1, count2)

        if differences:
            differences_found = True
            print(f"\n{fixture_name}:")
            for opcode, diff in sorted(differences.items()):
                if diff > 0:
                    print(f"  +{diff} {opcode}")
                else:
                    print(f"  {diff} {opcode}")
        elif show_common:
            print(f"\n{fixture_name}: No differences")
            common_with_same_counts += 1

    if not differences_found:
        print(
            "\nNo differences found in opcode counts between common fixtures!"
        )
    elif show_common:
        print(
            f"\n{common_with_same_counts} fixtures have identical opcode counts"
        )


if __name__ == "__main__":
    main()
