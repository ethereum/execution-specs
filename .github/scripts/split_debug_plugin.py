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
    # Only run once (on first worker or controller), not 48 times.
    if hasattr(config, "_split_debug_done"):
        return
    config._split_debug_done = True

    splits = getattr(config.option, "splits", None)
    group = getattr(config.option, "group", None)
    durations_path = getattr(config.option, "durations_path", None)
    algorithm = getattr(config.option, "splitting_algorithm", None)

    def _log(msg: str) -> None:
        print(f"[split-debug] {msg}", file=sys.stderr, flush=True)

    _log("=== pytest-split diagnostics ===")
    _log(f"cwd={os.getcwd()}")
    _log(f"splits={splits} group={group} algorithm={algorithm}")
    _log(f"durations_path={durations_path}")
    _log(f"items_collected={len(items)}")

    # Check if PytestSplitPlugin is registered
    split_plugin = config.pluginmanager.get_plugin("pytestsplitplugin")
    _log(f"PytestSplitPlugin registered={split_plugin is not None}")
    if split_plugin is not None:
        cached = getattr(split_plugin, "cached_durations", None)
        _log(f"PytestSplitPlugin.cached_durations entries="
             f"{len(cached) if cached else 0}")
        if cached:
            # Check if cached durations have @ suffixes
            at_count = sum(1 for k in cached if "@" in k)
            _log(f"PytestSplitPlugin cached keys with @={at_count}")
            # Check matching against current items
            matched_cached = sum(
                1 for item in items if item.nodeid in cached
            )
            _log(f"PytestSplitPlugin cached matched="
                 f"{matched_cached}/{len(items)}")
            if matched_cached == 0 and items:
                _log("ZERO CACHED MATCHES - samples:")
                for i in range(min(3, len(items))):
                    _log(f"  item: {items[i].nodeid!r}")
                cached_keys = sorted(cached.keys())[:3]
                for k in cached_keys:
                    _log(f"  cached: {k!r}")

    if durations_path is None:
        _log("No durations_path configured")
        return

    exists = os.path.exists(durations_path)
    _log(f"file_exists={exists}")

    if not exists:
        _log("PROBLEM: durations file does not exist!")
        return

    with open(durations_path) as f:
        durations = json.load(f)
    _log(f"file_durations_entries={len(durations)}")

    matched = sum(1 for item in items if item.nodeid in durations)
    _log(f"file_matched={matched}/{len(items)}")

    _log("=== end ===")
