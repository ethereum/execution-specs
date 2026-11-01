"""Tests for starting the next group's client ahead of its tests."""

import threading
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any, Iterator, List, cast

import pytest
from hive.client import Client

from ..simulators.client_start_pipeline import (
    LOOKAHEAD_TESTS,
    GroupLookaheadScheduling,
    next_group_item,
    queued_items,
)
from ..simulators.helpers.test_tracker import PreAllocGroupTestTracker
from ..simulators.multi_test_client import MultiTestClientManager


class _StubClient:
    """A client that only remembers whether it was stopped."""

    def __init__(self, name: str = "stub") -> None:
        self.id = name
        self.stopped = False

    def stop(self) -> None:
        """Record the stop."""
        self.stopped = True


def _manager(counts: dict[str, int]) -> MultiTestClientManager:
    """Return a manager expecting `counts` tests per group."""
    manager = MultiTestClientManager()
    tracker = PreAllocGroupTestTracker()
    for group, count in counts.items():
        tracker.set_group_test_count(group, count)
    manager.set_test_tracker(tracker)
    return manager


class TestStartAhead:
    """A client started ahead is claimed by its group's first test."""

    def test_the_first_test_waits_for_and_claims_the_client(self) -> None:
        """
        `get_client` blocks until the start finishes, then registers the
        client, so the group's later tests reuse it.
        """
        manager = _manager({"next": 2})
        release = threading.Event()
        stub = _StubClient()

        def start() -> Client:
            release.wait()
            return cast(Client, stub)

        manager.start_ahead("next", start)
        threading.Timer(0.05, release.set).start()
        assert manager.get_client("next") is stub
        assert manager.pending_start is None
        assert manager.get_client("next") is stub

    def test_another_groups_lookup_leaves_the_start_pending(self) -> None:
        """Only the group the client was started for claims it."""
        manager = _manager({"next": 1})
        manager.start_ahead("next", lambda: cast(Client, _StubClient()))
        assert manager.get_client("current") is None
        assert manager.pending_start is not None

    def test_a_failed_start_falls_back_to_a_normal_start(self) -> None:
        """The failure is dropped, so the caller starts the client."""
        manager = _manager({"next": 1})

        def start() -> Client:
            raise RuntimeError("hive refused the client")

        manager.start_ahead("next", start)
        assert manager.get_client("next") is None
        assert manager.pending_start is None

    def test_an_interrupted_wait_leaves_the_start_pending(self) -> None:
        """An interrupt leaves the start to the session-end cleanup."""
        manager = _manager({"next": 1})

        def start() -> Client:
            raise KeyboardInterrupt

        manager.start_ahead("next", start)
        with pytest.raises(KeyboardInterrupt):
            manager.get_client("next")
        assert manager.pending_start is not None

    def test_only_one_client_is_started_ahead(self) -> None:
        """A second start ahead before the first is claimed is a bug."""
        manager = _manager({})
        manager.start_ahead("a", lambda: cast(Client, _StubClient()))
        with pytest.raises(AssertionError, match="already started ahead"):
            manager.start_ahead("b", lambda: cast(Client, _StubClient()))

    def test_an_unclaimed_client_stops_with_its_group(self) -> None:
        """
        A group whose tests never asked for the client (all skipped)
        still stops the client started for it.
        """
        manager = _manager({"next": 1})
        stub = _StubClient()
        manager.start_ahead("next", lambda: cast(Client, stub))
        manager.mark_test_completed("next", "test-a")
        assert stub.stopped
        assert manager.pending_start is None
        assert "next" not in manager.clients

    def test_session_end_stops_an_unclaimed_client(self) -> None:
        """The session-end cleanup stops a client nobody claimed."""
        manager = _manager({"next": 1})
        stub = _StubClient()
        manager.start_ahead("next", lambda: cast(Client, stub))
        manager.stop_all_clients()
        assert stub.stopped


