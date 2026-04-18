#!/usr/bin/env python3
"""
Diagnose a pytest-split ``.test_durations`` file.

Report entry count, whether keys still carry ``@xdist_group`` suffixes
(indicating incomplete normalization), and print sample keys for
quick visual comparison against collected test nodeids.

Usage::

    uv run python .github/scripts/diagnose_durations.py [path]

*path* defaults to ``.test_durations`` in the current directory.
"""

import sys
from pathlib import Path

from execution_testing.cli.pytest_commands.plugins.split.durations import (
    load_durations,
)


def main() -> None:
    """Entry point."""
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".test_durations")
    if not path.exists():
        print(f"::warning::No durations file at {path}")
        return

    data = load_durations(path)
    has_at = sum(1 for k in data if "@" in k)
    keys = sorted(data)
    abs_path = path.resolve()

    print(f"Durations file: {path}")
    print(f"  Entries: {len(data)}")
    print(f"  Keys with @ suffix: {has_at}/{len(data)}")
    if has_at:
        print(
            f"  WARNING: {has_at} keys still have @ suffixes"
            " - normalization may have failed"
        )

    for label, sample in (
        ("First 3 keys:", keys[:3]),
        ("Last 3 keys:", keys[-3:]),
    ):
        print(f"  {label}")
        for k in sample:
            print(f"    {k}: {data[k]:.2f}s")

    print(f"  Absolute path: {abs_path}")
    print(f"  File size: {abs_path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
