"""
Scheduling for ``--grouped-split``: bin-pack grouped items across runners.

This module combines three concerns that together implement the
``--grouped-split`` flag:

1. **Grouping invariant** (correctness). Items sharing a group key
   always land on the same runner. The caller supplies the key via
   the ``(key, item)`` pairs in *keyed_items*; this module only
   enforces the "same key, same runner" rule. Fan-in safety for
   per-group output files (e.g. fill's per-``(fork, function)``
   fixture files) depends on this invariant alone.

2. **LPT runner scheduling** (CI-wallclock performance). Given the
   grouping constraint, groups are assigned *heaviest-first* to the
   *least-loaded* runner via a min-heap -- Longest-Processing-Time-
   first, the standard 4/3-approximation for makespan minimization
   on identical machines. This balances total wallclock across CI
   runners.

3. **Intra-group item ordering** (worker-straggler prevention).
   Within each group, items are sorted by individual duration DESC
   before being handed back to pytest. Under xdist's default scheduler
   settings (``--dist=load`` or ``--dist=loadgroup`` without
   ``--loadscopereorder``) this order is preserved all the way to
   worker dispatch, so slow tests start first and don't become
   trailing stragglers on a runner's ``-n N`` worker pool. Disable
   via ``assign_runners(..., sort_intra_group=False)``.

Duration data is optional. Unknown items fall back to the mean of
known items (or ``1.0`` if none are known), so when ``.test_durations``
is absent the scheduler degrades gracefully.

Public API:

- :func:`build_group_durations` -- items to groups + per-group totals.
- :func:`sort_items_within_groups` -- sort each group slowest-first.
- :func:`lpt_schedule` -- group durations to runner assignments.
- :func:`assign_runners` -- end-to-end: items to :class:`SplitGroup`s.
"""

from __future__ import annotations

import heapq
from collections import OrderedDict
from collections.abc import Callable, Iterable, Sequence
from typing import NamedTuple, Protocol, TypeVar, runtime_checkable

from execution_testing.cli.pytest_commands.plugins.split.durations import (
    strip_xdist_suffix,
)


@runtime_checkable
class _HasNodeId(Protocol):
    """Minimal protocol for items with a ``nodeid`` attribute."""

    @property
    def nodeid(self) -> str:
        """Return the pytest node identifier."""
        ...


_ItemT = TypeVar("_ItemT", bound=_HasNodeId)


class SplitGroup(NamedTuple):
    """One runner's workload after splitting."""

    selected: list[_HasNodeId]
    deselected: list[_HasNodeId]
    duration: float
    max_group_duration: float


def _item_weight(
    items: Iterable[_HasNodeId],
    durations: dict[str, float],
) -> Callable[[_HasNodeId], float]:
    """
    Return an ``item -> estimated duration`` function.

    Per-item duration is looked up by bare nodeid (after stripping
    any ``@t8n-cache-*`` suffix); unknown items inherit the mean of
    known items, or ``1.0`` when no durations are known. The caller
    passes the set of items in-scope so the average is computed over
    that scope.
    """
    known: dict[str, float] = {}
    for item in items:
        nid = strip_xdist_suffix(item.nodeid)
        if nid in durations:
            known[nid] = durations[nid]
    avg = sum(known.values()) / len(known) if known else 1.0

    def weight(item: _HasNodeId) -> float:
        return known.get(strip_xdist_suffix(item.nodeid), avg)

    return weight


def build_group_durations(
    keyed_items: Sequence[tuple[str, _HasNodeId]],
    durations: dict[str, float],
) -> tuple[OrderedDict[str, list[_HasNodeId]], dict[str, float]]:
    """
    Group *keyed_items* by key and compute each group's total duration.

    Items sharing a key are collected in collection order under that
    key. See :func:`_item_weight` for the per-item duration lookup
    and fallback rule.

    Returns ``(groups, group_durations)``:

    - ``groups[key]`` -- the items under *key* in collection order.
    - ``group_durations[key]`` -- the sum of per-item durations.
    """
    groups: OrderedDict[str, list[_HasNodeId]] = OrderedDict()
    for key, item in keyed_items:
        groups.setdefault(key, []).append(item)

    weight = _item_weight((item for _, item in keyed_items), durations)
    group_durations = {
        key: sum(weight(item) for item in members)
        for key, members in groups.items()
    }
    return groups, group_durations


