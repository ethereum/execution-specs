"""Tests for the frame transaction entries in EthrexExceptionMapper."""

from typing import Set

import pytest

from execution_testing.client_clis.clis.ethrex import EthrexExceptionMapper
from execution_testing.exceptions import (
    ExceptionBase,
    TransactionException,
    UndefinedException,
)

FORMAT = TransactionException.TYPE_6_INVALID_FRAME_FORMAT


def matched(message: str) -> Set[ExceptionBase]:
    """Return the exceptions the mapper reports for a client message."""
    exceptions = EthrexExceptionMapper().message_to_exception(message)
    assert not isinstance(exceptions, UndefinedException), message
    return set(exceptions)


@pytest.mark.parametrize(
    "message",
    [
        "Error decoding field 'frames' of type alloc::vec::Vec<"
        "ethrex_common::types::transaction::Frame>: InvalidLength",
        "Error decoding field 'signatures' of type alloc::vec::Vec<"
        "ethrex_common::types::transaction::FrameSignature>: InvalidLength",
        "Error decoding field 'nonce_keys' of type alloc::vec::Vec<"
        "primitive_types::U256>: InvalidLength",
        "Error decoding field 'nonce_seq' of type u64: InvalidLength",
    ],
)
def test_frame_field_too_wide_maps_to_invalid_frame_format(
    message: str,
) -> None:
    """
    A frame transaction field too wide for its type, which ethrex rejects
    while decoding, maps to the frame format label.

    The messages are ethrex's verbatim, including the EIP-8250 nonce key
    set and nonce sequence of `test_static_validity`'s `key_beyond_width`
    and `seq_beyond_width` cases.
    """
    assert FORMAT in matched(message)


def test_other_field_too_wide_is_not_a_frame_format_error() -> None:
    """The frame label does not leak onto other transaction types' fields."""
    message = "Error decoding field 'nonce' of type u64: InvalidLength"
    assert FORMAT not in matched(message)
