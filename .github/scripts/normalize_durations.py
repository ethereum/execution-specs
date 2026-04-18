#!/usr/bin/env python3
"""
Normalize a pytest-split ``.test_durations`` file in place.

Strip ``@xdist_group`` suffixes so the keys match the bare nodeids
pytest sees during collection. ``--store-durations`` records ids with
the suffix (e.g. ``@t8n-cache-<hash>``) added by xdist during
execution, so a normalization pass is required before a subsequent run
can look up durations.

Usage::

    uv run python .github/scripts/normalize_durations.py [path]

*path* defaults to ``.test_durations`` in the current directory.
"""

import sys
from pathlib import Path

from execution_testing.cli.pytest_commands.plugins.split.durations import (
    load_durations,
    normalize_durations,
    write_durations,
)


def main() -> None:
    """Entry point."""
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".test_durations")
    if not path.exists():
        print(f"::warning::No durations file at {path}")
        return

    raw = load_durations(path)
    normalized = normalize_durations(raw)
    write_durations(path, normalized)

    collisions = len(raw) - len(normalized)
    print(
        f"Normalized {len(raw)} -> {len(normalized)} entries"
        f" ({collisions} collisions)"
    )


if __name__ == "__main__":
    main()
