"""Tests for the multi-test client manager's lifecycle bookkeeping."""

from contextlib import nullcontext
from types import SimpleNamespace
from typing import Any, Iterator, List, cast

import pytest
from hive.client import Client

from ..simulators.helpers.test_tracker import (
    PreAllocGroupTestTracker,
    make_group_identifier,
)
from ..simulators.multi_test_client import (
    MultiTestClientManager,
    group_client,
)
from .variant_generator import PRE_HASH


class _StubClient:
    """A client that only remembers whether it was stopped."""

    def __init__(self) -> None:
        self.id = "stub"
        self.stopped = False

    def stop(self) -> None:
        """Record the stop."""
        self.stopped = True


class _UnstoppableClient:
    """A client whose stop always fails."""

    def stop(self) -> None:
        """Fail the way a dead container fails."""
        raise RuntimeError("container already gone")


def _register(
    manager: MultiTestClientManager, group: str, client: Any = None
) -> Any:
    """Register `client`, a fresh stub by default, and return it."""
    client = _StubClient() if client is None else client
    manager.register_client(group, cast(Client, client))
    return client


def _manager(
    counts: dict[str, int],
) -> tuple[MultiTestClientManager, List[Client]]:
    """Return a manager expecting `counts` and the clients it stops."""
    manager = MultiTestClientManager()
    tracker = PreAllocGroupTestTracker()
    for group, count in counts.items():
        tracker.set_group_test_count(group, count)
    manager.set_test_tracker(tracker)
    stopped: List[Client] = []
    manager.stop_callbacks.append(stopped.append)
    return manager, stopped


class TestDiscardClient:
    """A discarded client is stopped and its group slot freed."""

    def test_a_discard_stops_and_frees_only_its_group(self) -> None:
        """
        A live group refuses a second client, and discarding an unknown
        group changes nothing. A discarded client is stopped and the next
        lookup finds nothing, so a replacement takes the slot, which a
        stop that fails still frees.
        """
        manager = MultiTestClientManager()
        stub = _register(manager, "group")
        other = _register(manager, "other")
        with pytest.raises(RuntimeError, match="already exists"):
            _register(manager, "group")
        manager.discard_client("missing")
        assert not stub.stopped and not other.stopped
        manager.discard_client("group")
        assert stub.stopped
        assert manager.get_client("group") is None
        assert manager.get_client("other") is other
        replacement = _register(manager, "group", _UnstoppableClient())
        assert manager.get_client("group") is replacement
        manager.discard_client("group")
        assert manager.get_client("group") is None


class TestStopCallbacks:
    """Simulators learn about every client the manager stops."""

    def test_group_completion_runs_the_callbacks(self) -> None:
        """Stopping a completed group's client notifies the callbacks."""
        manager, stopped = _manager({"group": 1})
        stub = _register(manager, "group")
        manager.mark_test_completed("group", "test-a")
        assert stopped == [stub]

    def test_discard_and_session_end_run_the_callbacks(self) -> None:
        """Discarded and session-end clients are reported too."""
        manager, stopped = _manager({"group": 2})
        first = _register(manager, "group")
        manager.discard_client("group")
        second = _register(manager, "group")
        manager.stop_all_clients()
        assert stopped == [first, second]

    def test_a_failing_callback_does_not_block_the_others(self) -> None:
        """One callback's error is logged, not raised."""
        manager, stopped = _manager({"group": 1})

        def broken(client: Client) -> None:
            del client
            raise RuntimeError("peer already closed")

        manager.stop_callbacks.insert(0, broken)
        _register(manager, "group")
        manager.mark_test_completed("group", "test-a")
        assert len(stopped) == 1


GROUP = make_group_identifier(PRE_HASH, "geth")
VARIANT_GROUP = make_group_identifier(PRE_HASH, "geth", "bal_served")


class _Hive:
    """A Hive test that starts stub clients and counts the boots."""

    def __init__(self) -> None:
        """Start with no clients booted."""
        self.booted: List[_StubClient] = []

    def start_client(self, **kwargs: Any) -> _StubClient:
        """Boot a stub client."""
        del kwargs
        self.booted.append(_StubClient())
        return self.booted[-1]


class _Node:
    """The slice of a test item `group_client` reads."""

    def __init__(self, group: str, nodeid: str) -> None:
        """Hold the group the generator assigned the test."""
        self.group = group
        self.nodeid = nodeid

    def iter_markers(self, name: str) -> Iterator[pytest.Mark]:
        """Yield this test's xdist_group marker."""
        assert name == "xdist_group"
        yield pytest.mark.xdist_group(name=self.group).mark


class TestGroupClient:
    """Tests of one client group share one client."""

    @staticmethod
    def _run(
        hive: _Hive, manager: MultiTestClientManager, group: str, test: str
    ) -> _StubClient:
        """Set up and tear down the `client` fixture for one test."""
        fixture = group_client(
            cast(Any, hive),
            manager,
            cast(Any, SimpleNamespace(name="geth")),
            {},
            {},
            cast(Any, SimpleNamespace(time=nullcontext)),
            cast(Any, SimpleNamespace(node=_Node(group, test))),
        )
        client = next(fixture)
        fixture.close()
        return cast(_StubClient, client)

    def test_a_group_boots_its_client_once(self) -> None:
        """The second test reuses the client; the last one stops it."""
        hive = _Hive()
        manager, _ = _manager({GROUP: 2, VARIANT_GROUP: 2})
        first = self._run(hive, manager, GROUP, "test-a")
        assert not first.stopped
        second = self._run(hive, manager, GROUP, "test-b")
        assert second is first
        assert hive.booted == [first]
        assert first.stopped
        assert manager.get_client(GROUP) is None

    def test_a_variant_group_boots_its_own_client(self) -> None:
        """A variant of the same pre-allocation group gets a new client."""
        hive = _Hive()
        manager, _ = _manager({GROUP: 2, VARIANT_GROUP: 2})
        plain = self._run(hive, manager, GROUP, "test-a")
        served = self._run(hive, manager, VARIANT_GROUP, "test-a-served")
        assert served is not plain
        assert hive.booted == [plain, served]
        assert manager.get_client(GROUP) is cast(Client, plain)
        assert manager.get_client(VARIANT_GROUP) is cast(Client, served)
