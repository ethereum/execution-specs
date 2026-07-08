"""Tests for the block rejection tracker used by the engine simulators."""

from execution_testing.base_types import Hash
from execution_testing.exceptions import (
    BlockException,
    UndefinedException,
)
from execution_testing.rpc.rpc_types import (
    BlockTransactionExceptionWithMessage,
)

from ..simulators.helpers.rejected_blocks import (
    BlockRejectionTracker,
    matches_expected_exception,
)

CLIENT_A = "client-a"
CLIENT_B = "client-b"
BLOCK_1 = Hash(1)
BLOCK_2 = Hash(2)

EXCESS_BLOB_GAS_ERROR = BlockTransactionExceptionWithMessage(
    exceptions=[BlockException.INCORRECT_EXCESS_BLOB_GAS],
    message="invalid excess blob gas: got 1179648, expected 1048576",
)
CACHED_REJECTION_ERROR = UndefinedException(
    "links to previously rejected block",
    mapper_name="RethExceptionMapper",
)


def test_first_rejection_returns_no_earlier_error() -> None:
    """The first rejection of a block has no earlier error."""
    tracker = BlockRejectionTracker()
    assert tracker.track(CLIENT_A, BLOCK_1, EXCESS_BLOB_GAS_ERROR) is None


def test_resubmission_returns_first_error() -> None:
    """Rejections after the first return the first recorded error."""
    tracker = BlockRejectionTracker()
    tracker.track(CLIENT_A, BLOCK_1, EXCESS_BLOB_GAS_ERROR)
    assert (
        tracker.track(CLIENT_A, BLOCK_1, CACHED_REJECTION_ERROR)
        is EXCESS_BLOB_GAS_ERROR
    )
    # The first error is not overwritten by later rejections.
    assert (
        tracker.track(CLIENT_A, BLOCK_1, CACHED_REJECTION_ERROR)
        is EXCESS_BLOB_GAS_ERROR
    )


def test_rejections_are_tracked_per_client() -> None:
    """A rejection by one client is not an earlier error for another."""
    tracker = BlockRejectionTracker()
    tracker.track(CLIENT_A, BLOCK_1, EXCESS_BLOB_GAS_ERROR)
    assert tracker.track(CLIENT_B, BLOCK_1, CACHED_REJECTION_ERROR) is None


def test_rejections_are_tracked_per_block() -> None:
    """A rejection of one block is not an earlier error for another."""
    tracker = BlockRejectionTracker()
    tracker.track(CLIENT_A, BLOCK_1, EXCESS_BLOB_GAS_ERROR)
    assert tracker.track(CLIENT_A, BLOCK_2, CACHED_REJECTION_ERROR) is None


def test_matching_earlier_rejection() -> None:
    """An earlier rejection matches its mapped exception."""
    assert matches_expected_exception(
        EXCESS_BLOB_GAS_ERROR, BlockException.INCORRECT_EXCESS_BLOB_GAS
    )


def test_matching_earlier_rejection_with_exception_list() -> None:
    """An earlier rejection matches a list containing its exception."""
    assert matches_expected_exception(
        EXCESS_BLOB_GAS_ERROR,
        [
            BlockException.INCORRECT_BLOB_GAS_USED,
            BlockException.INCORRECT_EXCESS_BLOB_GAS,
        ],
    )


def test_mismatching_earlier_rejection() -> None:
    """An earlier rejection does not match a different exception."""
    assert not matches_expected_exception(
        EXCESS_BLOB_GAS_ERROR, BlockException.INCORRECT_BLOB_GAS_USED
    )


def test_no_earlier_rejection_never_matches() -> None:
    """A block that was never rejected before cannot match."""
    assert not matches_expected_exception(
        None, BlockException.INCORRECT_EXCESS_BLOB_GAS
    )


def test_undefined_earlier_rejection_never_matches() -> None:
    """An unmappable earlier rejection cannot be verified as a match."""
    assert not matches_expected_exception(
        CACHED_REJECTION_ERROR,
        BlockException.INCORRECT_EXCESS_BLOB_GAS,
    )


def test_no_expected_exception_never_matches() -> None:
    """Without an expected exception there is nothing to match."""
    assert not matches_expected_exception(EXCESS_BLOB_GAS_ERROR, None)
