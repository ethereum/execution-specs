"""
Raw-RLP decode rejection tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A frame transaction is `0x06 || rlp(payload)`, with the payload laid out
as (EIP-8141 l.66-75):

```
[chain_id, nonce, sender, frames, signatures, fees, blob_versioned_hashes]
frames = [[mode, flags, target, limits, value, data], ...]
limits = [execution, state]
signatures = [[scheme, signer, msg, signature], ...]
fees = [max_fee, max_priority_fee_per_gas]
```

Each case starts from a valid, signed frame transaction, decomposes its
payload into nested RLP items, and changes exactly one thing at the
byte level: it truncates the input, appends bytes, breaks a list
header, gives a list the wrong number of elements, or encodes an
integer or a fixed-width field in a form the payload layout does not
allow. None of these byte strings decodes to a transaction, so each is
rejected before any validation or execution runs.

The malformed bytes cannot be built through the `Transaction` model, so
they are injected through `rlp_override` and filled as transaction
tests only. The transaction test format records the expected verdict
without running the reference implementation, so
`test_raw_rlp_reencoded_frame_transaction` anchors the local encoder:
re-encoding the unmodified payload reproduces the framework's own
encoding byte for byte, so every rejected case differs from a valid
transaction only by its named change.

An undefined frame mode, a reserved flag, a limit above 64 bits and the
other value-level rules are in `test_static_validity.py`.
"""

from copy import deepcopy
from typing import Any, Callable, List, Sequence, Union

import pytest
from execution_testing import (
    Address,
    Alloc,
    Bytes,
    Transaction,
    TransactionException,
    TransactionTestFiller,
)

from .helpers import default_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.inclusion_test,
]

FRAME_TARGET = Address(0x8141)
"""Target of the base transaction's second frame."""

FRAME_DATA = Bytes(b"\x01\x02")
"""Data of the base transaction's second frame."""

# Positions in the payload (l.69-74).
CHAIN_ID, NONCE, SENDER, FRAMES, SIGNATURES, FEES, BLOB_HASHES = range(7)
MODE, FLAGS, TARGET, LIMITS, VALUE, DATA = range(6)
EXECUTION, STATE = range(2)
SCHEME, SIGNER, MSG, SIGNATURE = range(4)
MAX_FEE, MAX_PRIORITY_FEE = range(2)

FRAME_FORMAT = TransactionException.TYPE_6_INVALID_FRAME_FORMAT


class Raw(bytes):
    """An item that is already RLP-encoded, emitted verbatim."""


Item = Union[bytes, Raw, List[Any]]
"""A payload item: a byte string, a pre-encoded item, or a list."""


