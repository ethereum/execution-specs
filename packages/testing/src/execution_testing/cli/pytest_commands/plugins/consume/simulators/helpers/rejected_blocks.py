"""Track invalid blocks previously rejected by a client instance."""

from execution_testing.base_types import Hash
from execution_testing.exceptions import (
    ExceptionInstanceOrList,
    UndefinedException,
)
from execution_testing.rpc.rpc_types import (
    BlockTransactionExceptionWithMessage,
)

ClientValidationError = (
    BlockTransactionExceptionWithMessage | UndefinedException
)


class BlockRejectionTracker:
    """
    Track the first validation error a client returns per invalid block.

    Clients keep a bad-block cache: resubmitting an already-rejected block
    is answered from the cache with a generic error (e.g. reth's "links to
    previously rejected block") instead of being re-validated and
    rejected with the specific error again. In enginex mode a client
    instance is reused across all tests of a pre-allocation group, so two
    tests containing an identical invalid block trigger this cache: the
    first submission is validated for real, the resubmission
    short-circuits.

    Remember the first (real) validation error per client and block so
    that the simulator can verify the expected exception against it when
    the response to a resubmission does not match.
    """

    def __init__(self) -> None:
        """Initialize the tracker with no recorded rejections."""
        self._first_errors: dict[tuple[str, Hash], ClientValidationError] = {}

    def track(
        self,
        client_id: str,
        block_hash: Hash,
        error: ClientValidationError,
    ) -> ClientValidationError | None:
        """
        Track a block rejection and return the earlier error, if any.

        Record `error` as the client's canonical validation error for the
        block if this is the first time the client rejects it; later
        rejections of the same block by the same client do not overwrite
        it. Return the error recorded for the client's earlier rejection
        of the block, or `None` if this is the first one.
        """
        key = (client_id, block_hash)
        earlier_error = self._first_errors.get(key)
        if earlier_error is None:
            self._first_errors[key] = error
        return earlier_error


def matches_expected_exception(
    earlier_rejection: ClientValidationError | None,
    expected_exception: ExceptionInstanceOrList | None,
) -> bool:
    """
    Return whether an earlier rejection matched the expected exception.

    Return `False` if there was no earlier rejection, if its error could
    not be mapped to any exception (`UndefinedException`), or if there is
    no expected exception to match against.
    """
    if expected_exception is None:
        return False
    return (
        isinstance(earlier_rejection, BlockTransactionExceptionWithMessage)
        and expected_exception in earlier_rejection
    )
