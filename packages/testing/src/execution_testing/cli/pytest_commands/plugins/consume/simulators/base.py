"""Common pytest fixtures for the Hive simulators."""

import logging
import time
from collections import OrderedDict
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


FIXTURE_FILE_CACHE_MAX_BYTES = 256 * 1024 * 1024
"""
Default bound of the per-worker fixture file cache, in bytes of fixture JSON
on disk.

Parsed fixtures take about twice their JSON size in memory for typical
files, and every pytest-xdist worker holds its own cache for the whole
session, so the bound must stay well below the memory of the host per
worker.
"""


class FixtureFileCache:
    """
    Cache parsed fixture files with least-recently-used eviction.

    Consume groups test cases by fixture file to improve cache reuse, except
    in EngineX, which groups by pre-allocation. A cached file can serve
    multiple tests without being read and validated again. Scheduling can
    still split a file's tests across workers or cause later revisits.

    Each xdist worker owns a cache for the whole session. Retaining every
    loaded file can contribute to memory pressure during long runs. The
    bound counts JSON bytes on disk, not process memory. The most recently
    loaded file is always kept, even when it exceeds the bound on its own.
    """

    def __init__(self, max_bytes: int = FIXTURE_FILE_CACHE_MAX_BYTES) -> None:
        """Initialize an empty cache with a `max_bytes` JSON size budget."""
        self._max_bytes = max_bytes
        self._fixtures: OrderedDict[Path, Fixtures] = OrderedDict()
        self._sizes: Dict[Path, int] = {}
        self._total_bytes = 0

    def __getitem__(self, key: Path) -> Fixtures:
        """
        Return the fixtures of a fixture file, loading it from disk if it is
        not cached, and evict the least recently used files over the bound.
        """
        assert key.is_file(), f"Expected a file path, got '{key}'"
        if key in self._fixtures:
            self._fixtures.move_to_end(key)
            return self._fixtures[key]
        start = time.perf_counter()
        fixtures = Fixtures.model_validate_json(key.read_text())
        logger.info(
            f"⏱ phase=fixture_load file={key.name} "
            f"ms={(time.perf_counter() - start) * 1000:.1f}"
        )
        self._fixtures[key] = fixtures
        self._sizes[key] = key.stat().st_size
        self._total_bytes += self._sizes[key]
        self._evict()
        return fixtures

    def __contains__(self, key: object) -> bool:
        """Return whether the fixture file is currently cached."""
        return key in self._fixtures

    def __len__(self) -> int:
        """Return the number of cached fixture files."""
        return len(self._fixtures)

    @property
    def cached_bytes(self) -> int:
        """Return the on-disk size of all cached fixture files."""
        return self._total_bytes

    def _evict(self) -> None:
        """Drop least recently used files until within the bound."""
        while self._total_bytes > self._max_bytes and len(self._fixtures) > 1:
            path, _ = self._fixtures.popitem(last=False)
            self._total_bytes -= self._sizes.pop(path)
            logger.debug(
                f"evicted fixture file {path.name} from the cache "
                f"(cached_bytes={self._total_bytes})"
            )


@pytest.fixture(scope="session")
def fixture_file_loader() -> FixtureFileCache:
    """
    Return the per-worker cache of parsed fixture files used by all tests.
    """
    return FixtureFileCache()


@pytest.fixture(scope="function")
def fixture(
    fixtures_source: FixturesSource,
    fixture_file_loader: FixtureFileCache,
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