def encode_header(length: int, offset: int) -> bytes:
    """Encode an RLP header for a payload of the given length."""
    if length < 56:
        return bytes([offset + length])
    size = length.to_bytes((length.bit_length() + 7) // 8, "big")
    return bytes([offset + 55 + len(size)]) + size


def rlp_bytes(payload: bytes) -> bytes:
    """Encode a byte string canonically."""
    if len(payload) == 1 and payload[0] < 0x80:
        return payload
    return encode_header(len(payload), 0x80) + payload


def encode(item: Item) -> bytes:
    """Encode a payload item, emitting `Raw` items as they are."""
    if isinstance(item, Raw):
        return bytes(item)
    if isinstance(item, list):
        payload = b"".join(encode(element) for element in item)
        return encode_header(len(payload), 0xC0) + payload
    return rlp_bytes(item)


def int_payload(value: int) -> bytes:
    """Return the canonical RLP payload of an integer."""
    return value.to_bytes((value.bit_length() + 7) // 8, "big")


def payload_items(element: Any) -> Item:
    """
    Decompose a field of the framework's transaction list into payload
    items: integers become their canonical big-endian bytes.
    """
    if isinstance(element, list):
        return [payload_items(child) for child in element]
    if isinstance(element, bytes):
        return bytes(element)
    return int_payload(int(element))


def signed_base_transaction(pre: Alloc, **overrides: Any) -> Transaction:
    """
    Return the signed base transaction: a `VERIFY` frame approving
    execution and payment through the sender's default code, and a
    `DEFAULT` frame carrying a target and data, so that every field of
    a frame is non-empty in one of the two.
    """
    return Transaction(
        sender=pre.fund_eoa(),
        frames=[
            verify_frame(),
            default_frame(target=FRAME_TARGET, data=FRAME_DATA),
        ],
        **overrides,
    ).with_signature_and_sender()


def base_items(tx: Transaction) -> List[Any]:
    """Decompose a signed frame transaction's payload into items."""
    items = payload_items(tx.to_list(signing=False))
    assert isinstance(items, list)
    return items


def with_type(payload: bytes) -> bytes:
    """Prefix an encoded payload with the frame transaction type."""
    return bytes([Spec.FRAME_TX_TYPE]) + payload


Mutation = Callable[[List[Any]], bytes]
"""Turn the base payload's items into a malformed transaction."""


def replaced(path: Sequence[int], new: Item) -> Mutation:
    """Replace the item at `path`, the whole payload if empty, and encode."""

    def mutate(items: List[Any]) -> bytes:
        if not path:
            return with_type(encode(new))
        items = deepcopy(items)
        parent = items
        for index in path[:-1]:
            parent = parent[index]
        parent[path[-1]] = new
        return with_type(encode(items))

    return mutate


def transformed(
    path: Sequence[int], change: Callable[[Any], Item]
) -> Mutation:
    """Replace the item at `path` by a function of it."""

    def mutate(items: List[Any]) -> bytes:
        old: Any = items
        for index in path:
            old = old[index]
        return replaced(path, change(deepcopy(old)))(items)

    return mutate


def leading_zero(path: Sequence[int]) -> Mutation:
    """
    Prefix an integer's payload with a zero byte. A zero-valued field
    becomes the single byte `0x00` instead of the empty string `0x80`.
    """
    return transformed(path, lambda payload: Raw(rlp_bytes(b"\x00" + payload)))


def dropped_last(path: Sequence[int]) -> Mutation:
    """Remove the last element of the list at `path`."""
    return transformed(path, lambda items: items[:-1])


def appended_empty(path: Sequence[int]) -> Mutation:
    """Append an empty byte string to the list at `path`."""
    return transformed(path, lambda items: items + [b""])


def list_header_off_by(path: Sequence[int], delta: int) -> Mutation:
    """
    Encode the list at `path` with a header declaring `delta` bytes
    more than its payload, keeping every enclosing header consistent
    with the bytes actually present.
    """

    def header(items: List[Any]) -> Raw:
        payload = b"".join(encode(element) for element in items)
        return Raw(encode_header(len(payload) + delta, 0xC0) + payload)

    return transformed(path, header)


def as_byte_string(path: Sequence[int]) -> Mutation:
    """Encode the list at `path` as a byte string of its payload."""

    def string(items: List[Any]) -> Raw:
        payload = b"".join(encode(element) for element in items)
        return Raw(encode_header(len(payload), 0x80) + payload)

    return transformed(path, string)


def truncated_inside(field: int) -> Mutation:
    """
    End the input halfway through the payload's field `field`, under an
    outer header that still declares the complete payload.
    """

    def mutate(items: List[Any]) -> bytes:
        encoded = [encode(element) for element in items]
        complete = b"".join(encoded)
        kept = b"".join(encoded[:field])
        kept += encoded[field][: len(encoded[field]) // 2]
        return with_type(encode_header(len(complete), 0xC0) + kept)

    return mutate


def trailing(suffix: bytes) -> Mutation:
    """Append `suffix` after the complete payload."""
    return lambda items: with_type(encode(items)) + suffix


RAW_RLP_CASES = [
    # Truncated input and broken list headers.
    pytest.param(
        truncated_inside(FRAMES),
        [FRAME_FORMAT, TransactionException.RLP_ERROR_EOF],
        id="truncated_inside_frame_list",
    ),
    pytest.param(
        list_header_off_by([FRAMES], +1),
        [
            FRAME_FORMAT,
            TransactionException.RLP_ERROR_EOF,
            TransactionException.RLP_ERROR_SIZE,
        ],
        id="frame_list_header_declares_more",
    ),
    pytest.param(
        list_header_off_by([FRAMES], -1),
        [
            FRAME_FORMAT,
            TransactionException.RLP_ERROR_EOF,
            TransactionException.RLP_ERROR_SIZE,
        ],
        id="frame_list_header_declares_less",
    ),
    pytest.param(
        list_header_off_by([FRAMES, 1], -1),
        [
            FRAME_FORMAT,
            TransactionException.RLP_ERROR_EOF,
            TransactionException.RLP_ERROR_SIZE,
        ],
        id="frame_header_declares_less",
    ),
    # Bytes after the payload.
    pytest.param(
        trailing(b"\x00"),
        [FRAME_FORMAT, TransactionException.RLP_ERROR_SIZE],
        id="trailing_byte",
    ),
    pytest.param(
        trailing(b"\xc0"),
        [FRAME_FORMAT, TransactionException.RLP_ERROR_SIZE],
        id="trailing_empty_list",
    ),
    # Lists with the wrong number of elements.
    pytest.param(
        dropped_last([]),
        [FRAME_FORMAT, TransactionException.RLP_TOO_FEW_ELEMENTS],
        id="payload_missing_element",
    ),
    pytest.param(
        appended_empty([]),
        [FRAME_FORMAT, TransactionException.RLP_TOO_MANY_ELEMENTS],
        id="payload_extra_element",
    ),
    pytest.param(
        dropped_last([FRAMES, 1]),
        [FRAME_FORMAT, TransactionException.RLP_TOO_FEW_ELEMENTS],
        id="frame_missing_element",
    ),
    pytest.param(
        appended_empty([FRAMES, 1]),
        [FRAME_FORMAT, TransactionException.RLP_TOO_MANY_ELEMENTS],
        id="frame_extra_element",
    ),
    pytest.param(
        dropped_last([FRAMES, 1, LIMITS]),
        [FRAME_FORMAT, TransactionException.RLP_TOO_FEW_ELEMENTS],
        id="limits_missing_element",
    ),
    pytest.param(
        appended_empty([FRAMES, 1, LIMITS]),
        [FRAME_FORMAT, TransactionException.RLP_TOO_MANY_ELEMENTS],
        id="limits_extra_element",
    ),
    pytest.param(
        dropped_last([SIGNATURES, 0]),
        [FRAME_FORMAT, TransactionException.RLP_TOO_FEW_ELEMENTS],
        id="signature_missing_element",
    ),
    pytest.param(
        appended_empty([SIGNATURES, 0]),
        [FRAME_FORMAT, TransactionException.RLP_TOO_MANY_ELEMENTS],
        id="signature_extra_element",
    ),
    pytest.param(
        dropped_last([FEES]),
        [FRAME_FORMAT, TransactionException.RLP_TOO_FEW_ELEMENTS],
        id="fees_missing_element",
    ),
    pytest.param(
        appended_empty([FEES]),
        [FRAME_FORMAT, TransactionException.RLP_TOO_MANY_ELEMENTS],
        id="fees_extra_element",
    ),
    pytest.param(
        as_byte_string([FRAMES, 1]),
        [FRAME_FORMAT, TransactionException.RLP_INVALID_HEADER],
        id="frame_as_byte_string",
    ),
    pytest.param(
        as_byte_string([FRAMES, 1, LIMITS]),
        [FRAME_FORMAT, TransactionException.RLP_INVALID_HEADER],
        id="limits_as_byte_string",
    ),
    # Non-canonical integers: a leading zero byte. The nonce, the frame
    # value and the priority fee are zero in the base transaction, so
    # theirs is the single byte `0x00` instead of `0x80`.
    *(
        pytest.param(
            leading_zero(path),
            [FRAME_FORMAT, *extra],
            id=f"leading_zero_{name}",
        )
        for name, path, extra in [
            ("chain_id", [CHAIN_ID], [TransactionException.INVALID_CHAINID]),
            (
                "nonce",
                [NONCE],
                [TransactionException.RLP_LEADING_ZEROS_NONCE],
            ),
            ("frame_mode", [FRAMES, 0, MODE], []),
            ("frame_flags", [FRAMES, 0, FLAGS], []),
            (
                "frame_execution_limit",
                [FRAMES, 1, LIMITS, EXECUTION],
                [TransactionException.RLP_LEADING_ZEROS_GASLIMIT],
            ),
            (
                "frame_state_limit",
                [FRAMES, 1, LIMITS, STATE],
                [TransactionException.RLP_LEADING_ZEROS_GASLIMIT],
            ),
            (
                "frame_value",
                [FRAMES, 1, VALUE],
                [TransactionException.RLP_LEADING_ZEROS_VALUE],
            ),
            ("signature_scheme", [SIGNATURES, 0, SCHEME], []),
            (
                "max_fee",
                [FEES, MAX_FEE],
                [TransactionException.RLP_LEADING_ZEROS_GASPRICE],
            ),
            (
                "max_priority_fee",
                [FEES, MAX_PRIORITY_FEE],
                [TransactionException.RLP_LEADING_ZEROS_PRIORITY_FEE],
            ),
        ]
    ),
    pytest.param(
        # The frame mode `1` as a one-byte string, `0x8101`, where RLP
        # encodes a single byte below `0x80` as itself.
        replaced([FRAMES, 0, MODE], Raw(b"\x81\x01")),
        [FRAME_FORMAT],
        id="frame_mode_single_byte_as_string",
    ),
    # Integers wider than their field.
    pytest.param(
        # `assert frame.value < 2**256` (l.176).
        replaced([FRAMES, 1, VALUE], int_payload(2**256)),
        [FRAME_FORMAT, TransactionException.VALUE_OVERFLOW],
        id="frame_value_above_256_bits",
    ),
    pytest.param(
        replaced([NONCE], int_payload(2**256)),
        [
            FRAME_FORMAT,
            TransactionException.NONCE_OVERFLOW,
            TransactionException.NONCE_IS_MAX,
        ],
        id="nonce_above_256_bits",
    ),
    # Fixed-width byte fields of the wrong width.
    *(
        pytest.param(
            transformed(path, change),
            [FRAME_FORMAT],
            id=name,
        )
        for name, path, change in [
            # `assert len(tx.sender) == 20` (l.151).
            ("sender_19_bytes", [SENDER], lambda b: b[1:]),
            ("sender_21_bytes", [SENDER], lambda b: b"\x00" + b),
            # `frame.target is None or len(frame.target) == 20` (l.175).
            ("frame_target_19_bytes", [FRAMES, 1, TARGET], lambda b: b[1:]),
            (
                "frame_target_21_bytes",
                [FRAMES, 1, TARGET],
                lambda b: b"\x00" + b,
            ),
        ]
    ),
]
"""
Byte-level malformations of the base transaction, each with the
exceptions a client may report: the frame format error, or the RLP
decoding error its decoder raises first.
"""


def test_raw_rlp_reencoded_frame_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
) -> None:
    """
    Re-encode the base transaction's payload with the local encoder and
    check it reproduces the framework's encoding byte for byte, so the
    rejected cases differ from this valid transaction only by their
    named change. The transaction is accepted.
    """
    tx = signed_base_transaction(pre)
    assert with_type(encode(base_items(tx))) == bytes(tx.rlp())
    transaction_test(pre=pre, tx=tx)


@pytest.mark.exception_test
@pytest.mark.parametrize("mutation,error", RAW_RLP_CASES)
def test_raw_rlp_decode_rejections(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    mutation: Mutation,
    error: List[TransactionException],
) -> None:
    """
    Reject frame transactions whose bytes do not decode to the payload
    layout of EIP-8141 l.66-75: input that ends inside the frame list,
    bytes after the payload, list headers that disagree with their
    content, lists with the wrong number of elements or encoded as byte
    strings, integers with leading zero bytes or wider than 256 bits,
    and addresses that are not 20 bytes (l.151, l.175).
    """
    tx = signed_base_transaction(pre, error=error)
    raw = mutation(base_items(tx))
    assert raw != bytes(tx.rlp())
    tx.rlp_override = Bytes(raw)
    transaction_test(pre=pre, tx=tx)
