"""
Temporary pytest plugin for debugging pytest-split duration matching.

Loaded via ``-p split_debug_plugin`` after copying to ``tests/``.
Remove after diagnosis is complete.
"""

import json
import os
import sys

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Print diagnostics about pytest-split duration matching."""
    if not os.environ.get("CI"):
        return

    splits = getattr(config.option, "splits", None)
    group = getattr(config.option, "group", None)
    durations_path = getattr(config.option, "durations_path", None)

    print(f"\n[split-debug] === pytest-split diagnostics ===", flush=True)
    print(f"[split-debug] cwd={os.getcwd()}", flush=True)
    print(
        f"[split-debug] splits={splits} group={group}", flush=True
    )
    print(
        f"[split-debug] durations_path={durations_path}", flush=True
    )
    print(f"[split-debug] items_collected={len(items)}", flush=True)

    if durations_path is None:
        print("[split-debug] No durations_path configured", flush=True)
        return

    exists = os.path.exists(durations_path)
    print(f"[split-debug] file_exists={exists}", flush=True)

    if not exists:
        print("[split-debug] PROBLEM: file does not exist!", flush=True)
        # Check relative path too
        rel = os.path.exists(".test_durations")
        print(f"[split-debug] .test_durations exists={rel}", flush=True)
        return

    with open(durations_path) as f:
        durations = json.load(f)
    print(f"[split-debug] durations_entries={len(durations)}", flush=True)

    # Check matching
    matched = sum(1 for item in items if item.nodeid in durations)
    print(f"[split-debug] matched={matched}/{len(items)}", flush=True)

    if matched == 0 and items and durations:
        # Show samples for debugging the mismatch
        item_ids = [items[i].nodeid for i in range(min(3, len(items)))]
        dur_keys = sorted(durations.keys())[:3]
        print("[split-debug] ZERO MATCHES - showing samples:", flush=True)
        for nid in item_ids:
            print(f"[split-debug]   item: {nid!r}", flush=True)
        for dk in dur_keys:
            print(f"[split-debug]   dur:  {dk!r}", flush=True)
    elif matched < len(items):
        unmatched = [
            item.nodeid for item in items if item.nodeid not in durations
        ][:5]
        print(
            f"[split-debug] unmatched_sample ({len(items) - matched} total):",
            flush=True,
        )
        for nid in unmatched:
            print(f"[split-debug]   {nid!r}", flush=True)

    print("[split-debug] === end ===\n", flush=True)
    sys.stdout.flush()
    sys.stderr.flush()
