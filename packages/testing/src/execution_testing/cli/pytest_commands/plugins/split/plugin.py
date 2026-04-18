"""
Pytest plugin for grouped test splitting.

When ``--grouped-split`` is passed alongside pytest-split's ``--splits``
and ``--group``, the plugin unregisters pytest-split's default splitter
and partitions items by ``(test_function_path, fork)`` — every
parametrization of one test function under one fork stays on the same
runner.

That invariant is what fill's native output layout relies on: each
per-test-function fixture file lives under a per-fork subdirectory, so
every output file is written by exactly one runner. CI fan-in can then
copy per-runner fixture dirs together without content collisions and
without needing ``--single-fixture-per-file``.
"""

from __future__ import annotations

import sys
from collections.abc import Generator
from pathlib import Path
from typing import Any, cast

import pytest
from _pytest.config import Config
from _pytest.nodes import Item
from _pytest.terminal import TerminalReporter

from execution_testing.cli.pytest_commands.plugins.split.durations import (
    load_durations,
    normalize_durations,
    strip_xdist_suffix,
)
from execution_testing.cli.pytest_commands.plugins.split.grouping import (
    group_key,
)
from execution_testing.cli.pytest_commands.plugins.split.scheduling import (
    assign_runners,
)

_SUMMARY_KEY = pytest.StashKey[list[str]]()
_SPLIT_PLUGIN_NAME = "pytestsplitplugin"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the ``--grouped-split`` flag."""
    parser.getgroup("split").addoption(
        "--grouped-split",
        dest="grouped_split",
        action="store_true",
        default=False,
        help=(
            "Replace pytest-split's default splitting with an"
            " xdist_group-aware algorithm that keeps cache-sharing"
            " items on the same runner. Requires --splits and"
            " --group."
        ),
    )


def _grouped_split_active(config: Config) -> bool:
    """Return True when grouped splitting should replace pytest-split."""
    if not config.getoption("grouped_split", default=False):
        return False
    splits = config.getoption("splits", default=None)
    group = config.getoption("group", default=None)
    return bool(splits and group)


def _classify_mode(
    *,
    durations_loaded: int,
    items: int,
    matched: int,
    durations_path: Path,
) -> str:
    """
    Return a human-readable one-line mode label for the summary.

    Distinguishes the three situations operators care about:

    - ``average-only (no durations file)``: the configured path does
      not exist or is empty. First run, or artifact not downloaded.
    - ``average-only (... loaded, 0/N match — KEY MISMATCH)``: the
      file was found but none of its keys line up with the collected
      nodeids. This is the silent-fallback regression; bin-packing
      is effectively random.
    - ``duration-aware (matched/total ...)``: at least some items
      have real durations; bin-packing is doing its job.
    """
    if durations_loaded == 0:
        return f"average-only (no durations at {durations_path})"
    if matched == 0:
        return (
            f"average-only ({durations_loaded} durations loaded from"
            f" {durations_path}, 0/{items} match — KEY MISMATCH)"
        )
    pct = 100.0 * matched / items if items else 0.0
    suffix = "" if matched == items else f", {items - matched} use avg"
    return f"duration-aware ({matched}/{items} matched, {pct:.0f}%{suffix})"


def pytest_configure(config: Config) -> None:
    """Unregister pytest-split's splitter when grouped mode is active."""
    if not _grouped_split_active(config):
        return
    plugin = config.pluginmanager.get_plugin(_SPLIT_PLUGIN_NAME)
    if plugin is not None:
        config.pluginmanager.unregister(plugin, _SPLIT_PLUGIN_NAME)


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    """Partition *items* across runners via grouped least-duration."""
    if not _grouped_split_active(config):
        return

    splits: int = config.getoption("splits")
    group: int = config.getoption("group")
    durations_path = Path(config.getoption("durations_path"))
    raw_durations = load_durations(durations_path)
    durations = normalize_durations(raw_durations)

    keyed_items = [(group_key(item), item) for item in items]
    all_groups = assign_runners(
        splits=splits, keyed_items=keyed_items, durations=durations
    )
    selected = all_groups[group - 1]  # pytest-split's --group is 1-indexed

    matched = sum(
        1 for item in items if strip_xdist_suffix(item.nodeid) in durations
    )
    unmatched = len(items) - matched
    unique_groups = len({key for key, _ in keyed_items})
    mode = _classify_mode(
        durations_loaded=len(durations),
        items=len(items),
        matched=matched,
        durations_path=durations_path,
    )
    # Emit a GitHub Actions ``::warning::`` annotation on the exact
    # regression mode we care about in CI: durations file loaded but
    # zero items match (bin-packing silently falls back to average).
    # Prefix must start the line for Actions to pick it up. Under
    # xdist, ``pytest_collection_modifyitems`` runs on every worker;
    # emit only from ``gw0`` (or the non-xdist controller) to avoid N
    # duplicate warnings.
    worker_id = getattr(config, "workerinput", {}).get("workerid", "master")
    if worker_id in ("master", "gw0") and len(durations) > 0 and matched == 0:
        print(
            "::warning title=grouped-split durations mismatch::"
            f" loaded {len(durations)} durations from {durations_path}"
            f" but 0/{len(items)} collected items match; bin-packing"
            " fell back to average (splits will be imbalanced).",
            file=sys.stderr,
            flush=True,
        )
    summary = [
        f"mode: {mode}",
        (
            f"runner {group}/{splits}:"
            f" selected {len(selected.selected)}/{len(items)} items,"
            f" est serial {selected.duration:.0f}s"
            f" (heaviest group {selected.max_group_duration:.0f}s)"
        ),
        (
            f"grouping: {unique_groups} (function, fork) keys,"
            f" duration coverage {matched}/{len(items)}"
            + (f" ({unmatched} unknown -> avg)" if unmatched else "")
        ),
        "all runners (selected / serial-s / heaviest-s):",
    ]
    for i, g in enumerate(all_groups, 1):
        marker = ">>>" if i == group else "   "
        summary.append(
            f"  {marker} {i:2d}: {len(g.selected):6d} items,"
            f" {g.duration:>7.0f}s, {g.max_group_duration:>7.0f}s"
        )
    config.stash[_SUMMARY_KEY] = summary

    items[:] = cast(list[Item], selected.selected)
    config.hook.pytest_deselected(items=selected.deselected)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session) -> None:
    """
    On an xdist worker, forward the summary to the controller via
    ``workeroutput`` so :func:`pytest_terminal_summary` (which runs on
    the controller) can find it. No-op on the controller and under
    non-xdist runs.
    """
    config = session.config
    if not hasattr(config, "workerinput"):
        return
    summary = config.stash.get(_SUMMARY_KEY, [])
    if summary and hasattr(config, "workeroutput"):
        config.workeroutput["grouped_split_summary"] = summary


def pytest_testnodedown(node: Any) -> None:
    """
    On the controller, accept the first worker's summary as the
    canonical one. Every worker produced the same summary (they all
    run the same grouping over the same items), so first-wins is
    safe.
    """
    if node.config.stash.get(_SUMMARY_KEY, None) is not None:
        return
    worker_output = getattr(node, "workeroutput", None)
    if worker_output is None:
        return
    summary = worker_output.get("grouped_split_summary")
    if summary:
        node.config.stash[_SUMMARY_KEY] = summary


@pytest.hookimpl(hookwrapper=True, trylast=True)
def pytest_terminal_summary(
    terminalreporter: TerminalReporter, config: Config
) -> Generator[None, None, None]:
    """Print the grouped-split summary after the normal terminal output."""
    yield
    summary = config.stash.get(_SUMMARY_KEY, [])
    if not summary:
        return
    terminalreporter.write_sep("=", "grouped-split", bold=True)
    for line in summary:
        terminalreporter.line(line)
