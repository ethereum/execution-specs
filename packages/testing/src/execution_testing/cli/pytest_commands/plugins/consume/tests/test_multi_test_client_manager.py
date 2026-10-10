"""Tests for the multi-test client manager's lifecycle bookkeeping."""

from typing import List, cast

from hive.client import Client

from ..simulators.helpers.test_tracker import PreAllocGroupTestTracker
from ..simulators.multi_test_client import MultiTestClientManager


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


class TestDiscardClient:
    """A discarded client is stopped and its group slot freed."""

    def test_discard_stops_and_forgets_the_client(self) -> None:
        """The client is stopped and the next lookup finds nothing."""
        manager = MultiTestClientManager()
        stub = _StubClient()
        manager.register_client("group", cast(Client, stub))
        manager.discard_client("group")
        assert stub.stopped
        assert manager.get_client("group") is None

    def test_discard_of_an_unknown_group_is_a_no_op(self) -> None:
        """Discarding a group without a client changes nothing."""
        MultiTestClientManager().discard_client("missing")

    def test_a_replacement_registers_under_the_same_group(self) -> None:
        """
        The freed slot accepts a new client.

        This is what lets `consume wirex` replace a group's client
        mid-group: `register_client` refuses a second client for a
        live group, so the discard must free the identifier first.
        """
        manager = MultiTestClientManager()
        manager.register_client("group", cast(Client, _StubClient()))
        manager.discard_client("group")
        replacement = _StubClient()
        manager.register_client("group", cast(Client, replacement))
        assert manager.get_client("group") is cast(Client, replacement)

    def test_discard_survives_a_failing_stop(self) -> None:
        """
        A stop error still frees the slot.

        The discard exists so the next test gets a fresh client; a
        client that cannot even be stopped must not wedge the group.
        """
        manager = MultiTestClientManager()
        manager.register_client("group", cast(Client, _UnstoppableClient()))
        manager.discard_client("group")
        assert manager.get_client("group") is None


class TestStopCallbacks:
    """Simulators learn about every client the manager stops."""

    @staticmethod
    def _manager(expected: int) -> MultiTestClientManager:
        manager = MultiTestClientManager()
        tracker = PreAllocGroupTestTracker()
        tracker.set_group_test_count("group", expected)
        manager.set_test_tracker(tracker)
        return manager

    def test_group_completion_runs_the_callbacks(self) -> None:
        """Stopping a completed group's client notifies the callbacks."""
        manager = self._manager(expected=1)
        stopped: List[Client] = []
        manager.stop_callbacks.append(stopped.append)
        stub = cast(Client, _StubClient())
        manager.register_client("group", stub)
        manager.mark_test_completed("group", "test-a")
        assert stopped == [stub]

    def test_discard_and_session_end_run_the_callbacks(self) -> None:
        """Discarded and session-end clients are reported too."""
        manager = self._manager(expected=2)
        stopped: List[Client] = []
        manager.stop_callbacks.append(stopped.append)
        first, second = (cast(Client, _StubClient()) for _ in range(2))
        manager.register_client("group", first)
        manager.discard_client("group")
        manager.register_client("group", second)
        manager.stop_all_clients()
        assert stopped == [first, second]

    def test_a_failing_callback_does_not_block_the_others(self) -> None:
        """One callback's error is logged, not raised."""
        manager = self._manager(expected=1)
        stopped: List[Client] = []

        def broken(client: Client) -> None:
            del client
            raise RuntimeError("peer already closed")

        manager.stop_callbacks.extend([broken, stopped.append])
        manager.register_client("group", cast(Client, _StubClient()))
        manager.mark_test_completed("group", "test-a")
        assert len(stopped) == 1
