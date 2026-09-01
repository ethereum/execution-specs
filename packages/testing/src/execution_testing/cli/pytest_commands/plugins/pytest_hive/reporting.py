"""
Helpers detecting silent hive test-result loss.

At very high test throughput (e.g. `consume-enginex`), the simulator
can transiently exhaust its ephemeral port range toward the hive API
endpoint: `connect()` then fails with `EADDRNOTAVAIL` for a few seconds
on all xdist workers at once. Tests in flight during such a burst
either error at setup (`start_test` failed: the test is then silently
missing from the hive results), or run and pass but never report their
verdict (`end_test` failed: the dangling hive test case is later
force-closed as "Test was terminated by host").

The root fix is connection pooling and connection-establishment retries
in the `ethereum-hive` package. The helpers here provide complementary
simulator-side detection by comparing the number of test results
successfully reported to hive against the tests pytest actually ran.
"""

import json
import os
from pathlib import Path
from typing import Dict, TypedDict

import pytest
from hive.testing import HiveTest, HiveTestResult, HiveTestSuite

from execution_testing.logging import get_logger

logger = get_logger(__name__)

reported_test_ids_key = pytest.StashKey[set[str]]()
"""Node IDs whose results this process successfully reported to hive."""

skipped_test_ids_key = pytest.StashKey[set[str]]()
"""Node IDs skipped before their hive test was started."""

executed_test_ids_key = pytest.StashKey[set[str]]()
"""Node IDs for which this process produced a setup report."""

hive_test_started_key = pytest.StashKey[bool]()
"""Whether a pytest item has successfully started its hive test."""


class WorkerTestCounts(TypedDict):
    """Persisted test-accounting state for one pytest worker."""

    reported: int
    skipped: int
    executed: int
    interrupted: bool


class HiveReportedTestCountError(Exception):
    """The number of hive test results does not match the pytest run."""


def record_test_execution(item: pytest.Item) -> None:
    """Record that pytest produced a setup report for an item."""
    item.config.stash.setdefault(executed_test_ids_key, set()).add(item.nodeid)


def mark_hive_test_started(item: pytest.Item) -> None:
    """Record that an item's hive test was successfully started."""
    item.stash[hive_test_started_key] = True


def end_test_and_count(
    config: pytest.Config,
    nodeid: str,
    test: HiveTest,
    result: HiveTestResult,
) -> None:
    """End a hive test once and record its successfully reported result."""
    test.end(result=result)
    config.stash.setdefault(reported_test_ids_key, set()).add(nodeid)


def count_skipped_test(item: pytest.Item) -> None:
    """
    Record a test skipped before its hive test was started.

    A later fixture can skip an item after `hive_test` has started. That
    item must be accounted for by the hive result instead of being counted
    as both skipped and reported.
    """
    if item.stash.get(hive_test_started_key, False):
        return
    item.config.stash.setdefault(skipped_test_ids_key, set()).add(item.nodeid)


def write_reported_test_count(
    config: pytest.Config,
    session: pytest.Session,
    session_temp_folder: Path,
) -> None:
    """
    Persist this process's test-accounting state to the shared session
    folder so the last-finishing xdist worker can verify the full run.
    """
    worker_id = os.environ.get("PYTEST_XDIST_WORKER", "master")
    counts: WorkerTestCounts = {
        "reported": len(config.stash.get(reported_test_ids_key, set())),
        "skipped": len(config.stash.get(skipped_test_ids_key, set())),
        "executed": len(config.stash.get(executed_test_ids_key, set())),
        "interrupted": bool(session.shouldstop or session.shouldfail),
    }
    count_file = (
        session_temp_folder / f"hive_reported_test_count_{worker_id}.json"
    )
    with open(count_file, "w") as f:
        json.dump(counts, f)


def verify_reported_test_count(
    request: pytest.FixtureRequest,
    suite: HiveTestSuite,
    session_temp_folder: Path,
) -> str | None:
    """
    Verify that every collected test reported a result to hive.

    Return an error message if results were lost, `None` otherwise. On
    loss, additionally report a failing meta-test case to hive so that
    the loss is visible in the hive results, where the affected tests
    are otherwise silently missing.
    """
    session = request.session
    collected = session.testscollected
    reported = 0
    skipped = 0
    executed = 0
    interrupted_workers: list[str] = []
    worker_counts: Dict[str, WorkerTestCounts] = {}
    for count_file in sorted(
        session_temp_folder.glob("hive_reported_test_count_*.json")
    ):
        with open(count_file, "r") as f:
            counts: WorkerTestCounts = json.load(f)
        worker_id = count_file.stem.removeprefix("hive_reported_test_count_")
        worker_counts[worker_id] = counts
        reported += counts["reported"]
        skipped += counts["skipped"]
        executed += counts["executed"]
        if counts["interrupted"]:
            interrupted_workers.append(worker_id)
        count_file.unlink()

    if (
        session.shouldstop
        or session.shouldfail
        or interrupted_workers
        or executed < collected
    ):
        logger.warning(
            "Test run was interrupted; skipping the collected-vs-reported "
            f"hive test count check ({executed}/{collected} tests ran; "
            f"interrupted workers: {interrupted_workers})."
        )
        return None

    accounted = reported + skipped
    if executed == collected and accounted == collected:
        logger.info(
            f"All {collected} collected tests are accounted for "
            f"({reported} reported to hive, {skipped} skipped)."
        )
        return None

    if executed > collected:
        message = (
            f"{executed - collected} more test execution(s) than collected "
            f"tests were recorded: {executed} ran, but only {collected} were "
            f"collected (per-worker counts: {worker_counts})."
        )
    elif accounted < collected:
        message = (
            f"{collected - accounted} test result(s) were not reported to "
            f"hive: collected and ran {collected} tests, but only {reported} "
            f"result(s) were reported and {skipped} test(s) were skipped "
            f"(per-worker counts: {worker_counts}). Results are typically "
            f"lost when hive API calls fail, e.g. due to client startup "
            f"failures or ephemeral port exhaustion (EADDRNOTAVAIL) at high "
            f"test throughput."
        )
    else:
        message = (
            f"{accounted - collected} more hive result(s) than collected "
            f"tests were recorded: {reported} reported + {skipped} skipped > "
            f"{collected} collected (per-worker counts: {worker_counts})."
        )
    logger.error(message)
    try:
        check_test = suite.start_test(
            name="reported-test-count-check",
            description=(
                "Meta-test verifying that every collected test reported "
                "its result to hive; fails if test results were lost."
            ),
        )
        check_test.end(result=HiveTestResult(test_pass=False, details=message))
    except Exception as e:
        logger.error(f"Failed to report the test count mismatch: {e}")
    return message
