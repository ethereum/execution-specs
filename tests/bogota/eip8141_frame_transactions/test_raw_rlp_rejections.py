"""
Raw-RLP decode rejection tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A frame transaction is `0x06 || rlp(payload)`, with the payload laid out
as (§Payload Encoding):

```
[chain_id, nonce, sender, frames, signatures, fees, blob_versioned_hashes]
frames = [[mode, flags, target, limits, value, data], ...]
limits = [execution, state]
signatures = [[scheme, signer, msg, signature], ...]
fees = [max_fee, max_priority_fee_per_gas]
```

Each case starts from a valid frame transaction, decomposes its payload
into nested RLP items, and changes exactly one thing at the byte level:
it truncates the input, appends bytes, breaks a list header, gives a list
the wrong number of elements, encodes a list as a byte string or a byte
string as a list, encodes an integer or a byte string non-canonically,
or gives a fixed-width field the wrong width. None of these byte strings
decodes to a transaction of this layout, so each is rejected before any
validation or execution runs.

A few cases change a value rather than its encoding: a chain ID, a frame
value or a nonce wider than its field, and a blob versioned hash that
is not 32 bytes long (§Constraints: "assert len(h) == 32 and h[0] ==
VERSIONED_HASH_VERSION_KZG"). Wherever the EIP lets a client decode the
value and reject it afterwards, that rule's exception is accepted too.

The base transaction is built so that no other rule can reject a case
for a decoder that reads a malformed field leniently, as some other
valid value. Its sender is a contract, so it carries no signature entry
whose signer a different sender or target could mismatch; its only
entry is an `ARBITRARY` one, which the protocol does not verify; and the
value sits on a `SENDER` frame, the only mode allowed to carry value.
Any 20-byte sender or target passes the static rules, so whatever
address a lenient decoder reads, the transaction it decodes is valid and
the case still expects it to be rejected.

Where possible, the lenient reading is the base transaction itself:
left-padding the 19-byte or 1-byte frame target, dropping the extra
leading zero byte of a 21-byte sender or frame target, reducing the
frame value modulo `2**256`, or keeping the last 32 bytes of the 33-byte
blob versioned hash. Other readings decode a different address: the
sender is derived from a hash and has no leading zero byte, so
left-padding `sender_19_bytes` does not restore it, and keeping the
first 20 bytes of a 21-byte field shifts the address by one byte.

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
    FrameSignature,
    Hash,
    Transaction,
    TransactionException,
    TransactionTestFiller,
)

from .helpers import APPROVE_ALL, sender_frame, verify_frame
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.inclusion_test,
]

FRAME_TARGET = Address(0x41)
"""
Target of the base transaction's second frame. All its bytes but the
last are zero, so a 1-byte or 19-byte target reads back as this address
when a decoder pads it on the left, and a 21-byte one when a decoder
drops its leading byte.
"""

FRAME_VALUE = 1
"""Value of the base transaction's second frame, a `SENDER` frame."""

FRAME_DATA = Bytes(b"\x01\x02")
"""Data of the base transaction's second frame."""

ARBITRARY_SIGNATURE = Bytes(b"\xab" * 5)
"""Raw bytes of the base transaction's only signature entry."""

BLOB_HASH = Hash(bytes([1]) + bytes(31))
"""The base transaction's only blob versioned hash, of version 1."""

# Positions in the payload (§Payload Encoding).
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


def base_transaction(pre: Alloc, **overrides: Any) -> Transaction:
    """
    Return the base transaction, sent by a contract that approves
    execution and payment: a `VERIFY` frame running the sender's code,
    a `SENDER` frame carrying a target, a value and data, an `ARBITRARY`
    signature entry with raw bytes, and one blob versioned hash, so that
    every field of the payload is present and every frame field is
    non-empty in one of the two frames.
    """
    sender = pre.deploy_contract(code=APPROVE_ALL, balance=10**18)
    return Transaction(
        sender=sender,
        nonce=1,
        frames=[
            verify_frame(),
            sender_frame(
                target=FRAME_TARGET, value=FRAME_VALUE, data=FRAME_DATA
            ),
        ],
        signatures=[
            FrameSignature(
                scheme=Spec.SCHEME_ARBITRARY, signature=ARBITRARY_SIGNATURE
            )
        ],
        blob_versioned_hashes=[BLOB_HASH],
        **overrides,
    ).with_signature_and_sender()


