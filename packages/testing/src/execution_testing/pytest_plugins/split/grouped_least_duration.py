"""
Grouped least-duration splitting algorithm for pytest-split.

Groups tests by ``(function, fork)`` so that all parametrizations sharing an
EVM execution cache and output fixture file land on the same runner, then
applies greedy least-duration bin-packing at the group level.
"""

from __future__ import annotations

import heapq
from collections import OrderedDict
from collections.abc import Sequence
from typing import NamedTuple, Protocol, runtime_checkable


@runtime_checkable
class HasNodeId(Protocol):
    """Object with a ``nodeid`` attribute (pytest Item or test stub)."""

    @property
    def nodeid(self) -> str:
        """Return the test node identifier."""
        ...


class SplitGroup(NamedTuple):
    """One runner's workload after splitting."""

    selected: list[HasNodeId]
    deselected: list[HasNodeId]
    duration: float
    max_group_duration: float


def strip_xdist_suffix(nodeid: str) -> str:
    """Strip the ``@xdist_group`` suffix from a nodeid."""
    return nodeid.split("@")[0]


def normalize_durations(
    raw: dict[str, float],
) -> dict[str, float]:
    """
    Strip ``@xdist_group`` suffixes from duration keys.

    ``--store-durations`` records nodeids with ``@t8n-cache-*`` suffixes
    added by xdist during execution, but ``item.nodeid`` during
    collection does not include them.
    """
    return {strip_xdist_suffix(k): v for k, v in raw.items()}


# Fixture format tokens that appear as parameters in test nodeids.
# These are stripped from the grouping key so that format variants
# of the same test case form a single group.
FIXTURE_FORMATS = frozenset(
    {
        "state_test",
        "blockchain_test",
        "blockchain_test_from_state_test",
        "blockchain_test_engine",
        "blockchain_test_engine_from_state_test",
        "blockchain_test_engine_x",
        "blockchain_test_engine_x_from_state_test",
    }
)


def grouping_key(nodeid: str) -> str:
    """
    Extract the ``(test_case, fork)`` grouping key from a nodeid.

    Strip the ``@xdist_group`` suffix and the fixture format token,
    keeping the function path, fork, and all other parameters.
    Format variants of the same test case share t8n cache entries
    and must land on the same runner.

    Unparametrized nodeids (no ``[``) are their own singleton group.
    """
    base_nid = strip_xdist_suffix(nodeid)
    if "[" not in base_nid:
        return base_nid
    base, params_bracket = base_nid.split("[", 1)
    params = params_bracket.rstrip("]")
    tokens = params.split("-")
    filtered = [t for t in tokens if t not in FIXTURE_FORMATS]
    return f"{base}[{'-'.join(filtered)}]"


def grouped_least_duration(
    splits: int,
    items: Sequence[HasNodeId],
    durations: dict[str, float],
    workers_per_runner: int = 1,
) -> list[SplitGroup]:
    """
    Split *items* into *splits* groups using grouped least-duration
    bin-packing.

    1. Group items by ``grouping_key(item.nodeid)``.
    2. Compute per-group duration from *durations* (average for unknowns).
    3. Assign groups heaviest-first to the runner with the smallest
       estimated wall time.
    4. Return one ``SplitGroup`` per runner.

    When *workers_per_runner* > 1, the heap key is the estimated wall
    time ``max(total / workers, max_group_dur)`` instead of just the
    serial total.  A secondary key on serial total fills free capacity
    on runners whose wall time is dominated by a single heavy group.
    """
    # --- 1. Build ordered groups (preserving collection order) ---
    groups: OrderedDict[str, list[HasNodeId]] = OrderedDict()
    for item in items:
        key = grouping_key(item.nodeid)
        groups.setdefault(key, []).append(item)

    # --- 2. Compute per-group duration ---
    # Normalize nodeids: item.nodeid may or may not have @xdist_group
    # suffixes depending on whether xdist is active during collection.
    relevant: dict[str, float] = {}
    for item in items:
        nid = strip_xdist_suffix(item.nodeid)
        if nid in durations:
            relevant[nid] = durations[nid]
    avg_duration = sum(relevant.values()) / len(relevant) if relevant else 1.0

    group_durations: dict[str, float] = {}
    for key, group_items in groups.items():
        group_durations[key] = sum(
            relevant.get(strip_xdist_suffix(item.nodeid), avg_duration)
            for item in group_items
        )

    # --- 3. Greedy bin-packing (heaviest first) ---
    sorted_keys = sorted(
        groups, key=lambda k: group_durations[k], reverse=True
    )

    runner_keys: list[list[str]] = [[] for _ in range(splits)]
    runner_totals: list[float] = [0.0] * splits
    runner_max_group: list[float] = [0.0] * splits
    w = max(workers_per_runner, 1)

    # Heap of (wall_time, total_duration, runner_index).
    # wall_time = max(total/workers, max_group_dur) when workers > 1,
    # otherwise just the serial total.  The secondary total_duration
    # key ensures runners with equal wall time but more free capacity
    # (lower serial total) are preferred.
    heap: list[tuple[float, float, int]] = [
        (0.0, 0.0, i) for i in range(splits)
    ]
    heapq.heapify(heap)

    for key in sorted_keys:
        _, total, idx = heapq.heappop(heap)
        runner_keys[idx].append(key)
        new_total = total + group_durations[key]
        runner_totals[idx] = new_total
        new_max = max(runner_max_group[idx], group_durations[key])
        runner_max_group[idx] = new_max
        if w > 1:
            wall = max(new_total / w, new_max)
        else:
            wall = new_total
        heapq.heappush(heap, (wall, new_total, idx))

    # --- 4. Expand to SplitGroup objects ---
    # Groups within each runner are in heaviest-first assignment order.
    # Items within each group are in original collection order, keeping
    # format parametrizations adjacent for t8n cache efficiency.
    result: list[SplitGroup] = []
    for i in range(splits):
        selected = [item for key in runner_keys[i] for item in groups[key]]
        selected_ids = set(id(item) for item in selected)
        deselected = [item for item in items if id(item) not in selected_ids]
        result.append(
            SplitGroup(
                selected=selected,
                deselected=deselected,
                duration=runner_totals[i],
                max_group_duration=runner_max_group[i],
            )
        )

    return result
