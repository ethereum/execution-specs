"""
Pytest fixtures for the `consume enginex` simulator.

Configure the hive back-end & EL clients for test execution
with `BlockchainEngineXFixtures`. Use multi-test client
architecture to reuse clients across tests with the same
pre-alloc group.
"""

import logging
import time
from typing import TYPE_CHECKING, Generator

import pytest
from hive.client import Client, ClientType

from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.consume import TestCaseIndexFile

from ..helpers.group_splitter import split_oversized_groups
from ..helpers.test_tracker import count_tests_per_group, xdist_group_of

if TYPE_CHECKING:
    from ..multi_test_client import MultiTestClientManager

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


MAX_REUSED_HEAD_NUMBER: dict[str, int] = {"ethrex": 128}
"""
Highest head, by block number, from which a reused client of these
clients is asked to rewind to genesis.

Each test starts with a forkchoice update to genesis, so the next test
makes the client unwind the whole chain the previous test left. A
client listed here is replaced with a fresh one after a test that
leaves a higher head, keyed by a substring of the Hive client name.

ethrex keeps the state of its latest 128 blocks in memory and rebuilds
older state from its state-history journal. When two different blocks
at the same height have the same post-state root (for example an empty
block and one with only zero-value withdrawals), the journal keeps the
wrong block hash, the rewind is refused, and ethrex never recovers: all
later tests in the group time out.
"""


def deepest_head_number(fixture: BlockchainEngineXFixture) -> int:
    """
    Return the highest block number among the fixture's valid payloads.

    The simulator moves the head to every valid payload in turn, so this
    is the deepest head the test leaves the client with; genesis (0) if
    the fixture has no valid payload.
    """
    return max(
        (int(p.params[0].number) for p in fixture.payloads if p.valid()),
        default=0,
    )


def max_reused_head_number(client_type_name: str) -> int | None:
    """
    Return the `MAX_REUSED_HEAD_NUMBER` limit for a Hive client name.

    Return `None` for a client that is always reused.
    """
    for client, max_head in MAX_REUSED_HEAD_NUMBER.items():
        if client in client_type_name:
            return max_head
    return None


def pytest_configure(config: pytest.Config) -> None:
    """Set the supported fixture formats for the enginex simulator."""
    config.supported_fixture_formats = [BlockchainEngineXFixture]  # type: ignore[attr-defined]


def _fixture_file(item: pytest.Item) -> str:
    """
    Return the path of the fixture file that holds an item's test case.

    Return an empty string for a test case read from stdin, which has no
    file.
    """
    callspec = getattr(item, "callspec", None)
    if callspec is None:
        return ""
    test_case = callspec.params.get("test_case")
    if isinstance(test_case, TestCaseIndexFile):
        return str(test_case.json_path)
    return ""


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    """
    Split oversized groups, then count and sort the groups by size.

    The xdist_group markers are set during parametrization in
    `pytest_generate_tests`. Split any group too large for a single
    worker to finish in step with the others, then count the tests per
    (sub-)group and sort largest first for optimal xdist scheduling.

    Use `trylast=True` to run after test deselection (from `-k`, `-m` and
    `--sim.limit` filters), so that the split is sized against the tests
    that will actually run.
    """
    supported_formats = getattr(config, "supported_fixture_formats", [])
    if BlockchainEngineXFixture not in supported_formats:
        return

    split_oversized_groups(config, items)

    group_counts = count_tests_per_group(session, items)

    def sort_key(item: pytest.Item) -> tuple[int, str, str]:
        """
        Return sort key: largest group first, then by group id, then by
        fixture file.

        Keeping the tests of a fixture file contiguous within a group lets
        the worker's fixture file cache load each file once per group.
        """
        group = xdist_group_of(item)
        if group is None:
            return (0, "", "")
        return (-group_counts[group], group, _fixture_file(item))

    items.sort(key=sort_key)
    logger.info(
        "Sorted tests by pre-alloc group (largest first) and fixture file"
    )


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


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_protocol(
    item: pytest.Item, nextitem: pytest.Item | None
) -> Generator[None, None, None]:
    """Log a group-start marker with dispatch idle time at group boundaries."""
    del nextitem

    group = xdist_group_of(item)
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


@pytest.fixture(scope="function", autouse=True)
def _replace_client_after_a_deep_chain(
    client: Client,
    multi_test_client_manager: "MultiTestClientManager",
    fixture: BlockchainEngineXFixture,
    client_type: ClientType,
) -> Generator[None, None, None]:
    """
    Discard the group's client after a test that leaves too deep a head.

    Torn down before `client`, so the discard happens before the test is
    counted toward its group, as in the `client` fixture this replaces.
    See `MAX_REUSED_HEAD_NUMBER`.
    """
    yield
    max_head = max_reused_head_number(client_type.name)
    head = deepest_head_number(fixture)
    if max_head is None or head <= max_head:
        return
    for group_identifier, group_client in list(
        multi_test_client_manager.clients.items()
    ):
        if group_client is client:
            logger.info(
                f"Replacing the client of group {group_identifier}: this "
                f"test left its head at block {head}, above {max_head}"
            )
            multi_test_client_manager.discard_client(group_identifier)
