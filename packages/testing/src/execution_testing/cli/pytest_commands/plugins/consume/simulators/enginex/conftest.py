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
from typing import Generator, cast

import pytest
from hive.client import Client, ClientType
from hive.testing import HiveTest

from execution_testing.fixtures import BlockchainEngineXFixture
from execution_testing.fixtures.blockchain import FixtureHeader
from execution_testing.fixtures.pre_alloc_groups import PreAllocGroup

from ..helpers.test_tracker import (
    PreAllocGroupTestTracker,
    enginex_group_counts_key,
    format_group_identifier,
)
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
    Count tests per pre-allocation group during collection phase.

    This hook analyzes all collected test items to determine how many tests
    belong to each pre-alloc group, enabling automatic client cleanup when
    all tests in a group complete.

    Use `trylast=True` to run after test deselection
    (from `-k`, `-m` filters).
    Reads group identifiers from `xdist_group` markers added in
    `pytest_generate_tests`.
    """
    supported_formats = getattr(config, "supported_fixture_formats", [])
    if BlockchainEngineXFixture not in supported_formats:
        return

    group_counts: dict[str, int] = {}

    for item in items:
        # Extract group identifier from xdist_group marker
        # (marker was added in pytest_generate_tests in consume.py)
        group_identifier = None
        for marker in item.iter_markers("xdist_group"):
            if hasattr(marker, "kwargs") and "name" in marker.kwargs:
                group_identifier = marker.kwargs["name"]
                break

        if group_identifier:
            group_counts[group_identifier] = (
                group_counts.get(group_identifier, 0) + 1
            )

    if group_counts:
        # Store counts in session stash for the test tracker fixture to use
        session.stash[enginex_group_counts_key] = group_counts
        logger.info(
            f"Counted {len(group_counts)} pre-alloc groups with "
            f"{sum(group_counts.values())} total tests"
        )

        # Sort tests by group_identifier to ensure consecutive execution
        # This minimizes client thrashing and enables immediate client cleanup
        def get_group_key(item: pytest.Item) -> str:
            """Extract group identifier from item for sorting."""
            for marker in item.iter_markers("xdist_group"):
                if hasattr(marker, "kwargs") and "name" in marker.kwargs:
                    return marker.kwargs["name"]
            raise AssertionError(
                f"EngineX test '{item.nodeid}' missing xdist_group marker"
            )

        items.sort(key=get_group_key)
        logger.info(
            "Sorted tests by pre-alloc group for consecutive execution"
        )
    else:
        logger.warning("No enginex test groups found during collection")


@pytest.fixture(scope="session", autouse=True)
def _configure_client_manager(
    multi_test_client_manager: MultiTestClientManager,
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
    multi_test_client_manager: MultiTestClientManager,
    fixture: BlockchainEngineXFixture,
    client_type: ClientType,
    environment: dict,
    client_genesis: dict,
    total_timing_data: TimingData,
    request: pytest.FixtureRequest,
) -> Generator[Client, None, None]:
    """
    Get or create a multi-test client for this pre-allocation group.

    Called for each test, but reuses clients across tests that
    share the same pre-allocation group.
    """
    group_identifier = fixture.pre_hash
    test_id = request.node.nodeid

    # Check for existing client
    existing_client = multi_test_client_manager.get_client(group_identifier)
    if existing_client is not None:
        logger.info(
            f"♻️  Reusing client for group "
            f"{format_group_identifier(group_identifier)}"
        )
        try:
            yield existing_client
        finally:
            multi_test_client_manager.mark_test_completed(
                group_identifier, test_id
            )
        return

    # Start new client; calculate genesis
    genesis_bytes = json.dumps(client_genesis).encode("utf-8")
    buffered_genesis = io.BufferedReader(
        cast(io.RawIOBase, io.BytesIO(genesis_bytes))
    )

    logger.info(
        f"🚀 Starting client ({client_type.name}) for group "
        f"{format_group_identifier(group_identifier)}"
    )

    with total_timing_data.time("Start client"):
        client = multi_test_hive_test.start_client(
            client_type=client_type,
            environment=environment,
            files={"/genesis.json": buffered_genesis},
        )

    assert client is not None, (
        f"Unable to connect to client ({client_type.name}) via Hive. "
        "Check the client or Hive server logs for more information."
    )

    logger.info(
        f"Client ({client_type.name}) ready for group "
        f"{format_group_identifier(group_identifier)}"
    )

    multi_test_client_manager.register_client(group_identifier, client)

    try:
        yield client
    finally:
        multi_test_client_manager.mark_test_completed(
            group_identifier, test_id
        )


@pytest.fixture(scope="function")
def genesis_header(pre_alloc_group: PreAllocGroup) -> FixtureHeader:
    """Provide the genesis header from the pre-allocation group."""
    return pre_alloc_group.genesis
