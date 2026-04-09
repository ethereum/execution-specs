#!/usr/bin/env python3
"""
Diagnose a pytest-split ``.test_durations`` file.

Report entry count, whether keys still carry ``@xdist_group``
suffixes (indicating incomplete normalization), and print sample
keys for quick visual comparison against collected test nodeids.

Usage::

    uv run python .github/scripts/diagnose_durations.py [path]

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

    data: dict[str, float] = json.loads(path.read_text())
    has_at = sum(1 for k in data if "@" in k)
    keys = sorted(data.keys())

    print(f"Durations file: {path}")
    print(f"  Entries: {len(data)}")
    print(f"  Keys with @ suffix: {has_at}/{len(data)}")
    if has_at:
        print(
            f"  WARNING: {has_at} keys still have @ suffixes"
            " — normalization may have failed"
        )

    print("  First 3 keys:")
    for k in keys[:3]:
        print(f"    {k}: {data[k]:.2f}s")
    print("  Last 3 keys:")
    for k in keys[-3:]:
        print(f"    {k}: {data[k]:.2f}s")


if __name__ == "__main__":
    main()
