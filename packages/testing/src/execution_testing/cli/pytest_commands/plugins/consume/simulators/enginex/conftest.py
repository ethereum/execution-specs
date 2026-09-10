"""
Pytest fixtures for the `consume enginex` simulator.

Configure the hive back-end & EL clients for test execution
with `BlockchainEngineXFixtures`. Use multi-test client
architecture to reuse clients across tests with the same
pre-alloc group.
"""

import logging
import time
from typing import Generator

import pytest

from execution_testing.fixtures import BlockchainEngineXFixture

from ..helpers.test_tracker import count_tests_per_group

logger = logging.getLogger(__name__)

pytest_plugins = (
    "execution_testing.cli.pytest_commands.plugins.pytest_hive.pytest_hive",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.base",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.multi_test_client",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.test_case_description",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.timing_data",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.exceptions",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.helpers.test_tracker",
    "execution_testing.cli.pytest_commands.plugins.consume.simulators.engine_api",
)


def pytest_configure(config: pytest.Config) -> None:
    """Set the supported fixture formats for the enginex simulator."""
    config.supported_fixture_formats = [BlockchainEngineXFixture]  # type: ignore[attr-defined]


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    """
    Count tests per xdist_group and sort largest groups first.

    The xdist_group markers are set during parametrization in
    `pytest_generate_tests`. This hook reads them to count tests
    per group and sort for optimal xdist scheduling.

    Use `trylast=True` to run after test deselection
    (from `-k`, `-m` filters).
    """
    supported_formats = getattr(config, "supported_fixture_formats", [])
    if BlockchainEngineXFixture not in supported_formats:
        return

    group_counts = count_tests_per_group(session, items)

    def sort_key(item: pytest.Item) -> tuple[int, str]:
        """Return sort key: largest group first, then by group id."""
        for marker in item.iter_markers("xdist_group"):
            if "name" in marker.kwargs:
                gid = marker.kwargs["name"]
                return (-group_counts[gid], gid)
        return (0, "")

    items.sort(key=sort_key)
    logger.info("Sorted tests by pre-alloc group (largest first)")


class _GroupDispatchTracker:
    """
    Per-worker (per-process) tracker of the idle time between test protocols.

    The gap between the end of one test's run protocol and the start of the
    next test's protocol is time the xdist worker spends waiting for the
    controller (dispatch latency) at group boundaries. Small gaps may
    instead be ordinary inter-protocol overhead (e.g. report submission):
    the gap only equals dispatch latency when the worker's local item
    queue is empty.
    """

    last_group: str | None = None
    last_protocol_end: float | None = None


def _xdist_group_name(item: pytest.Item) -> str | None:
    """Return the xdist_group marker name of an item, if any."""
    for marker in item.iter_markers("xdist_group"):
        if "name" in marker.kwargs:
            return marker.kwargs["name"]
    return None


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_protocol(
    item: pytest.Item, nextitem: pytest.Item | None
) -> Generator[None, None, None]:
    """Log a group-start marker with dispatch idle time at group boundaries."""
    del nextitem

    group = _xdist_group_name(item)
    if group is not None and group != _GroupDispatchTracker.last_group:
        if _GroupDispatchTracker.last_protocol_end is not None:
            idle_ms = (
                time.perf_counter() - _GroupDispatchTracker.last_protocol_end
            ) * 1000
            logger.info(
                f"⏱ phase=group_start group={group} idle_ms={idle_ms:.1f}"
            )
        else:
            logger.info(f"⏱ phase=group_start group={group}")
        _GroupDispatchTracker.last_group = group
    yield
    _GroupDispatchTracker.last_protocol_end = time.perf_counter()


@pytest.fixture(scope="module")
def test_suite_name() -> str:
    """The name of the hive test suite used in this simulator."""
    return "eels/consume-enginex"


@pytest.fixture(scope="module")
def test_suite_description() -> str:
    """The description of the hive test suite used in this simulator."""
    return (
        "Execute blockchain tests against clients using the Engine API with "
        "pre-allocation group optimization using Engine X fixtures."
    )