def sort_items_within_groups(
    groups: OrderedDict[str, list[_ItemT]],
    durations: dict[str, float],
) -> OrderedDict[str, list[_ItemT]]:
    """
    Return *groups* with each member list sorted slowest-first.

    Group order (keys) is preserved; only the items inside each
    group are reordered by individual duration DESC. Sort is stable,
    so items with identical durations keep their collection order.

    Used by :func:`assign_runners` so that xdist workers receive slow
    tests first within each scope, reducing end-of-run stragglers.
    See :func:`_item_weight` for the duration lookup.
    """
    all_items = (item for members in groups.values() for item in members)
    weight = _item_weight(all_items, durations)
    return OrderedDict(
        (key, sorted(members, key=weight, reverse=True))
        for key, members in groups.items()
    )


def lpt_schedule(
    group_durations: dict[str, float],
    splits: int,
) -> tuple[list[list[str]], list[float], list[float]]:
    """
    Assign groups to *splits* runners via Longest-Processing-Time-first.

    Groups are sorted heaviest-first and each is placed on the runner
    with the smallest current total (tie-broken by runner index via
    heap insertion order). The result is a 4/3-approximation of the
    optimal makespan; exact optimization is NP-hard.

    Returns three parallel lists of length *splits*:

    - ``runner_keys[i]`` -- group keys assigned to runner *i*, in
      placement order (heaviest-first globally).
    - ``runner_totals[i]`` -- total duration on runner *i*.
    - ``runner_max_group[i]`` -- duration of the largest single group
      on runner *i* (a per-runner wallclock lower bound).
    """
    sorted_keys = sorted(
        group_durations, key=lambda k: group_durations[k], reverse=True
    )
    runner_keys: list[list[str]] = [[] for _ in range(splits)]
    runner_totals = [0.0] * splits
    runner_max_group = [0.0] * splits

    heap: list[tuple[float, int]] = [(0.0, i) for i in range(splits)]
    heapq.heapify(heap)
    for key in sorted_keys:
        total, idx = heapq.heappop(heap)
        new_total = total + group_durations[key]
        runner_keys[idx].append(key)
        runner_totals[idx] = new_total
        runner_max_group[idx] = max(
            runner_max_group[idx], group_durations[key]
        )
        heapq.heappush(heap, (new_total, idx))

    return runner_keys, runner_totals, runner_max_group


def assign_runners(
    splits: int,
    keyed_items: Sequence[tuple[str, _HasNodeId]],
    durations: dict[str, float],
    sort_intra_group: bool = True,
) -> list[SplitGroup]:
    """
    Split *keyed_items* across *splits* runners by group key.

    Composes :func:`build_group_durations`, optionally
    :func:`sort_items_within_groups`, and :func:`lpt_schedule`, then
    expands each runner's assigned keys back into the original item
    objects. Group contiguity is preserved so that t8n-cache hits
    stay adjacent under ``--dist loadgroup``.

    Items sharing a key always land on the same runner; groups are
    distributed heaviest-first to the least-loaded runner (see
    :func:`lpt_schedule`). With *sort_intra_group* true (default),
    items within each group are ordered slowest-first so xdist
    workers start on the longest tests first.
    """
    groups, group_durations = build_group_durations(keyed_items, durations)
    if sort_intra_group:
        groups = sort_items_within_groups(groups, durations)
    runner_keys, runner_totals, runner_max_group = lpt_schedule(
        group_durations, splits
    )

    result: list[SplitGroup] = []
    for i in range(splits):
        selected = [item for key in runner_keys[i] for item in groups[key]]
        selected_ids = {id(item) for item in selected}
        deselected = [
            item for _, item in keyed_items if id(item) not in selected_ids
        ]
        result.append(
            SplitGroup(
                selected=selected,
                deselected=deselected,
                duration=runner_totals[i],
                max_group_duration=runner_max_group[i],
            )
        )
    return result
