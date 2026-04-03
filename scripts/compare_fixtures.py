#!/usr/bin/env python3
"""
Compare two fixture directories by full JSON content.

Match fixtures across directories with different path layouts and naming
conventions. Fixtures are paired by (fork, normalized_name), ignoring
category directories since the same test can live in different categories
across static-fill and ported Python tests.

When multiple files match the same (fork, name), all combinations are
tried to find a content match.

The ``_info`` field is stripped before comparison (it contains source
paths and tool metadata that legitimately differ).

Usage:
    python scripts/compare_fixtures.py LEFT RIGHT
    python scripts/compare_fixtures.py LEFT RIGHT --show-missing
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def _normalize_name(name: str) -> str:
    """
    Normalize a fixture name for comparison.

    CamelCase -> snake_case, replace special chars, collapse underscores.
    """
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = s.lower()
    s = s.replace("+", "plus").replace("-", "minus")
    s = re.sub(r"[^a-z0-9]", "", s)
    if s.startswith("test_"):
        s = s[5:]
    return s


def _strip_info(obj: object) -> None:
    """Recursively remove all '_info' keys."""
    if isinstance(obj, dict):
        obj.pop("_info", None)
        for v in obj.values():
            _strip_info(v)
    elif isinstance(obj, list):
        for v in obj:
            _strip_info(v)


def _canonical_values(path: Path) -> list[str]:
    """Load fixture, strip _info, return sorted canonical values."""
    with open(path) as f:
        data = json.load(f)
    _strip_info(data)
    return sorted(json.dumps(v, sort_keys=True) for v in data.values())


def _index(root: Path) -> dict[tuple[str, str], list[Path]]:
    """
    Index state_test fixtures by (fork, normalized_name).

    Return {(fork, name): [paths]} — multiple paths per key are
    possible when the same test name exists in different categories.
    """
    idx: dict[tuple[str, str], list[Path]] = {}
    for p in root.rglob("*.json"):
        if ".meta" in p.parts:
            continue
        rel = str(p.relative_to(root))
        if not rel.startswith("state_tests/"):
            continue
        m = re.search(r"for_(\w+)/", rel)
        if not m:
            continue
        fork = m.group(1)
        name = _normalize_name(p.stem)
        idx.setdefault((fork, name), []).append(p)
    return idx


def compare(
    left: Path,
    right: Path,
    *,
    show_missing: bool = False,
) -> int:
    """Compare two fixture directories by full JSON content."""
    left_idx = _index(left)
    right_idx = _index(right)

    common_keys = sorted(set(left_idx) & set(right_idx))
    only_left = sorted(set(left_idx) - set(right_idx))
    only_right = sorted(set(right_idx) - set(left_idx))

    matched = 0
    mismatched = 0
    mismatch_details: list[str] = []

    for key in common_keys:
        l_paths = left_idx[key]
        r_paths = right_idx[key]

        # Try all path combinations to find a content match
        found = False
        for lp in l_paths:
            for rp in r_paths:
                try:
                    if _canonical_values(lp) == _canonical_values(rp):
                        found = True
                        break
                except Exception:
                    pass
            if found:
                break

        if found:
            matched += 1
        else:
            mismatched += 1
            fork, name = key
            mismatch_details.append(f"{fork}/{name}")

    # Left-only fixtures are errors (missing from right).
    errors = mismatched + len(only_left)

    print(f"Paired:     {len(common_keys)}")
    print(f"Matched:    {matched}/{len(common_keys)}")
    if mismatched:
        print(f"Mismatched: {mismatched}")
    print(f"Left only:  {len(only_left)}")
    print(f"Right only: {len(only_right)}")

    if errors:
        print(f"\nERRORS: {errors}")
    else:
        print("\nOK")

    if mismatch_details:
        print(f"\n-- Mismatched ({len(mismatch_details)}) --")
        for d in mismatch_details:
            print(f"  {d}")

    if show_missing:
        print(f"\n-- Only in {left} ({len(only_left)}) --")
        for key in only_left:
            print(f"  {'/'.join(key)}")
        print(f"\n-- Only in {right} ({len(only_right)}) --")
        for key in only_right:
            print(f"  {'/'.join(key)}")

    return errors


def main() -> None:
    """Compare two fixture directories by full JSON content."""
    parser = argparse.ArgumentParser(
        description=(
            "Compare fixture directories by full JSON content "
            "(stripping _info, sorting keys)."
        ),
    )
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument(
        "--show-missing",
        action="store_true",
        help="List fixtures present in only one directory",
    )
    args = parser.parse_args()
    result = compare(args.left, args.right, show_missing=args.show_missing)
    sys.exit(1 if result else 0)


if __name__ == "__main__":
    main()