def base_items(tx: Transaction) -> List[Any]:
    """Decompose a frame transaction's payload into items."""
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


def as_list(path: Sequence[int]) -> Mutation:
    """Wrap the byte string at `path` in a one-element list."""
    return transformed(path, lambda string: [string])


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


def typed(payload: bytes) -> Mutation:
    """Replace the whole transaction with the type byte and `payload`."""
    return lambda _items: with_type(payload)


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
    # No payload, or an empty one.
    pytest.param(
        typed(b""),
        [FRAME_FORMAT, TransactionException.RLP_ERROR_EOF],
        id="type_byte_only",
    ),
    pytest.param(
        typed(b"\xc0"),
        [FRAME_FORMAT, TransactionException.RLP_TOO_FEW_ELEMENTS],
        id="empty_payload_list",
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
    # Lists encoded as byte strings.
    *(
        pytest.param(
            as_byte_string(path),
            [FRAME_FORMAT, TransactionException.RLP_INVALID_HEADER],
            id=f"{name}_as_byte_string",
        )
        for name, path in [
            ("payload", []),
            ("frame_list", [FRAMES]),
            ("frame", [FRAMES, 1]),
            ("limits", [FRAMES, 1, LIMITS]),
            ("signature_list", [SIGNATURES]),
            ("signature", [SIGNATURES, 0]),
            ("fees", [FEES]),
            ("blob_hash_list", [BLOB_HASHES]),
        ]
    ),
    # Byte strings and integers encoded as lists.
    *(
        pytest.param(
            as_list(path),
            [FRAME_FORMAT, TransactionException.RLP_INVALID_HEADER],
            id=f"{name}_as_list",
        )
        for name, path in [
            ("sender", [SENDER]),
            ("frame_mode", [FRAMES, 1, MODE]),
            ("frame_target", [FRAMES, 1, TARGET]),
            ("frame_value", [FRAMES, 1, VALUE]),
            ("frame_data", [FRAMES, 1, DATA]),
            ("signature_signer", [SIGNATURES, 0, SIGNER]),
            ("signature_msg", [SIGNATURES, 0, MSG]),
            ("blob_hash", [BLOB_HASHES, 0]),
        ]
    ),
    # Non-canonical integers: a leading zero byte. The priority fee and
    # the `ARBITRARY` scheme are zero in the base transaction, so theirs
    # is the single byte `0x00` instead of `0x80`.
    *(
        pytest.param(
            leading_zero(path),
            [FRAME_FORMAT, *extra],
            id=f"leading_zero_{name}",
        )
        for name, path, extra in [
            ("chain_id", [CHAIN_ID], []),
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
    # Non-canonical byte strings.
    pytest.param(
        # The frame mode `1` as a one-byte string, `0x8101`, where RLP
        # encodes a single byte below `0x80` as itself.
        replaced([FRAMES, 0, MODE], Raw(b"\x81\x01")),
        [FRAME_FORMAT],
        id="frame_mode_single_byte_as_string",
    ),
    pytest.param(
        # The frame data replaced by the single byte `0x01`, encoded as
        # the one-byte string `0x8101` instead of as itself.
        replaced([FRAMES, 1, DATA], Raw(b"\x81\x01")),
        [FRAME_FORMAT],
        id="frame_data_single_byte_as_string",
    ),
    pytest.param(
        # The two bytes of frame data under a long-form header, which
        # RLP reserves for strings of 56 bytes or more.
        replaced(
            [FRAMES, 1, DATA],
            Raw(bytes([0xB7 + 1, len(FRAME_DATA)]) + bytes(FRAME_DATA)),
        ),
        [FRAME_FORMAT],
        id="frame_data_long_header_for_short_string",
    ),
    # Integers wider than their field.
    pytest.param(
        # The EIP bounds the chain ID by 2**256 only (§Constraints:
        # "assert tx.chain_id < 2**256"), so a client may decode 2**64
        # and reject it as another chain's.
        replaced([CHAIN_ID], int_payload(2**64)),
        [FRAME_FORMAT, TransactionException.INVALID_CHAINID],
        id="chain_id_2_pow_64",
    ),
    pytest.param(
        replaced([CHAIN_ID], int_payload(2**256)),
        [FRAME_FORMAT],
        id="chain_id_2_pow_256",
    ),
    pytest.param(
        # §Constraints: "assert frame.value < 2**256". The value sits on
        # the `SENDER` frame, which may carry value; reduced modulo
        # 2**256 it reads back as the base transaction's value.
        replaced([FRAMES, 1, VALUE], int_payload(2**256 + FRAME_VALUE)),
        [FRAME_FORMAT, TransactionException.VALUE_OVERFLOW],
        id="sender_frame_value_above_256_bits",
    ),
    pytest.param(
        # Above the nonce bound of §Constraints ("assert tx.nonce <
        # 2**64") as well as the width of any integer field.
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
            [FRAME_FORMAT, *extra],
            id=name,
        )
        for name, path, change, extra in [
            # §Constraints: "assert len(tx.sender) == 20".
            ("sender_empty", [SENDER], lambda _b: b"", []),
            ("sender_19_bytes", [SENDER], lambda b: b[1:], []),
            ("sender_21_bytes", [SENDER], lambda b: b"\x00" + b, []),
            # §Constraints: "assert frame.target is None or
            # len(frame.target) == 20".
            ("frame_target_1_byte", [FRAMES, 1, TARGET], lambda b: b[-1:], []),
            (
                "frame_target_19_bytes",
                [FRAMES, 1, TARGET],
                lambda b: b[1:],
                [],
            ),
            (
                "frame_target_21_bytes",
                [FRAMES, 1, TARGET],
                lambda b: b"\x00" + b,
                [],
            ),
            # §Constraints: "assert len(h) == 32 and h[0] ==
            # VERSIONED_HASH_VERSION_KZG".
            (
                # A decoder padding it on the left reads version 0,
                # which the same assert rejects.
                "blob_hash_31_bytes",
                [BLOB_HASHES, 0],
                lambda b: b[:-1],
                [TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH],
            ),
            (
                # A decoder keeping the last 32 bytes reads the base
                # transaction's hash.
                "blob_hash_33_bytes",
                [BLOB_HASHES, 0],
                lambda b: b"\x00" + b,
                [TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH],
            ),
        ]
    ),
]
"""
Byte-level malformations of the base transaction, each with the
exceptions a client may report: the frame format error, the RLP
decoding error its decoder raises first, or the error of the value rule
a decoded field breaks.
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
    tx = base_transaction(pre)
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
    layout of §Payload Encoding: input that is missing or ends early,
    bytes after the payload, list headers that disagree with their
    content, lists with the wrong number of elements, lists and byte
    strings encoded as each other, integers with leading zero bytes and
    byte strings with non-canonical headers, integers wider than their
    field, and addresses and blob versioned hashes of the wrong width.

    EIP-8141 §Payload Encoding: "The payload is defined as the RLP
    serialization of the following: [chain_id, nonce, sender, frames,
    signatures, fees, blob_versioned_hashes]".
    """
    tx = base_transaction(pre, error=error)
    raw = mutation(base_items(tx))
    assert raw != bytes(tx.rlp())
    tx.rlp_override = Bytes(raw)
    transaction_test(pre=pre, tx=tx)
