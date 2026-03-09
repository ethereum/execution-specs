#!/usr/bin/env python3
"""
Compare two fixture directories by post-state hashes.

Matches fixtures across directories with different path layouts and
naming conventions:
  compiled:  state_tests/for_{fork}/static/state_tests/{cat}/{Name}.json
  generated: state_tests/for_{fork}/ported_static/{cat}/{name}/{name}.json

Fixtures are paired by (category, normalized_name) across all fork
directories.  Names are normalized via the same transforms as
fixture_to_python.py so that ``addNonConst`` matches ``add_non_const``.
Post-state hashes are compared only for forks present on both sides.

Unmatched fixtures (present on one side only) are treated as errors.

Usage:
    python scripts/compare_fixtures.py LEFT RIGHT
    python scripts/compare_fixtures.py LEFT RIGHT --show-missing
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# Key = (category, normalized_name)
FixtureKey = tuple[str, str]

# Category directories start with these prefixes (case-sensitive).
# "st" is followed by an uppercase letter (stBugs, stCallCodes, ...)
# "vm" and "VM" are followed by anything (vmArith, VMTests, ...)
_CATEGORY_RE = re.compile(r"^(st[A-Z]|vm|VM)")


def _normalize_name(name: str) -> str:
    """
    Normalize a fixture name for comparison.

    Apply the same transforms as filler_name_to_test_name minus the
    ``test_`` prefix:  camelCase -> snake_case, replace special chars,
    collapse underscores.
    """
    # CamelCase -> snake_case
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    s = s.lower()
    # Replace + and - with descriptive words before general cleanup
    s = s.replace("+", "_plus_")
    s = s.replace("-", "_minus_")
    # Replace remaining non-alphanumeric (except _) with _
    s = re.sub(r"[^a-z0-9_]", "_", s)
    # Collapse multiple underscores
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def _parse_entry(path: Path, root: Path) -> tuple[FixtureKey, str] | None:
    """
    Extract ((category, normalized_name), fork) from a fixture path.

    Return None if the path doesn't match a recognizable layout.
    """
    parts = path.relative_to(root).parts

    # Find fork directory
    fork = next((p for p in parts if p.startswith("for_")), None)
    if fork is None:
        return None

    # Everything between fork and the filename
    fork_pos = parts.index(fork)
    between = parts[fork_pos + 1 : -1]

    # Walk backwards to find the category dir
    category = None
    for part in reversed(between):
        if _CATEGORY_RE.match(part):
            category = part
            break

    if category is None:
        return None

    name = _normalize_name(path.stem)
    # Strip leading test_ prefix so compiled "AddNonConst" and filled
    # "test_add_non_const" both normalize to "add_non_const".
    if name.startswith("test_"):
        name = name[5:]
    return ((category, name), fork)


def _post_hashes(path: Path) -> set[tuple[str, str]]:
    """Extract the set of (fork, hash) from all post entries."""
    hashes: set[tuple[str, str]] = set()
    for _key, test in json.loads(path.read_text()).items():
        for fork, entries in test.get("post", {}).items():
            for entry in entries:
                h = entry.get("hash", "")
                if h:
                    hashes.add((fork, h))
    return hashes


def _index(
    root: Path,
) -> dict[FixtureKey, dict[str, Path]]:
    """
    Index fixture JSONs by (category, normalized_name).

    Return {key: {fork: path, ...}} collecting all fork variants.
    """
    idx: dict[FixtureKey, dict[str, Path]] = defaultdict(dict)
    for p in root.rglob("*.json"):
        if ".meta" in p.parts:
            continue
        result = _parse_entry(p, root)
        if result is None:
            continue
        key, fork = result
        # Keep first file per (key, fork)
        if fork not in idx[key]:
            idx[key][fork] = p
    return dict(idx)


def compare(
    left: Path,
    right: Path,
    *,
    show_missing: bool = False,
) -> int:
    """Compare two fixture directories. Return number of errors."""
    left_idx = _index(left)
    right_idx = _index(right)

    common = sorted(set(left_idx) & set(right_idx))
    only_left = sorted(set(left_idx) - set(right_idx))
    only_right = sorted(set(right_idx) - set(left_idx))

    mismatches = 0
    no_common_fork = 0

    for key in common:
        l_forks = left_idx[key]
        r_forks = right_idx[key]
        shared_forks = set(l_forks) & set(r_forks)

        if not shared_forks:
            # No common fork dirs — compare post hashes by fork name
            # inside the JSON (the JSON contains per-fork post entries
            # regardless of which for_X directory it sits in).
            lh: set[tuple[str, str]] = set()
            for p in l_forks.values():
                lh |= _post_hashes(p)
            rh: set[tuple[str, str]] = set()
            for p in r_forks.values():
                rh |= _post_hashes(p)

            # Find forks present in both JSONs
            l_fork_names = {f for f, _ in lh}
            r_fork_names = {f for f, _ in rh}
            common_forks = l_fork_names & r_fork_names

            if not common_forks:
                no_common_fork += 1
                continue

            lh_f = {(f, h) for f, h in lh if f in common_forks}
            rh_f = {(f, h) for f, h in rh if f in common_forks}

            if lh_f != rh_f:
                mismatches += 1
                print(f"MISMATCH {'/'.join(key)} (cross-fork)")
                diff_l = lh_f - rh_f
                diff_r = rh_f - lh_f
                print(
                    f"  {len(diff_l)} only in left,"
                    f" {len(diff_r)} only in right"
                )
        else:
            # Compare within shared fork directories
            for fork in sorted(shared_forks):
                lh_s = _post_hashes(l_forks[fork])
                rh_s = _post_hashes(r_forks[fork])
                if lh_s != rh_s:
                    mismatches += 1
                    print(f"MISMATCH {'/'.join(key)} ({fork})")
                    print(f"  left:  {l_forks[fork]}")
                    print(f"  right: {r_forks[fork]}")
                    diff_l = lh_s - rh_s
                    diff_r = rh_s - lh_s
                    print(
                        f"  {len(diff_l)} only in left,"
                        f" {len(diff_r)} only in right"
                    )

    total = len(common)
    matched = total - mismatches - no_common_fork
    # Mismatches and left-only (missing from generated) are errors.
    # Right-only (extra generated, e.g. fork-specific fillers) are
    # warnings — the generated side may legitimately have tests that
    # the compiled reference lacks.
    errors = mismatches + len(only_left)

    print()
    print(f"Paired:     {total}")
    print(f"Matched:    {matched}/{total}")
    if mismatches:
        print(f"Mismatched: {mismatches}")
    if no_common_fork:
        print(f"No common fork to compare: {no_common_fork}")
    if only_left:
        print(f"Left only:  {len(only_left)}  (ERROR)")
    if only_right:
        print(f"Right only: {len(only_right)}")

    if errors:
        print(f"\nERRORS: {errors}")
    else:
        print("\nOK")

    if show_missing and only_left:
        print(f"\n-- Only in {left} ({len(only_left)}) --")
        for key in only_left:
            print(f"  {'/'.join(key)}")

    if show_missing and only_right:
        print(f"\n-- Only in {right} ({len(only_right)}) --")
        for key in only_right:
            print(f"  {'/'.join(key)}")

    return errors


def main() -> None:
    """Compare two fixture directories by post-state hashes."""
    parser = argparse.ArgumentParser(
        description="Compare fixture directories by post-state hashes.",
    )
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument(
        "--show-missing",
        action="store_true",
        help="List fixtures that exist in only one directory",
    )
    args = parser.parse_args()
    result = compare(args.left, args.right, show_missing=args.show_missing)
    sys.exit(1 if result else 0)


if __name__ == "__main__":
    main()
