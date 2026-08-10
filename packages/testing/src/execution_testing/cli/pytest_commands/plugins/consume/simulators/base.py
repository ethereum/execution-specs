"""Common pytest fixtures for the Hive simulators."""

import logging
import time
from pathlib import Path
from typing import Dict, Generator, Literal

import pytest
from hive.client import Client

from execution_testing.fixtures import (
    BaseFixture,
)
from execution_testing.fixtures.consume import (
    TestCaseIndexFile,
    TestCaseStream,
)
from execution_testing.fixtures.file import Fixtures
from execution_testing.rpc import EthRPC

from ..consume import FixturesSource
from .helpers.rejected_blocks import BlockRejectionTracker

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def eth_rpc(client: Client) -> Generator[EthRPC, None, None]:
    """Initialize ethereum RPC client for the execution client under test."""
    with EthRPC(f"http://{client.ip}:8545") as rpc:
        yield rpc


@pytest.fixture(scope="session")
def genesis_verified_clients() -> set[str]:
    """
    Return the set of client ids whose genesis block has been verified.

    Genesis is immutable per client, so the `getBlockByNumber(0)` check only
    needs to run once per client. In enginex mode a client is reused across a
    pre-alloc group, letting later tests skip the redundant check.
    """
    return set()


@pytest.fixture(scope="session")
def block_rejection_tracker() -> BlockRejectionTracker:
    """
    Return the tracker of invalid blocks rejected by each client.

    In enginex mode a client is reused across a pre-alloc group, so a later
    test can resubmit a block that the client already rejected for an earlier
    test and receive a generic bad-block-cache error instead of the specific
    validation error. The tracker remembers each client's first rejection so
    the expected exception can be verified against it in that case.
    """
    return BlockRejectionTracker()


@pytest.fixture(scope="function")
def check_live_port(test_suite_name: str) -> Literal[8545, 8551]:
    """Port used by hive to check for liveness of the client."""
    if test_suite_name == "eels/consume-rlp":
        return 8545
    elif test_suite_name in {
        "eels/consume-engine",
        "eels/consume-enginex",
        "eels/consume-sync",
        "eels/consume-wirex",
        "eels/build-block",
    }:
        return 8551
    raise ValueError(
        f"Unexpected test suite name '{test_suite_name}' while setting "
        "HIVE_CHECK_LIVE_PORT."
    )


class FixturesDict(Dict[Path, Fixtures]):
    """
    A dictionary that caches loaded fixture files to avoid reloading the same
    file multiple times.
    """

    def __init__(self) -> None:
        """Initialize the dictionary that caches loaded fixture files."""
        self._fixtures: Dict[Path, Fixtures] = {}

    def __getitem__(self, key: Path) -> Fixtures:
        """
        Return the fixtures from the index file, if not found, load from disk.
        """
        assert key.is_file(), f"Expected a file path, got '{key}'"
        if key not in self._fixtures:
            start = time.perf_counter()
            self._fixtures[key] = Fixtures.model_validate_json(key.read_text())
            logger.info(
                f"⏱ phase=fixture_load file={key.name} "
                f"ms={(time.perf_counter() - start) * 1000:.1f}"
            )
        return self._fixtures[key]


@pytest.fixture(scope="session")
def fixture_file_loader() -> Dict[Path, Fixtures]:
    """
    Return a singleton dictionary that caches loaded fixture files used in all
    tests.
    """
    return FixturesDict()


@pytest.fixture(scope="function")
def fixture(
    fixtures_source: FixturesSource,
    fixture_file_loader: Dict[Path, Fixtures],
    test_case: TestCaseIndexFile | TestCaseStream,
) -> BaseFixture:
    """
    Load the fixture from a file or from stream in any of the supported fixture
    formats.

    The fixture is either already available within the test case (if consume is
    taking input on stdin) or loaded from the fixture json file if taking input
    from disk (fixture directory with index file).
    """
    fixture: BaseFixture
    if fixtures_source.is_stdin:
        assert isinstance(test_case, TestCaseStream), (
            "Expected a stream test case"
        )
        fixture = test_case.fixture
    else:
        assert isinstance(test_case, TestCaseIndexFile), (
            "Expected an index file test case"
        )
        fixtures_file_path = fixtures_source.path / test_case.json_path
        fixtures: Fixtures = fixture_file_loader[fixtures_file_path]
        fixture = fixtures[test_case.id]
    assert isinstance(fixture, test_case.format), (
        f"Expected a {test_case.format.format_name} test fixture"
    )
    return fixture
