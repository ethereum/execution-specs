"""Test completion tracking for multi-test client architectures."""

import logging

import pytest
from pytest import StashKey

logger = logging.getLogger(__name__)

# Typed stash keys for session-scoped data (replaces dynamic attributes)
enginex_group_counts_key: StashKey[dict[str, int]] = StashKey()


def make_group_identifier(pre_hash: str, client_name: str) -> str:
    """Build xdist group key from pre-alloc hash and client name."""
    return f"{pre_hash}-{client_name}"


class PreAllocGroupTestTracker:
    """
    Track test completion per pre-allocation group.

    Enable automatic client cleanup. Maintain counts of expected
    vs. completed tests for each group. When all tests in a group
    complete, signal that the associated client can be stopped.
    """

    def __init__(self) -> None:
        """Initialize the test tracker."""
        self.expected_counts: dict[
            str, int
        ] = {}  # group_identifier -> total expected tests
        self.completed_tests: dict[
            str, set[str]
        ] = {}  # group_identifier -> set of completed test IDs
        logger.debug("PreAllocGroupTestTracker initialized")

    def set_group_test_count(self, group_identifier: str, count: int) -> None:
        """
        Set the expected number of tests for a group.

        This is typically called during pytest collection phase.

        """
        self.expected_counts[group_identifier] = count
        self.completed_tests[group_identifier] = set()
        logger.debug(
            f"Set expected test count for group {group_identifier}: {count}"
        )

    def mark_test_completed(self, group_identifier: str, test_id: str) -> bool:
        """
        Mark a test as completed and check if the group is now complete.

        """
        if group_identifier not in self.completed_tests:
            logger.warning(
                f"Marking test complete for unknown group "
                f"{group_identifier}, initializing"
            )
            self.completed_tests[group_identifier] = set()

        self.completed_tests[group_identifier].add(test_id)
        completed = len(self.completed_tests[group_identifier])
        expected = self.expected_counts.get(group_identifier, 0)

        logger.debug(
            f"Group {group_identifier}: {completed}/{expected} tests completed"
        )

        # Check if group is complete
        is_complete = completed >= expected and expected > 0
        if is_complete:
            logger.info(
                f"✓ Pre-alloc group {group_identifier}"
                f" complete ({completed}/{expected} tests)"
            )

        return is_complete


@pytest.fixture(scope="session")
def pre_alloc_group_test_tracker(
    request: pytest.FixtureRequest,
) -> PreAllocGroupTestTracker:
    """
    Provide session-scoped test tracker for automatic client cleanup.

    This fixture initializes the tracker and populates it with test counts
    from the collection phase (if available via pytest stash).
    """
    tracker = PreAllocGroupTestTracker()

    # Load test counts from session stash (set during collection)
    session = request.session
    group_counts = session.stash.get(enginex_group_counts_key, None)
    if group_counts is not None:
        for group_identifier, count in group_counts.items():
            tracker.set_group_test_count(group_identifier, count)
        logger.info(
            f"Loaded {len(group_counts)} group counts from session stash"
        )

    return tracker
