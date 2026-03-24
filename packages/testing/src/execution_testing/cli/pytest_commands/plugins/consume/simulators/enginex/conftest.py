"""
Pytest fixtures for the `consume enginex` simulator.

Configure the hive back-end & EL clients for test execution
with `BlockchainEngineXFixtures`. Use multi-test client
architecture to reuse clients across tests with the same
pre-alloc group.
"""

import io
import json
import logging
from typing import TYPE_CHECKING, Generator, cast

import pytest
from hive.client import Client, ClientType
from hive.testing import HiveTest

from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.fixtures.pre_alloc_groups import PreAllocGroup

from ..helpers.test_tracker import (
    PreAllocGroupTestTracker,
    enginex_group_counts_key,
    make_group_identifier,
)

if TYPE_CHECKING:
    from ..multi_test_client import MultiTestClientManager
    from ..timing_data import TimingData

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

    group_counts: dict[str, int] = {}

    for item in items:
        for marker in item.iter_markers("xdist_group"):
            if "name" in marker.kwargs:
                group_identifier = marker.kwargs["name"]
                break
        else:
            continue
        group_counts[group_identifier] = (
            group_counts.get(group_identifier, 0) + 1
        )

    session.stash[enginex_group_counts_key] = group_counts
    logger.info(
        f"Counted {len(group_counts)} pre-alloc groups with "
        f"{sum(group_counts.values())} total tests"
    )

    def sort_key(item: pytest.Item) -> tuple[int, str]:
        """Return sort key: largest group first, then by group id."""
        for marker in item.iter_markers("xdist_group"):
            if "name" in marker.kwargs:
                gid = marker.kwargs["name"]
                return (-group_counts[gid], gid)
        return (0, "")

    items.sort(key=sort_key)
    logger.info("Sorted tests by pre-alloc group (largest first)")


@pytest.fixture(scope="session", autouse=True)
def _configure_client_manager(
    multi_test_client_manager: "MultiTestClientManager",
    pre_alloc_group_test_tracker: PreAllocGroupTestTracker,
) -> None:
    """Wire the test tracker to the client manager at session start."""
    multi_test_client_manager.set_test_tracker(pre_alloc_group_test_tracker)


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


@pytest.fixture(scope="function")
def client(
    multi_test_hive_test: HiveTest,
    multi_test_client_manager: "MultiTestClientManager",
    fixture: BlockchainEngineXFixture,
    client_type: ClientType,
    environment: dict,
    client_genesis: dict,
    total_timing_data: "TimingData",
    request: pytest.FixtureRequest,
) -> Generator[Client, None, None]:
    """
    Get or create a multi-test client for this pre-allocation group.

    Called for each test, but reuses clients across tests that
    share the same pre-allocation group.
    """
    group_identifier = make_group_identifier(
        fixture.pre_hash, client_type.name
    )
    test_id = request.node.nodeid

    resolved_client = multi_test_client_manager.get_client(group_identifier)
    if resolved_client is not None:
        logger.info(f"♻️  Reusing client for group {group_identifier}")
    else:
        # Start new client; calculate genesis
        genesis_bytes = json.dumps(client_genesis).encode("utf-8")
        buffered_genesis = io.BufferedReader(
            cast(io.RawIOBase, io.BytesIO(genesis_bytes))
        )

        logger.info(
            f"🚀 Starting client ({client_type.name}) "
            f"for group {group_identifier}"
        )

        with total_timing_data.time("Start client"):
            resolved_client = multi_test_hive_test.start_client(
                client_type=client_type,
                environment=environment,
                files={"/genesis.json": buffered_genesis},
            )

        assert resolved_client is not None, (
            f"Unable to connect to client ({client_type.name}) via "
            "Hive. Check the client or Hive server logs for more "
            "information."
        )

        logger.info(
            f"Client ({client_type.name}) ready for group {group_identifier}"
        )

        multi_test_client_manager.register_client(
            group_identifier, resolved_client
        )

    try:
        yield resolved_client
    finally:
        multi_test_client_manager.mark_test_completed(
            group_identifier, test_id
        )


@pytest.fixture(scope="function")
def genesis_header(pre_alloc_group: PreAllocGroup) -> FixtureHeader:
    """Provide the genesis header from the pre-allocation group."""
    return pre_alloc_group.genesis
