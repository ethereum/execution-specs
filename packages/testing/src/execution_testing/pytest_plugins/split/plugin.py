"""
Pytest plugin for grouped test splitting.

When ``--grouped-split`` is passed alongside ``--splits`` and ``--group``,
replaces pytest-split's built-in splitting with a ``(function, fork)``-
aware algorithm that keeps cache-sharing parametrizations on the same
runner.

Registered via ``-p`` in ``pytest-fill.ini``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.nodes import Item


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the ``--grouped-split`` flag."""
    parser.getgroup("split").addoption(
        "--grouped-split",
        dest="grouped_split",
        action="store_true",
        default=False,
        help=(
            "Use grouped least-duration splitting"
            " (requires --splits and --group)."
        ),
    )


def pytest_configure(config: Config) -> None:
    """Unregister pytest-split's plugin when using grouped splitting."""
    if not config.getoption("grouped_split", default=False):
        return
    splits = config.getoption("splits", default=None)
    group = config.getoption("group", default=None)
    if splits and group:
        plugin = config.pluginmanager.get_plugin("pytestsplitplugin")
        if plugin is not None:
            config.pluginmanager.unregister(plugin, "pytestsplitplugin")


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    """Apply grouped least-duration splitting."""
    if not config.getoption("grouped_split", default=False):
        return
    splits = config.getoption("splits", default=None)
    group = config.getoption("group", default=None)
    if splits is None or group is None:
        return

    from execution_testing.pytest_plugins.split.grouped_least_duration import (
        grouped_least_duration,
        normalize_durations,
    )

    durations_path = Path(config.getoption("durations_path"))
    try:
        raw = json.loads(durations_path.read_text())
    except FileNotFoundError:
        raw = {}
    durations = normalize_durations(raw)

    all_groups = grouped_least_duration(
        splits=splits, items=items, durations=durations
    )
    split = all_groups[group - 1]  # group is 1-indexed

    items[:] = split.selected
    config.hook.pytest_deselected(items=split.deselected)
