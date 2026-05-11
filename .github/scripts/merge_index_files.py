#!/usr/bin/env python3
"""
Merge multiple .meta/index.json files from split fixture builds.

Accept fixture directories as arguments, load each directory's
``.meta/index.json``, merge them via ``IndexFile.merge()``, and write
the result to the specified output path.
"""

import sys
from pathlib import Path

from execution_testing.fixtures.consume import IndexFile


def main() -> None:
    """Entry point."""
    if len(sys.argv) < 3:
        print(
            "Usage: merge_index_files.py <output.json>"
            " <fixture_dir> [<fixture_dir> ...]",
            file=sys.stderr,
        )
        sys.exit(1)

    output_path = Path(sys.argv[1])
    fixture_dirs = [Path(d) for d in sys.argv[2:]]

    indexes: list[IndexFile] = []
    for d in fixture_dirs:
        index_path = d / ".meta" / "index.json"
        if not index_path.exists():
            print(f"Skipping {d} (no .meta/index.json)")
            continue
        indexes.append(IndexFile.model_validate_json(index_path.read_text()))

    if not indexes:
        print("No index files found, nothing to merge.")
        sys.exit(0)

    merged = IndexFile.merge(indexes)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(merged.model_dump_json(indent=2))
    print(f"Merged {len(indexes)} index files ({merged.test_count} tests)")


if __name__ == "__main__":
    main()
