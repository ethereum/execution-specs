#!/usr/bin/env python3
"""
Merge multiple pytest-split .test_durations files from split builds.

Accept an output path and one or more input ``.test_durations`` JSON
files.  Each file is a flat ``{"test::node::id": seconds, ...}`` dict.
Since fork-range splits produce disjoint test sets, keys are merged
without conflict.
"""

import json
import sys
from pathlib import Path


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
    input_files = [Path(f) for f in sys.argv[2:]]

    merged: dict[str, float] = {}
    count = 0
    for f in input_files:
        if not f.exists():
            print(f"Skipping {f} (not found)")
            continue
        data = json.loads(f.read_text())
        merged.update(data)
        count += 1

    if not merged:
        print("No durations found, nothing to merge.")
        sys.exit(0)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"Merged {count} durations files ({len(merged)} tests)")


if __name__ == "__main__":
    main()
