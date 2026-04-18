#!/usr/bin/env python3
"""
Merge multiple pytest-split ``.test_durations`` files.

Accept an output path and one or more input ``.test_durations`` JSON
files and flat-merge them into one file. Splits produce disjoint test
sets by construction, so collisions are not expected; when they do
occur the last input wins.

Usage::

    uv run python .github/scripts/merge_durations_files.py \
        <output.json> <durations_file> [<durations_file> ...]
"""

import sys
from pathlib import Path

from execution_testing.cli.pytest_commands.plugins.split.durations import (
    load_durations,
    merge_durations,
    write_durations,
)


def main() -> None:
    """Entry point."""
    if len(sys.argv) < 3:
        print(
            "Usage: merge_durations_files.py <output.json>"
            " <durations_file> [<durations_file> ...]",
            file=sys.stderr,
        )
        sys.exit(1)

    output_path = Path(sys.argv[1])
    inputs = [Path(p) for p in sys.argv[2:]]

    sources: list[dict[str, float]] = []
    count = 0
    for path in inputs:
        if not path.exists():
            print(f"Skipping {path} (not found)")
            continue
        sources.append(load_durations(path))
        count += 1

    if not sources:
        print("No durations found, nothing to merge.")
        sys.exit(0)

    merged = merge_durations(sources)
    write_durations(output_path, merged)
    print(f"Merged {count} durations files ({len(merged)} tests)")


if __name__ == "__main__":
    main()
