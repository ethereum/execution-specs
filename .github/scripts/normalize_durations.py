#!/usr/bin/env python3
"""
Normalize a pytest-split ``.test_durations`` file.

Strip ``@xdist_group`` suffixes from duration keys so they match the
nodeids pytest sees during collection (where the suffix has not yet
been added).

Usage::

    uv run python .github/scripts/normalize_durations.py [path]

*path* defaults to ``.test_durations`` in the current directory.
"""

import json
import sys
from pathlib import Path


def main() -> None:
    """Entry point."""
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".test_durations")

    if not path.exists():
        print(f"::warning::No durations file at {path}")
        return

    raw: dict[str, float] = json.loads(path.read_text())
    normalized = {k.split("@")[0]: v for k, v in raw.items()}
    path.write_text(json.dumps(normalized))

    collisions = len(raw) - len(normalized)
    print(
        f"Normalized {len(raw)} -> {len(normalized)} entries"
        f" ({collisions} collisions)"
    )


if __name__ == "__main__":
    main()
