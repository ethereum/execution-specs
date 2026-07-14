"""Track and verify invalid blocks rejected by a client instance."""

from execution_testing.base_types import Hash
from execution_testing.exceptions import (
    ExceptionInstanceOrList,
    UndefinedException,
)
from execution_testing.logging import get_logger
from execution_testing.rpc.rpc_types import (
    BlockTransactionExceptionWithMessage,
    ClientValidationError,
)

from .exceptions import LoggedError

logger = get_logger(__name__)


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
    ) -> ClientValidationError:
        """
        Track a block rejection and return the client's first error for it.

        Record `error` as the client's canonical validation error for the
        block if this is the first time the client rejects it; later
        rejections of the same block by the same client do not overwrite
        it. Return the recorded first error, which is `error` itself when
        this is the first rejection.
        """
        return self._first_errors.setdefault((client_id, block_hash), error)


def matches_expected_exception(
    first_rejection: ClientValidationError,
    expected_exception: ExceptionInstanceOrList | None,
) -> bool:
    """
    Return whether a tracked rejection matched the expected exception.

    Return `False` if the rejection's error could not be mapped to any
    exception (`UndefinedException`) or if there is no expected exception
    to match against.
    """
    if expected_exception is None:
        return False
    return (
        isinstance(first_rejection, BlockTransactionExceptionWithMessage)
        and expected_exception in first_rejection
    )


def verify_block_rejection(
    expected_exception: ExceptionInstanceOrList | None,
    returned_error: ClientValidationError,
    first_rejection: ClientValidationError,
    block_hash: Hash,
    strict_exception_matching: bool,
) -> None:
    """
    Verify a client's block rejection against the expected exception.

    Raise `LoggedError` if `returned_error` does not match
    `expected_exception` (or could not be mapped to any exception at all)
    and strict exception matching is enabled; without strict matching only
    log a warning.

    Accept and log a mismatched `returned_error` when `first_rejection`,
    the client's first rejection of the same block, matched the expected
    exception: the client has answered a resubmission of the block from
    its bad-block cache with a generic error instead of re-validating it.
    A mismatched or unmappable error can never match itself, so a block's
    first rejection is always verified strictly.
    """
    if isinstance(returned_error, UndefinedException):
        message = (
            "Undefined exception message: "
            f'expected exception: "{expected_exception}", '
            f'returned exception: "{returned_error}" '
            f'(mapper: "{returned_error.mapper_name}")'
        )
    elif expected_exception not in returned_error:
        message = (
            "Client returned unexpected validation error: "
            f'got: "{returned_error}" '
            f'expected: "{expected_exception}"'
        )
    else:
        return
    if matches_expected_exception(first_rejection, expected_exception):
        logger.info(
            f"Accepting mismatched validation error for block {block_hash}: "
            "this client already rejected the same block with an error "
            f'matching the expected exception ("{first_rejection}") and '
            "has rejected the resubmission from its bad-block cache. "
            f"{message}"
        )
    elif strict_exception_matching:
        raise LoggedError(message)
    else:
        logger.warning(message)
