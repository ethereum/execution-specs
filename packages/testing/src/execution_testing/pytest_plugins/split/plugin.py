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
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.nodes import Item
    from _pytest.terminal import TerminalReporter

_SPLIT_SUMMARY_KEY = pytest.StashKey[list[str]]()


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
        strip_xdist_suffix,
    )

    durations_path = Path(config.getoption("durations_path"))
    try:
        raw = json.loads(durations_path.read_text())
    except FileNotFoundError:
        raw = {}
    durations = normalize_durations(raw)

    matched = sum(
        1 for item in items if strip_xdist_suffix(item.nodeid) in durations
    )
    unmatched = len(items) - matched

    all_groups = grouped_least_duration(
        splits=splits, items=items, durations=durations
    )
    split = all_groups[group - 1]  # group is 1-indexed

    summary = [
        f"Duration coverage:"
        f" {matched}/{len(items)} matched"
        f" ({unmatched} unknown, using average)",
    ]
    if 0 < unmatched <= 50:
        for item in items:
            nid = strip_xdist_suffix(item.nodeid)
            if nid not in durations:
                summary.append(f"  Unknown: {nid}")
    elif unmatched > 50:
        count = 0
        for item in items:
            nid = strip_xdist_suffix(item.nodeid)
            if nid not in durations:
                summary.append(f"  Unknown: {nid}")
                count += 1
                if count >= 50:
                    summary.append(f"  ... and {unmatched - 50} more")
                    break
    summary.append(
        f"Runner {group}/{splits}:"
        f" {len(split.selected)} items,"
        f" estimated {split.duration:.1f}s"
    )
    config.stash[_SPLIT_SUMMARY_KEY] = summary

    items[:] = split.selected
    config.hook.pytest_deselected(items=split.deselected)


def pytest_testnodedown(node: Any) -> None:
    """Transfer split summary from first worker to controller."""
    summary = node.config.stash.get(_SPLIT_SUMMARY_KEY, None)
    if summary is None:
        worker_summary = (
            node.workeroutput.get("grouped_split_summary")
            if hasattr(node, "workeroutput")
            else None
        )
        if worker_summary:
            node.config.stash[_SPLIT_SUMMARY_KEY] = worker_summary


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session) -> None:
    """Send split summary to controller via workeroutput."""
    if not hasattr(session.config, "workerinput"):
        return
    summary = session.config.stash.get(_SPLIT_SUMMARY_KEY, [])
    if summary and hasattr(session.config, "workeroutput"):
        session.config.workeroutput["grouped_split_summary"] = summary


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_terminal_summary(
    terminalreporter: TerminalReporter,
    config: Config,
) -> Generator:
    """Print grouped-split summary at session end."""
    yield
    summary = config.stash.get(_SPLIT_SUMMARY_KEY, [])
    if not summary:
        return
    terminalreporter.write_sep(
        "=",
        " grouped-split",
        bold=True,
    )
    for line in summary:
        terminalreporter.line(line)
