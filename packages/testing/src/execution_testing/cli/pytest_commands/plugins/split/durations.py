"""
Utilities for pytest-split ``.test_durations`` files.

``--store-durations`` records nodeids with a ``@t8n-cache-<hash>``
suffix appended during execution, but pytest collection sees bare
nodeids. These helpers bridge the two so the plugin and the CI
scripts share one implementation of suffix stripping, normalization,
and per-group merging.

Only the ``@t8n-cache-*`` suffix is stripped. Other ``xdist_group``
markers (e.g. ``@bigmem``) and ``@`` characters inside parametrize
values (e.g. ``test[email@example.com]``) are preserved, matching
``filler._strip_xdist_group_suffix``.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path


def strip_xdist_suffix(nodeid: str) -> str:
    """Strip a ``@t8n-cache-*`` suffix from *nodeid*, if present."""
    if "@" in nodeid:
        base, suffix = nodeid.rsplit("@", 1)
        if suffix.startswith("t8n-cache-"):
            return base
    return nodeid


def normalize_durations(raw: dict[str, float]) -> dict[str, float]:
    """
    Return *raw* with ``@t8n-cache-*`` suffixes removed from every key.

    When two keys collapse to the same stripped form (e.g. runs with
    different t8n-cache ids), the last one wins.
    """
    return {strip_xdist_suffix(k): v for k, v in raw.items()}


def merge_durations(
    sources: Iterable[dict[str, float]],
) -> dict[str, float]:
    """
    Flat-merge *sources* into a single durations dict.

    Fork-range and pytest-split groups produce disjoint nodeid sets by
    construction, so collisions are expected to be empty; if any occur,
    the last source wins.
    """
    merged: dict[str, float] = {}
    for src in sources:
        merged.update(src)
    return merged


def load_durations(path: Path) -> dict[str, float]:
    """Read a ``.test_durations`` JSON file; empty dict if absent."""
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return {}


def write_durations(path: Path, data: dict[str, float]) -> None:
    """Serialize *data* as JSON to *path*, creating parents as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
