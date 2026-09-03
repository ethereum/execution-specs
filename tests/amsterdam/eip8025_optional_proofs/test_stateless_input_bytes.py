"""Stateless input byte validation tests."""

from typing import Callable

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    Fork,
    Transaction,
)

from .gas_helpers import empty_account_value_transfer_gas_limit

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

StatelessInputBytesModifier = Callable[[Bytes], Bytes]


def empty_input_bytes(input_bytes: Bytes) -> Bytes:
    """Replace stateless input bytes with empty input."""
    del input_bytes
    return Bytes(b"")


def incomplete_schema_id(input_bytes: Bytes) -> Bytes:
    """Keep only one byte of the schema id."""
    return Bytes(input_bytes[:1])


def unsupported_schema_revision(input_bytes: Bytes) -> Bytes:
    """Replace the schema id with an unsupported Amsterdam revision."""
    return Bytes(b"\x15\x02" + input_bytes[2:])


def unsupported_schema_fork(input_bytes: Bytes) -> Bytes:
    """Replace the schema id with an unsupported fork."""
    return Bytes(b"\x16\x01" + input_bytes[2:])


def missing_ssz_body(input_bytes: Bytes) -> Bytes:
    """Keep only the schema id."""
    return Bytes(input_bytes[:2])


def truncated_ssz_body(input_bytes: Bytes) -> Bytes:
    """Drop the final SSZ body byte."""
    return Bytes(input_bytes[:-1])


def trailing_garbage(input_bytes: Bytes) -> Bytes:
    """Append extra bytes after the SSZ body."""
    return Bytes(input_bytes + b"\x00")


def invalid_first_ssz_offset(input_bytes: Bytes) -> Bytes:
    """
    Corrupt the first SSZ container offset.

    The stateless input starts with a 2-byte schema id, followed by the
    encoded payload selected by that schema. For Amsterdam schema 0x1501,
    the payload is an SSZ-encoded ``StatelessInput`` container. Its
    first four SSZ bytes encode the offset to the first variable-size field.
    Setting that offset to 1 makes it point inside the fixed-size section,
    so the SSZ decoder must reject the input before stateless validation
    can run.
    """
    return Bytes(input_bytes[:2] + b"\x01\x00\x00\x00" + input_bytes[6:])


@pytest.mark.parametrize(
    "modifier",
    [
        pytest.param(empty_input_bytes, id="empty_input_bytes"),
        pytest.param(incomplete_schema_id, id="incomplete_schema_id"),
        pytest.param(
            unsupported_schema_revision,
            id="unsupported_schema_revision",
        ),
        pytest.param(unsupported_schema_fork, id="unsupported_schema_fork"),
        pytest.param(missing_ssz_body, id="missing_ssz_body"),
        pytest.param(truncated_ssz_body, id="truncated_ssz_body"),
        pytest.param(trailing_garbage, id="trailing_garbage"),
        pytest.param(invalid_first_ssz_offset, id="invalid_first_ssz_offset"),
    ],
)
def test_invalid_stateless_input_bytes_are_rejected(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    modifier: StatelessInputBytesModifier,
) -> None:
    """Invalid stateless input bytes fail guest validation."""
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    tx = Transaction(
        sender=sender,
        to=recipient,
        value=1,
        gas_limit=empty_account_value_transfer_gas_limit(fork),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                stateless_input_bytes_modifier=modifier,
                expected_stateless_validation_success=False,
            )
        ],
        post={
            sender: Account(nonce=1),
            recipient: Account(balance=1),
        },
    )
