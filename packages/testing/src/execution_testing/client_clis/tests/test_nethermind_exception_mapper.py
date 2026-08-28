"""Tests for the frame transaction entries in NethermindExceptionMapper."""

from typing import List, Set, Tuple

import pytest

from execution_testing.client_clis.clis.nethermind import (
    NethermindExceptionMapper,
)
from execution_testing.exceptions import (
    ExceptionBase,
    TransactionException,
    UndefinedException,
)

FORMAT = TransactionException.TYPE_6_INVALID_FRAME_FORMAT
SIGNATURE = TransactionException.TYPE_6_INVALID_SIGNATURE
EXECUTION = TransactionException.TYPE_6_INVALID_FRAME_EXECUTION
TYPE_6 = {FORMAT, SIGNATURE, EXECUTION}

# One client wording per rule, verbatim from the client's own rejection
# message constants.
FRAME_MESSAGES: List[Tuple[str, TransactionException]] = [
    ("frame transaction must contain between 1 and 64 frames", FORMAT),
    ("frame transaction sender must be set", FORMAT),
    ("frame mode must be DEFAULT, VERIFY, SENDER, or POST_TX", FORMAT),
    ("POST_TX frames must form a trailing suffix of the frame list", FORMAT),
    ("POST_TX frames are not enabled", FORMAT),
    ("frame flags must not use reserved bits", FORMAT),
    ("frame value is only allowed in SENDER mode", FORMAT),
    ("frames allowed to approve execution must target the sender", FORMAT),
    ("the last frame must not have the atomic batch flag set", FORMAT),
    ("the atomic batch flag must not be set on a VERIFY frame", FORMAT),
    ("the atomic batch flag must not be set on a POST_TX frame", FORMAT),
    ("an atomic batch frame must not be followed by a VERIFY frame", FORMAT),
    ("an atomic batch frame must not be followed by a POST_TX frame", FORMAT),
    (
        "frames belonging to an atomic batch must not carry approval scope",
        FORMAT,
    ),
    ("total frame gas must not exceed 2^64 - 1", FORMAT),
    (
        "expiry verifier frame must have zero flags, zero value, and 8-byte "
        "data",
        FORMAT,
    ),
    ("at most one expiry verifier frame is allowed", FORMAT),
    ("unknown signature scheme", FORMAT),
    ("ARBITRARY signatures must not name a signer", FORMAT),
    ("signature msg must be empty or a 32-byte digest", FORMAT),
    (
        "frame transaction signature msg must be empty or a 32-byte digest",
        FORMAT,
    ),
    ("explicit signature msg must not be the zero digest", FORMAT),
    ("max fee per blob gas must be 0 when there are no blob hashes", FORMAT),
    ("keyed nonces are not enabled", FORMAT),
    ("legacy nonce is not allowed", FORMAT),
    ("malformed nonce key set", FORMAT),
    ("at most 16 recent root references are allowed", FORMAT),
    (
        "frame transaction SECP256K1 signer does not match the recovered "
        "address",
        FORMAT,
    ),
    ("frame transaction P256 signer does not match the public key", FORMAT),
    ("frame transaction has an invalid signature", SIGNATURE),
    ("frame transaction signature has the wrong length", SIGNATURE),
    (
        "frame transaction signature must use a 0/1 recovery id and a "
        "canonical low s value",
        SIGNATURE,
    ),
    (
        "frame transaction P256 signature must be canonical with a low s "
        "value",
        SIGNATURE,
    ),
    (
        "frame transaction P256 signatures require the secp256r1 precompile",
        SIGNATURE,
    ),
    ("VERIFY frame reverted", EXECUTION),
    ("validation prefix frame reverted", EXECUTION),
    ("SENDER frame before execution approval", EXECUTION),
    ("frame transaction never set a payer", EXECUTION),
    ("frame transaction validation prefix never set a payer", EXECUTION),
]


def matched(message: str) -> Set[ExceptionBase]:
    """Return the exceptions the mapper reports for a client message."""
    exceptions = NethermindExceptionMapper().message_to_exception(message)
    assert not isinstance(exceptions, UndefinedException), message
    return set(exceptions)


@pytest.mark.parametrize(
    "message, expected", FRAME_MESSAGES, ids=[m for m, _ in FRAME_MESSAGES]
)
@pytest.mark.parametrize("wrapped", [False, True])
def test_frame_message_maps_to_exactly_one_type_6_exception(
    message: str, expected: TransactionException, wrapped: bool
) -> None:
    """
    Each client wording maps to its own label and to neither of the other two.

    A fixture naming one label has to fail when the client rejected for
    another, so the format, signature and execution sets must stay pairwise
    disjoint under the mapper's substring and regex matching. `wrapped` covers
    the `Transaction <n> is not valid: <cause>` form the client uses for
    payload transactions.
    """
    if wrapped:
        message = f"Transaction 0 is not valid: {message}"
    exceptions = matched(message)
    assert expected in exceptions
    assert exceptions & TYPE_6 == {expected}


@pytest.mark.parametrize(
    "substring",
    sorted(
        value
        for exception, value in (
            NethermindExceptionMapper.mapping_substring.items()
        )
        if exception not in TYPE_6
    ),
)
def test_no_type_6_label_on_unrelated_messages(substring: str) -> None:
    """No frame label leaks onto a message belonging to another exception."""
    assert not matched(substring) & TYPE_6
