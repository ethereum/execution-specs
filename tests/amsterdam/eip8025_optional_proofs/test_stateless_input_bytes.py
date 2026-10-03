"""Stateless input byte validation tests."""

from dataclasses import replace

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

from ethereum.forks.amsterdam.stateless import (
    MAX_BYTES_PER_HEADER,
    StatelessInput,
)

from .gas_helpers import empty_account_value_transfer_gas_limit
from .spec import ref_spec_8025
from .stateless_input_helpers import (
    StatelessInputBytesModifier,
    modify_stateless_input,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = ref_spec_8025.git_path
REFERENCE_SPEC_VERSION = ref_spec_8025.version


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
    """
    End the SSZ body where the witness field should begin.

    Dropping only the final byte would shorten the last witness header,
    which is still valid SSZ, so cut off the whole witness instead.
    """
    # The second top-level offset, after the schema id and the payload
    # request offset, points at the witness.
    witness_offset = int.from_bytes(input_bytes[6:10], "little")
    return Bytes(input_bytes[: 2 + witness_offset])


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


def shifted_ssz_offsets(input_bytes: Bytes) -> Bytes:
    """Shift every top-level offset and leave an extra byte at the end."""
    encoded = bytearray(input_bytes)
    for offset in (2, 6):
        value = int.from_bytes(encoded[offset : offset + 4], "little")
        encoded[offset : offset + 4] = (value + 1).to_bytes(4, "little")
    encoded.append(0xFF)
    return Bytes(bytes(encoded))


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
        pytest.param(invalid_first_ssz_offset, id="invalid_first_ssz_offset"),
        pytest.param(shifted_ssz_offsets, id="shifted_ssz_offsets"),
    ],
)
def test_invalid_stateless_input_bytes_are_rejected(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    modifier: StatelessInputBytesModifier,
) -> None:
    """Stateless input bytes that fail to decode are rejected."""
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
                expected_stateless_input_decode_failure=True,
            )
        ],
        post={
            sender: Account(nonce=1),
            recipient: Account(balance=1),
        },
    )


def pad_last_witness_header(
    bytes_over_limit: int,
) -> StatelessInputBytesModifier:
    """Pad the last witness header to its SSZ size limit, plus extra bytes."""

    def pad_to_limit(stateless_input: StatelessInput) -> StatelessInput:
        witness = stateless_input.witness
        *headers, last_header = witness.headers
        padding = b"\x00" * (MAX_BYTES_PER_HEADER - len(last_header))
        return replace(
            stateless_input,
            witness=replace(
                witness,
                headers=(*headers, last_header + padding),
            ),
        )

    padded_to_limit = modify_stateless_input(pad_to_limit)

    def modifier(input_bytes: Bytes) -> Bytes:
        # Serialization refuses an oversized header, but the headers are the
        # last SSZ field, so appended bytes extend the last header.
        return Bytes(padded_to_limit(input_bytes) + b"\x00" * bytes_over_limit)

    return modifier


@pytest.mark.parametrize(
    "bytes_over_limit,decoding_fails",
    [
        pytest.param(0, False, id="at_size_limit"),
        pytest.param(1, True, id="over_size_limit"),
    ],
)
def test_witness_header_ssz_size_limit(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    bytes_over_limit: int,
    decoding_fails: bool,
) -> None:
    """
    A witness header over its SSZ size limit fails to decode.

    At the limit the input decodes, and validation fails only because the
    padded header has trailing RLP bytes.
    """
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
                stateless_input_bytes_modifier=pad_last_witness_header(
                    bytes_over_limit
                ),
                expected_stateless_validation_success=False,
                expected_stateless_input_decode_failure=decoding_fails,
            )
        ],
        post={
            sender: Account(nonce=1),
            recipient: Account(balance=1),
        },
    )
