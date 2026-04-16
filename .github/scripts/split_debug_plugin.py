"""
Temporary conftest for debugging pytest-split duration matching.

Copied to ``tests/conftest.py`` in CI before the fill step.
Remove after diagnosis is complete.
"""

import sys


def _log(msg: str) -> None:
    print(f"[split-debug] {msg}", file=sys.stderr, flush=True)


def pytest_configure(config) -> None:
    """Monkey-patch pytest-split's algorithm to add diagnostics."""
    del config
    from pytest_split import algorithms

    original_get = algorithms._get_items_with_durations

    def patched_get(items, durations):
        filtered = algorithms._remove_irrelevant_durations(items, durations)
        avg = algorithms._get_avg_duration_per_test(filtered)
        _log(
            f"_get_items_with_durations: items={len(items)} "
            f"input_durations={len(durations)} "
            f"filtered={len(filtered)} avg={avg:.4f}"
        )
        if len(filtered) == 0 and len(durations) > 0 and len(items) > 0:
            _log("ZERO FILTERED - nodeids don't match cached durations!")
            for i in range(min(3, len(items))):
                _log(f"  item: {items[i].nodeid!r}")
            for k in sorted(durations.keys())[:3]:
                _log(f"  dur:  {k!r}")
        return original_get(items, durations)

    algorithms._get_items_with_durations = patched_get
    _log("Monkey-patched _get_items_with_durations")
