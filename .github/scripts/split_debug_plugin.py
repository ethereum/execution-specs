"""
Temporary conftest for debugging pytest-split duration matching.

Copied to ``tests/conftest.py`` in CI before the fill step.
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
    splits = getattr(config.option, "splits", None)
    group = getattr(config.option, "group", None)
    durations_path = getattr(config.option, "durations_path", None)

    def _log(msg: str) -> None:
        print(f"[split-debug] {msg}", file=sys.stderr, flush=True)

    _log("=== pytest-split diagnostics ===")
    _log(f"cwd={os.getcwd()}")
    _log(f"splits={splits} group={group}")
    _log(f"durations_path={durations_path}")
    _log(f"items_collected={len(items)}")

    if durations_path is None:
        _log("No durations_path configured")
        return

    exists = os.path.exists(durations_path)
    _log(f"file_exists={exists}")

    if not exists:
        _log("PROBLEM: durations file does not exist!")
        _log(f".test_durations in cwd exists={os.path.exists('.test_durations')}")
        return

    with open(durations_path) as f:
        durations = json.load(f)
    _log(f"durations_entries={len(durations)}")

    matched = sum(1 for item in items if item.nodeid in durations)
    _log(f"matched={matched}/{len(items)}")

    if matched == 0 and items and durations:
        item_ids = [items[i].nodeid for i in range(min(3, len(items)))]
        dur_keys = sorted(durations.keys())[:3]
        _log("ZERO MATCHES - showing samples:")
        for nid in item_ids:
            _log(f"  item: {nid!r}")
        for dk in dur_keys:
            _log(f"  dur:  {dk!r}")
    elif 0 < len(items) - matched <= 50:
        for item in items:
            if item.nodeid not in durations:
                _log(f"  unmatched: {item.nodeid!r}")
    elif matched < len(items):
        count = 0
        for item in items:
            if item.nodeid not in durations:
                _log(f"  unmatched: {item.nodeid!r}")
                count += 1
                if count >= 10:
                    _log(f"  ... and {len(items) - matched - count} more")
                    break

    _log("=== end ===")
