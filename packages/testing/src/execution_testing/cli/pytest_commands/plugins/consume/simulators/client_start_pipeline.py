"""
Start the next client while the current one runs its tests.

A worker starts the client of the next group queued to it as soon as
its current group's client is ready, so the next group's tests find
their client running instead of waiting for it to boot. A worker starts
at most one client ahead. On by default; `--no-pipeline-client-start`
turns it off.

xdist's `loadgroup` scheduler hands a worker its next group only when
the worker has two or fewer tests left, and most groups have one or two
tests, so the next group is rarely known in time. The
`GroupLookaheadScheduling` scheduler keeps one more group queued per
worker.
"""

import argparse
from typing import TYPE_CHECKING

import pytest
from xdist.scheduler import LoadGroupScheduling

from .helpers.test_tracker import xdist_group_of

if TYPE_CHECKING:
    from xdist.remote import Producer
    from xdist.workermanage import WorkerController


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add the client start pipelining option."""
    consume_group = parser.getgroup(
        "consume", "Arguments related to consuming fixtures via a client"
    )
    consume_group.addoption(
        "--pipeline-client-start",
        action=argparse.BooleanOptionalAction,
        dest="pipeline_client_start",
        default=True,
        help=(
            "Start the client of the next group queued to a worker while "
            "the current group's tests run, hiding the client's start "
            "time. Holds at most one extra client per worker. On by "
            "default."
        ),
    )


LOOKAHEAD_TESTS = 100
"""
Most tests a worker may have left in its current group when it is handed
its next one.

Enough for a group's last tests to cover a slow client's start, while a
long group cannot hold another group back from idle workers for long.
"""


def pipeline_client_start(config: pytest.Config) -> bool:
    """Return whether client start pipelining is on."""
    return bool(config.getoption("pipeline_client_start", False))


class GroupLookaheadScheduling(LoadGroupScheduling):
    """
    Keep each worker's next group queued alongside its current one.

    The next group is handed out once the current one has at most
    `LOOKAHEAD_TESTS` tests left. Groups still run whole on one worker;
    only the moment a group is handed out changes.
    """

    def _reschedule(self, node: "WorkerController") -> None:
        """Hand `node` its next group once its current one nears its end."""
        workload = self.assigned_work[node]
        unfinished = sum(not all(unit.values()) for unit in workload.values())
        if (
            not node.shutting_down
            and self.workqueue
            and unfinished < 2
            and self._pending_of(workload) <= LOOKAHEAD_TESTS
        ):
            self._assign_work_unit(node)
        else:
            super()._reschedule(node)


@pytest.hookimpl(optionalhook=True, tryfirst=True)
def pytest_xdist_make_scheduler(
    config: pytest.Config, log: "Producer"
) -> LoadGroupScheduling | None:
    """Use `GroupLookaheadScheduling` while pipelining client starts."""
    if not pipeline_client_start(config):
        return None
    if config.getvalue("dist") != "loadgroup":
        return None
    return GroupLookaheadScheduling(config, log)


def queued_items(item: pytest.Item) -> list[pytest.Item]:
    """
    Return the items this process will run after `item`, in order.

    Under xdist, these are the items already sent to this worker: the
    next item, which xdist takes off its queue before running `item`,
    then the rest of the queue. Without xdist, every later item.
    """
    items = item.session.items
    if not hasattr(item.config, "workerinput"):
        return items[items.index(item) + 1 :]
    # xdist runs its worker module as `__channelexec__`, not as
    # `xdist.remote`, so the worker's plugin is found by its queue.
    interactor = next(
        (
            plugin
            for plugin in item.config.pluginmanager.get_plugins()
            if hasattr(plugin, "torun") and hasattr(plugin, "nextitem_index")
        ),
        None,
    )
    if interactor is None:
        return []
    with interactor.torun.lock() as queue:
        indices = [interactor.nextitem_index, *queue]
    return [items[index] for index in indices if isinstance(index, int)]


def next_group_item(
    queued: list[pytest.Item], current_group: str
) -> pytest.Item | None:
    """
    Return the first queued item of a group other than `current_group`.

    A worker is sent whole groups, in order, so another group is queued
    only if the last queued item belongs to one; checking it first keeps
    a long group from scanning its own remaining tests on every test.
    """
    if not queued or xdist_group_of(queued[-1]) == current_group:
        return None
    return next(
        (item for item in queued if xdist_group_of(item) != current_group),
        None,
    )
