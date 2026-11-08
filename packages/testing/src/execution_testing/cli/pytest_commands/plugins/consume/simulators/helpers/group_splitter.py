"""
Split oversized pre-alloc groups so that xdist can spread them out.

`consume enginex` pins every test of a pre-alloc group to a single xdist
worker (via `--dist loadgroup`) so that the whole group can share one
client container. That makes a group indivisible. When one group holds a
large share of the selected tests, as a single fork's tests do under
`--sim.limit`, the run cannot finish before that group does, and the
other workers idle out the tail.

Splitting an oversized group into sub-groups lifts that ceiling. Every
sub-group starts its own client from the *same* genesis (the pre-alloc
hash is untouched, only the group identifier gains a suffix), and each
test already runs from that genesis, so per-test isolation is unchanged.
The only cost is one extra client start per additional sub-group.

The genesis itself cannot be split: its hash and the state root of every
block in the group's fixtures commit to the full pre-alloc.
"""

import logging
import os
from math import ceil
from pathlib import Path

import pytest

from execution_testing.fixtures.consume import TestCaseIndexFile

from .test_tracker import xdist_group_of

logger = logging.getLogger(__name__)

# Sub-groups to aim for per worker when sizing the cap. Two gives the
# scheduler slack to even out the tail of a run without splitting groups so
# finely that client starts dominate.
SUB_GROUPS_PER_WORKER = 2

# Groups at or below this many tests are never split: on a small selection
# an extra client start costs more than the scheduling gain.
MIN_SPLITTABLE_GROUP_SIZE = 1000


def max_group_size(total_tests: int, worker_count: int) -> int:
    """
    Return the most tests a (sub-)group may hold.

    Cap each group at about half a worker's fair share of the selected
    tests, `total / (2 * workers)`, so that only a group large enough to
    hold up the end of the run is split, but never below
    `MIN_SPLITTABLE_GROUP_SIZE`.
    """
    return max(
        MIN_SPLITTABLE_GROUP_SIZE,
        ceil(total_tests / (SUB_GROUPS_PER_WORKER * worker_count)),
    )


def plan_sub_group_counts(
    group_sizes: dict[str, int], max_size: int
) -> dict[str, int]:
    """
    Return the number of sub-groups to split each oversized group into.

    A group larger than `max_size` tests is split into the fewest balanced
    pieces that each fit within it; groups already within it are omitted
    from the result and left untouched.
    """
    return {
        group_identifier: ceil(size / max_size)
        for group_identifier, size in group_sizes.items()
        if size > max_size
    }


def sub_group_indices(files: list[str], sub_group_count: int) -> list[int]:
    """
    Return the sub-group of each test of a group sorted by `files`.

    Cut the group into `sub_group_count` balanced pieces, but move each
    cut back to the start of the file it falls in, so that a fixture
    file never spans two sub-groups and its worker loads it once. A
    test without a file (`""`, read from stdin) has nothing to keep
    together and is cut where it falls. Whole files make the pieces
    uneven by at most a file each, and a file larger than a piece
    leaves the pieces whose cut falls inside it empty.
    """
    file_starts: dict[str, int] = {}
    indices = []
    for index, file in enumerate(files):
        start = file_starts.setdefault(file, index) if file else index
        indices.append(start * sub_group_count // len(files))
    return indices


def xdist_worker_count() -> int:
    """
    Return the number of xdist workers, or zero if not running under xdist.

    Read from the environment rather than from `--numprocesses`, which
    xdist clears in worker processes (`xdist.remote.setup_config`). The
    distinction matters because it is the workers, not the controller,
    that collect and group the tests.
    """
    try:
        return int(os.environ.get("PYTEST_XDIST_WORKER_COUNT", "0"))
    except ValueError:
        return 0


def _split_order_key(item: pytest.Item) -> tuple[str, str]:
    """
    Return the key that orders a group's tests before it is cut.

    Order by fixture file first, the order the group's tests run in, so
    that `sub_group_indices` can cut the group along whole files and the
    worker's fixture file cache loads a file once. Break ties by node
    ID: every worker collects and splits on its own, and they must all
    arrive at the same partition, otherwise xdist rejects the run for
    having collected differing tests.
    """
    callspec = getattr(item, "callspec", None)
    test_case = callspec.params.get("test_case") if callspec else None
    path = (
        Path(test_case.json_path).as_posix()
        if isinstance(test_case, TestCaseIndexFile)
        else ""
    )
    return (path, item.nodeid)


def split_oversized_groups(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """
    Reassign the tests of oversized pre-alloc groups to sub-groups.

    Do nothing unless the run is distributed with group-aware scheduling
    over at least two workers, the only case that has anything to gain.
    Size the cap against `items`, the tests left after deselection, so
    that a `--sim.limit` selection is split by its own group sizes.

    A simulator calls this first in its `pytest_collection_modifyitems`:
    before counting tests per group, which must see the sub-groups, and
    before deriving anything keyed by node ID, because a split test's
    node ID gains the sub-group suffix.
    """
    worker_count = xdist_worker_count()
    if worker_count < 2 or not config.getoption("loadgroup", default=False):
        return

    groups: dict[str, list[pytest.Item]] = {}
    for item in items:
        group_identifier = xdist_group_of(item)
        if group_identifier is not None:
            groups.setdefault(group_identifier, []).append(item)

    max_size = max_group_size(
        sum(len(group) for group in groups.values()), worker_count
    )
    sub_group_counts = plan_sub_group_counts(
        {identifier: len(group) for identifier, group in groups.items()},
        max_size,
    )
    sub_groups = 0
    for group_identifier, sub_group_count in sub_group_counts.items():
        group = sorted(groups[group_identifier], key=_split_order_key)
        indices = sub_group_indices(
            [_split_order_key(item)[0] for item in group], sub_group_count
        )
        for item, sub_group_index in zip(group, indices, strict=True):
            _assign_sub_group(item, group_identifier, sub_group_index)
        sub_groups += len(set(indices))

    logger.info(
        f"Pre-alloc group cap {max_size} tests across {worker_count} "
        f"workers: split {len(sub_group_counts)} group(s) into "
        f"{sub_groups} sub-groups"
    )


def _assign_sub_group(
    item: pytest.Item, group_identifier: str, sub_group_index: int
) -> None:
    """
    Move a test into one sub-group of its pre-alloc group.

    Two consumers have to agree on the new identifier:

    - xdist, which schedules by the group name that it appends to the
      node ID as an `@` suffix. It appends that suffix from its own
      `pytest_collection_modifyitems`, which runs before this plugin's
      `trylast` hook, so rewriting the marker no longer reaches the
      scheduler and the suffix has to be extended in place.
    - this plugin, which reads the marker to key the client and to count
      how many tests it must run before it can be stopped.

    Extending the suffix rather than rewriting it keeps this independent
    of what other plugins do to a node ID in between (`fix_package_test
    _path`, for one, trims its last character) and only relies on the
    suffix still being the last `@`-delimited segment, which is how xdist
    recovers the group it scheduled by. Hive names a test after
    `item.name`, so the reported test names do not change.
    """
    sub_group_identifier = f"{group_identifier}#{sub_group_index}"
    assert item.nodeid.rfind("@") > item.nodeid.rfind("]"), (
        f"expected xdist to have suffixed the node ID of {item.nodeid} "
        f"with its pre-alloc group '{group_identifier}'"
    )
    item.own_markers = [
        marker for marker in item.own_markers if marker.name != "xdist_group"
    ]
    item.add_marker(pytest.mark.xdist_group(name=sub_group_identifier))
    item._nodeid = f"{item.nodeid}#{sub_group_index}"
