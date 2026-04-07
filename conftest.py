"""
Root conftest for grouped test splitting.

When ``--splitting-algorithm grouped_least_duration`` is passed alongside
``--splits`` and ``--group``, this hook replaces pytest-split's built-in
splitting with a ``(function, fork)``-aware algorithm that keeps cache-
sharing parametrizations on the same runner.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.nodes import Item

ALGORITHM_NAME = "grouped_least_duration"


def pytest_configure(config: Config) -> None:
    """Unregister pytest-split's plugin when using our custom algorithm."""
    algo = config.getoption("splitting_algorithm", default=None)
    splits = config.getoption("splits", default=None)
    group = config.getoption("group", default=None)

    if algo == ALGORITHM_NAME and splits and group:
        plugin = config.pluginmanager.get_plugin("pytestsplitplugin")
        if plugin is not None:
            config.pluginmanager.unregister(plugin, "pytestsplitplugin")


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    """Apply grouped least-duration splitting."""
    algo = config.getoption("splitting_algorithm", default=None)
    splits = config.getoption("splits", default=None)
    group = config.getoption("group", default=None)

    if algo != ALGORITHM_NAME or splits is None or group is None:
        return

    from execution_testing.pytest_plugins.split.grouped_least_duration import (
        grouped_least_duration,
    )

    durations_path = Path(config.getoption("durations_path"))
    try:
        durations = json.loads(durations_path.read_text())
    except FileNotFoundError:
        durations = {}

    all_groups = grouped_least_duration(
        splits=splits, items=items, durations=durations
    )
    split = all_groups[group - 1]  # group is 1-indexed

    items[:] = split.selected
    config.hook.pytest_deselected(items=split.deselected)