class _Node:
    """A worker that records the indices it is sent."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.gateway = SimpleNamespace(id=name)
        self.sent: List[int] = []
        self.shutting_down = False

    def send_runtest_some(self, indices: List[int]) -> None:
        """Record the dispatched indices."""
        self.sent.extend(indices)

    def shutdown(self) -> None:
        """Record the shutdown."""
        self.shutting_down = True


def _scheduler(
    groups: dict[str, int], nodes: List[_Node]
) -> GroupLookaheadScheduling:
    """Return a scheduler that has collected `groups` on `nodes`."""
    config = SimpleNamespace(
        getvalue={"tx": [f"{len(nodes)}*popen"]}.get,
        option=SimpleNamespace(loadscopereorder=True),
    )
    scheduler = GroupLookaheadScheduling(cast(pytest.Config, config))
    collection = [
        f"test.py::test[{group}-{i}]@{group}"
        for group, count in groups.items()
        for i in range(count)
    ]
    for node in nodes:
        scheduler.add_node(node)
        scheduler.add_node_collection(node, collection)
    scheduler.schedule()
    return scheduler


def _groups_sent(
    scheduler: GroupLookaheadScheduling, node: _Node
) -> List[str]:
    """Return the groups sent to `node`, in order."""
    collection = scheduler.registered_collections[cast(Any, node)]
    groups: List[str] = []
    for index in node.sent:
        group = collection[index].rsplit("@", 1)[1]
        if group not in groups:
            groups.append(group)
    return groups


class TestGroupLookaheadScheduling:
    """Each worker has its next group queued while it runs one."""

    def test_a_worker_is_sent_two_groups_up_front(self) -> None:
        """
        A worker gets its first group of 10 tests alone under xdist's
        `loadgroup`; the lookahead scheduler sends the next group with
        it.
        """
        node = _Node("gw0")
        scheduler = _scheduler({"a": 10, "b": 10, "c": 10}, [node])
        assert _groups_sent(scheduler, node) == ["a", "b"]

    def test_finishing_a_group_queues_the_next(self) -> None:
        """
        A worker is sent a third group once its first completes, not
        before, and every group is sent whole to one worker.
        """
        node = _Node("gw0")
        scheduler = _scheduler({"a": 10, "b": 10, "c": 10, "d": 10}, [node])
        for index in node.sent[:9]:
            scheduler.mark_test_complete(cast(Any, node), index)
        assert _groups_sent(scheduler, node) == ["a", "b"]
        scheduler.mark_test_complete(cast(Any, node), node.sent[9])
        assert _groups_sent(scheduler, node) == ["a", "b", "c"]
        assert len(node.sent) == 30

    def test_a_long_group_gets_its_next_group_near_its_end(self) -> None:
        """
        A group longer than `LOOKAHEAD_TESTS` is sent alone; the next
        group follows once at most `LOOKAHEAD_TESTS` of its tests are
        left, so it cannot hold that group back from idle workers.
        """
        node = _Node("gw0")
        long = LOOKAHEAD_TESTS + 50
        scheduler = _scheduler({"a": long, "b": 10, "c": 10}, [node])
        assert _groups_sent(scheduler, node) == ["a"]
        for index in node.sent[:49]:
            scheduler.mark_test_complete(cast(Any, node), index)
        assert _groups_sent(scheduler, node) == ["a"]
        scheduler.mark_test_complete(cast(Any, node), node.sent[49])
        assert _groups_sent(scheduler, node) == ["a", "b"]

    def test_groups_never_split_across_workers(self) -> None:
        """Every test of a group goes to the worker that got the group."""
        nodes = [_Node("gw0"), _Node("gw1")]
        scheduler = _scheduler(dict.fromkeys("abcdefgh", 3), nodes)
        while scheduler.workqueue:
            for node in nodes:
                for index in list(node.sent):
                    scheduler.mark_test_complete(cast(Any, node), index)
        sent = [set(_groups_sent(scheduler, node)) for node in nodes]
        assert not sent[0] & sent[1]
        assert sent[0] | sent[1] == set("abcdefgh")
        for node in nodes:
            assert len(node.sent) == 3 * len(_groups_sent(scheduler, node))


class _Queue:
    """xdist's worker test queue: a queue behind a lock."""

    def __init__(self, indices: List[Any]) -> None:
        self.items = indices

    @contextmanager
    def lock(self) -> Iterator[List[Any]]:
        """Yield the queued indices."""
        yield self.items


def _item(config: Any, session: Any, name: str) -> Any:
    """Return a stand-in item."""
    return SimpleNamespace(config=config, session=session, name=name)


class TestQueuedItems:
    """The lookahead reads what this process will run next."""

    def test_a_worker_reads_its_next_item_then_its_queue(self) -> None:
        """
        The next item comes first, since xdist takes it off the queue
        before the current one runs; the shutdown marker is skipped.
        """
        interactor = SimpleNamespace(
            torun=_Queue([3, 1, "shutdown"]), nextitem_index=2
        )
        config = SimpleNamespace(
            workerinput={},
            pluginmanager=SimpleNamespace(get_plugins=lambda: [interactor]),
        )
        session = SimpleNamespace(items=[])
        session.items = [_item(config, session, str(i)) for i in range(4)]
        names = [i.name for i in queued_items(session.items[0])]
        assert names == ["2", "3", "1"]

    def test_a_worker_without_its_queue_sees_nothing(self) -> None:
        """
        A worker never falls back to the collection order, which holds
        groups other workers run.
        """
        config = SimpleNamespace(
            workerinput={},
            pluginmanager=SimpleNamespace(get_plugins=lambda: []),
        )
        session = SimpleNamespace(items=[])
        session.items = [_item(config, session, str(i)) for i in range(3)]
        assert list(queued_items(session.items[0])) == []

    def test_without_xdist_every_later_item_is_next(self) -> None:
        """A single process runs the collection in order."""
        config = SimpleNamespace()
        session = SimpleNamespace(items=[])
        session.items = [_item(config, session, str(i)) for i in range(3)]
        names = [i.name for i in queued_items(session.items[1])]
        assert names == ["2"]


class _GroupItem:
    """An item in an xdist group that counts how often it is asked."""

    def __init__(self, group: str) -> None:
        self.group = group
        self.asked = 0

    def iter_markers(self, name: str) -> Iterator[Any]:
        """Yield the item's xdist_group marker."""
        assert name == "xdist_group"
        self.asked += 1
        yield SimpleNamespace(kwargs={"name": self.group})


class TestNextGroupItem:
    """The next group is found without rescanning a long group."""

    def test_only_the_last_item_is_read_while_the_group_runs(self) -> None:
        """
        With only the current group queued, the answer comes from the
        last queued item, however long the group is.
        """
        queued = [_GroupItem("a") for _ in range(1000)]
        assert next_group_item(cast(Any, queued), "a") is None
        assert sum(item.asked for item in queued) == 1

    def test_the_first_item_of_the_next_group_is_returned(self) -> None:
        """Once another group is queued, its first item is returned."""
        queued = [_GroupItem(g) for g in ("a", "a", "b", "b")]
        assert next_group_item(cast(Any, queued), "a") is queued[2]

    def test_nothing_queued_returns_none(self) -> None:
        """A worker at the end of its queue has nothing to start."""
        assert next_group_item([], "a") is None
