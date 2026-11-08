"""
Tests for counting tests that stop during setup toward their group.

A group's client is stopped when every test of the group has completed.
A test that skips or errors before the `client` fixture would otherwise
never count, and its group's client would outlive the group.
"""

from types import SimpleNamespace
from typing import Any, List, cast

from _pytest.reports import TestReport
from hive.client import Client

from ..simulators.helpers.test_tracker import PreAllocGroupTestTracker
from ..simulators.multi_test_client import (
    MultiTestClientManager,
    multi_test_client_manager_key,
    pytest_runtest_makereport,
)


class _StubClient:
    """A client that only remembers whether it was stopped."""

    def __init__(self) -> None:
        self.stopped = False

    def stop(self) -> None:
        """Record the stop."""
        self.stopped = True


class _MarkedItem:
    """The slice of a pytest item the hook reads."""

    def __init__(self, manager: MultiTestClientManager) -> None:
        self.nodeid = "test_skipped"
        self.session = SimpleNamespace(
            stash={multi_test_client_manager_key: manager}
        )

    def iter_markers(self, name: str) -> List[Any]:
        """Return this item's xdist_group marker."""
        assert name == "xdist_group"
        return [SimpleNamespace(kwargs={"name": "group"})]


def _manager_with_client(
    expected: int,
) -> tuple[MultiTestClientManager, _StubClient]:
    """Return a manager tracking one group with a registered client."""
    manager = MultiTestClientManager()
    tracker = PreAllocGroupTestTracker()
    tracker.set_group_test_count("group", expected)
    manager.set_test_tracker(tracker)
    stub = _StubClient()
    manager.register_client("group", cast(Client, stub))
    return manager, stub


def _drive_hook(item: _MarkedItem, when: str, passed: bool) -> None:
    """Run the wrapper hook around a report with the given outcome."""
    report = SimpleNamespace(when=when, passed=passed)
    hook = pytest_runtest_makereport(cast(Any, item), cast(Any, None))
    next(hook)
    try:
        hook.send(cast(TestReport, report))
    except StopIteration as stop:
        assert stop.value is report


def test_a_test_stopped_in_setup_completes_its_group() -> None:
    """A test that skipped before `client` counts, so the client stops."""
    manager, stub = _manager_with_client(expected=1)
    _drive_hook(_MarkedItem(manager), when="setup", passed=False)
    assert stub.stopped
    assert manager.get_client("group") is None


def test_a_test_past_setup_is_left_to_the_client_fixture() -> None:
    """Passing setup and call-phase reports do not complete the group."""
    manager, stub = _manager_with_client(expected=1)
    _drive_hook(_MarkedItem(manager), when="setup", passed=True)
    _drive_hook(_MarkedItem(manager), when="call", passed=False)
    assert not stub.stopped
