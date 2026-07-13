"""Tests for RLP-level validity of type-0 transaction encodings."""

from typing import Dict, List, Mapping

import pytest
from execution_testing import (
    Alloc,
    Bytes,
    Fork,
    Transaction,
    TransactionException,
    TransactionTestFiller,
)

pytestmark = pytest.mark.valid_from("Frontier")

LEGACY_TX_TESTS = (
    "https://github.com/ethereum/tests/blob/"
    "c67e485ff8b5be9abc8ad15345ec21aa22e290d9/src/TransactionTestsFiller"
)


def encode_header(length: int, offset: int) -> bytes:
    """Encode an RLP header for a payload of the given length."""
    if length < 56:
        return bytes([offset + length])
    size = length.to_bytes((length.bit_length() + 7) // 8, "big")
    return bytes([offset + 55 + len(size)]) + size


def rlp_bytes(payload: bytes) -> bytes:
    """Encode a byte string."""
    if len(payload) == 1 and payload[0] < 0x80:
        return payload
    return encode_header(len(payload), 0x80) + payload


def rlp_list(items: List[bytes]) -> bytes:
    """Encode a list of already-encoded items."""
    payload = b"".join(items)
    return encode_header(len(payload), 0xC0) + payload


def int_payload(value: int) -> bytes:
    """Return the canonical RLP payload of an integer."""
    if value == 0:
        return b""
    return value.to_bytes((value.bit_length() + 7) // 8, "big")


def tx_fields(tx: Transaction) -> Dict[str, bytes]:
    """
    Decompose a signed transaction into its canonical RLP payload per
    field, using the framework's own field order and values.
    """
    return {
        name: bytes(el) if isinstance(el, bytes) else int_payload(int(el))
        for name, el in zip(
            tx.get_rlp_fields(),
            tx.to_list(signing=False),
            strict=True,
        )
    }


def signed_tx(
    pre: Alloc, fork: Fork, nonce: int = 0, data: bytes = b""
) -> Transaction:
    """Build and sign the base type-0 transaction."""
    return Transaction(
        sender=pre.fund_eoa(),
        to=pre.fund_eoa(amount=0),
        nonce=nonce,
        gas_price=10,
        gas_limit=30_000,
        value=1,
        data=data,
        protected=fork.supports_protected_txs(),
    ).with_signature_and_sender()


def signed_tx_fields(
    pre: Alloc, fork: Fork, nonce: int = 0, data: bytes = b""
) -> Dict[str, bytes]:
    """Build a signed type-0 transaction and decompose it."""
    return tx_fields(signed_tx(pre, fork, nonce=nonce, data=data))


def encode_tx(
    fields: Mapping[str, bytes], override: Mapping[str, bytes] | None = None
) -> bytes:
    """
    Encode the transaction fields, allowing per-field pre-encoded
    replacements.
    """
    override = override or {}
    return rlp_list(
        [override.get(name, rlp_bytes(fields[name])) for name in fields]
    )


def invalid_tx(
    pre: Alloc,
    rlp: bytes,
    error: TransactionException | list[TransactionException],
) -> Transaction:
    """Return a transaction whose serialization is the given raw bytes."""
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=0,
        gas_price=10,
        gas_limit=30_000,
        error=error,
    )
    tx.rlp_override = Bytes(rlp)
    return tx


def test_valid_reencoded_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify the local field encoder reproduces the framework encoding
    byte for byte, anchoring the malformation tests to a valid baseline.
    """
    tx = signed_tx(pre, fork)
    fields = tx_fields(tx)
    assert encode_tx(fields) == bytes(tx.rlp())
    transaction_test(pre=pre, tx=tx)


@pytest.mark.ported_from(
    [
        f"{LEGACY_TX_TESTS}/ttWrongRLP/RLPNonceWithFirstZerosCopier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/RLPgasPriceWithFirstZerosCopier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/RLPgasLimitWithFirstZerosCopier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/RLPValueWithFirstZerosCopier.json",
        f"{LEGACY_TX_TESTS}/ttRSValue/TransactionWithRvaluePrefixed00Filler.json",
        f"{LEGACY_TX_TESTS}/ttRSValue/TransactionWithSvaluePrefixed00Filler.json",
        f"{LEGACY_TX_TESTS}/ttRSValue/RightVRSTestVPrefixedBy0Filler.json",
        f"{LEGACY_TX_TESTS}/ttNonce/TransactionWithLeadingZerosNonceFiller.json",
        f"{LEGACY_TX_TESTS}/ttNonce/TransactionWithZerosBigIntFiller.json",
        f"{LEGACY_TX_TESTS}/ttGasPrice/"
        "TransactionWithLeadingZerosGasPriceFiller.json",
        f"{LEGACY_TX_TESTS}/ttGasLimit/"
        "TransactionWithLeadingZerosGasLimitFiller.json",
        f"{LEGACY_TX_TESTS}/ttValue/TransactionWithLeadingZerosValueFiller.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_gasLimit_Prefixed0000Copier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_rvalue_Prefixed0000Copier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_svalue_Prefixed0000Copier.json",
    ],
)
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "field, error",
    [
        ("nonce", TransactionException.RLP_LEADING_ZEROS_NONCE),
        ("gas_price", TransactionException.RLP_LEADING_ZEROS_GASPRICE),
        ("gas_limit", TransactionException.RLP_LEADING_ZEROS_GASLIMIT),
        ("value", TransactionException.RLP_LEADING_ZEROS_VALUE),
        ("v", TransactionException.RLP_LEADING_ZEROS_V),
        ("r", TransactionException.RLP_LEADING_ZEROS_R),
        ("s", TransactionException.RLP_LEADING_ZEROS_S),
    ],
)
def test_field_leading_zeros(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
    field: str,
    error: TransactionException,
) -> None:
    """
    Prefix one integer field's payload with a zero byte; the
    non-canonical encoding must be rejected. The base nonce is zero, so
    its variant is the classic zero-encoded-as-0x00 case.
    """
    fields = signed_tx_fields(pre, fork)
    corrupted = rlp_bytes(b"\x00" + fields[field])
    rlp = encode_tx(fields, {field: corrupted})
    transaction_test(pre=pre, tx=invalid_tx(pre, rlp, error))


@pytest.mark.ported_from(
    [
        f"{LEGACY_TX_TESTS}/ttWrongRLP/RLPIncorrectByteEncoding00Copier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/RLPIncorrectByteEncoding01Copier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/RLPIncorrectByteEncoding127Copier.json",
    ],
)
@pytest.mark.exception_test
def test_non_canonical_single_byte(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Encode the single-byte nonce payload behind a one-byte string
    header (0x8101) instead of as the byte itself; the non-canonical
    encoding must be rejected.
    """
    fields = signed_tx_fields(pre, fork, nonce=1)
    payload = fields["nonce"]
    assert len(payload) == 1 and payload[0] < 0x80
    rlp = encode_tx(fields, {"nonce": b"\x81" + payload})
    transaction_test(
        pre=pre,
        tx=invalid_tx(
            pre, rlp, TransactionException.RLP_LEADING_ZEROS_NONCE_SIZE
        ),
    )


@pytest.mark.ported_from(
    [
        f"{LEGACY_TX_TESTS}/ttWrongRLP/"
        "RLPArrayLengthWithFirstZerosCopier.json",
    ],
)
@pytest.mark.exception_test
def test_data_size_leading_zeros(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Encode the size of the data field's long-form string header with a
    leading zero byte; the non-canonical encoding must be rejected.
    """
    fields = signed_tx_fields(pre, fork, data=b"\xff" * 64)
    payload = fields["data"]
    # The corruption assumes the long-form string header.
    assert len(payload) >= 56
    size = len(payload).to_bytes(2, "big")
    assert size[0] == 0
    corrupted = bytes([0x80 + 55 + len(size)]) + size + payload
    rlp = encode_tx(fields, {"data": corrupted})
    transaction_test(
        pre=pre,
        tx=invalid_tx(
            pre, rlp, TransactionException.RLP_LEADING_ZEROS_DATA_SIZE
        ),
    )


@pytest.mark.ported_from(
    [
        f"{LEGACY_TX_TESTS}/ttNonce/TransactionWithNonceOverflowFiller.json",
        f"{LEGACY_TX_TESTS}/ttValue/TransactionWithHighValueOverflowFiller.json",
        f"{LEGACY_TX_TESTS}/ttRSValue/TransactionWithRvalueOverflowFiller.json",
        f"{LEGACY_TX_TESTS}/ttRSValue/TransactionWithSvalueOverflowFiller.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_rvalue_TooLargeCopier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_svalue_TooLargeCopier.json",
    ],
)
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "field, error",
    [
        ("nonce", TransactionException.RLP_INVALID_NONCE),
        ("value", TransactionException.VALUE_OVERFLOW),
        ("r", TransactionException.RLP_INVALID_SIGNATURE_R),
        ("s", TransactionException.RLP_INVALID_SIGNATURE_S),
    ],
)
def test_field_overflow(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
    field: str,
    error: TransactionException,
) -> None:
    """
    Encode one integer field as a 33-byte value (2**256), exceeding the
    256-bit width of the field. The spec decodes the nonce as a 256-bit
    scalar as well; its 64-bit bound is a validation rule (EIP-2681),
    not a decoding one, and clients that store the nonce in 64 bits
    reject the oversized encoding all the same.

    The gas limit and gas price are unbounded scalars in the spec, so
    oversized values there are not a decoding error and are rejected
    only in block context. The signature v is also a bounded 256-bit
    field, but has no field-specific decoding exception, so its
    oversized encoding is not covered here.
    """
    fields = signed_tx_fields(pre, fork)
    corrupted = rlp_bytes(int_payload(2**256))
    rlp = encode_tx(fields, {field: corrupted})
    transaction_test(pre=pre, tx=invalid_tx(pre, rlp, error))


@pytest.mark.ported_from(
    [
        f"{LEGACY_TX_TESTS}/ttWrongRLP/RLPAddressWrongSizeCopier.json",
        f"{LEGACY_TX_TESTS}/ttAddress/AddressLessThan20Filler.json",
        f"{LEGACY_TX_TESTS}/ttAddress/AddressMoreThan20PrefixedBy0Filler.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/RLPAddressWithFirstZerosCopier.json",
        f"{LEGACY_TX_TESTS}/ttAddress/AddressMoreThan20Filler.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_to_Prefixed0000Copier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_to_TooLargeCopier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_to_TooShortCopier.json",
    ],
)
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "size, error",
    [
        (19, TransactionException.ADDRESS_TOO_SHORT),
        (21, TransactionException.ADDRESS_TOO_LONG),
    ],
)
def test_to_address_size(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
    size: int,
    error: TransactionException,
) -> None:
    """
    Encode the to field with a truncated 19-byte address or a 21-byte
    address made of a zero byte prefixing a valid address.
    """
    fields = signed_tx_fields(pre, fork)
    if size < 20:
        fields["to"] = fields["to"][:size]
    else:
        fields["to"] = fields["to"].rjust(size, b"\x00")
    rlp = encode_tx(fields)
    transaction_test(pre=pre, tx=invalid_tx(pre, rlp, error))


@pytest.mark.ported_from(
    [
        f"{LEGACY_TX_TESTS}/ttWrongRLP/"
        "RLPElementIsListWhenItShouldntBeCopier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/"
        "RLPElementIsListWhenItShouldntBe2Copier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_rvalue_GivenAsListCopier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_svalue_GivenAsListCopier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_data_GivenAsListCopier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_gasLimit_GivenAsListCopier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_to_GivenAsListCopier.json",
    ],
)
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "field, error",
    [
        ("nonce", TransactionException.RLP_INVALID_NONCE),
        ("gas_limit", TransactionException.RLP_INVALID_GASLIMIT),
        ("to", TransactionException.RLP_INVALID_TO),
        ("value", TransactionException.RLP_INVALID_VALUE),
        ("data", TransactionException.RLP_INVALID_DATA),
        ("r", TransactionException.RLP_INVALID_SIGNATURE_R),
        ("s", TransactionException.RLP_INVALID_SIGNATURE_S),
    ],
)
def test_field_as_list(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
    field: str,
    error: TransactionException,
) -> None:
    """
    Encode one field as an RLP list instead of a byte string.

    The gas price and v fields are equally rejected but have no
    field-specific decoding exception, so they are not covered.
    """
    fields = signed_tx_fields(pre, fork)
    corrupted = rlp_list([rlp_bytes(fields[field])])
    rlp = encode_tx(fields, {field: corrupted})
    transaction_test(pre=pre, tx=invalid_tx(pre, rlp, error))


@pytest.mark.ported_from(
    [
        f"{LEGACY_TX_TESTS}/ttWrongRLP/RLPExtraRandomByteAtTheEndCopier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_HeaderLargerThanRLP_0Copier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/TRANSCT_HeaderGivenAsArray_0Copier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/RLPListLengthWithFirstZerosCopier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/aMaliciousRLPCopier.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/RLPTransactionGivenAsArrayCopier.json",
    ],
)
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "mutation, error",
    [
        ("truncated", TransactionException.RLP_ERROR_EOF),
        ("extra_byte", TransactionException.RLP_ERROR_SIZE),
        ("too_few_elements", TransactionException.RLP_TOO_FEW_ELEMENTS),
        ("too_many_elements", TransactionException.RLP_TOO_MANY_ELEMENTS),
        ("header_declares_more", TransactionException.RLP_ERROR_EOF),
        (
            "header_declares_less",
            [
                TransactionException.RLP_ERROR_EOF,
                TransactionException.RLP_ERROR_SIZE,
            ],
        ),
        ("tx_as_byte_string", TransactionException.RLP_INVALID_HEADER),
        (
            "list_size_leading_zeros",
            TransactionException.RLP_ERROR_SIZE_LEADING_ZEROS,
        ),
    ],
)
def test_invalid_structure(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
    mutation: str,
    error: TransactionException | list[TransactionException],
) -> None:
    """
    Corrupt the RLP structure of the whole transaction.

    A list header that declares less than the actual payload leaves
    both a truncated final field and a trailing byte at the top level,
    so clients report it as either an EOF or a size error.
    """
    fields = signed_tx_fields(pre, fork)
    items = [rlp_bytes(fields[name]) for name in fields]
    payload = b"".join(items)
    # The header mutations assume the long-form list header.
    assert len(payload) >= 56
    good = encode_tx(fields)
    if mutation == "truncated":
        rlp = good[:-1]
    elif mutation == "extra_byte":
        rlp = good + b"\x00"
    elif mutation == "too_few_elements":
        rlp = rlp_list(items[:-1])
    elif mutation == "too_many_elements":
        rlp = rlp_list(items + [rlp_bytes(b"")])
    elif mutation == "header_declares_more":
        rlp = encode_header(len(payload) + 1, 0xC0) + payload
    elif mutation == "header_declares_less":
        rlp = encode_header(len(payload) - 1, 0xC0) + payload
    elif mutation == "tx_as_byte_string":
        rlp = encode_header(len(payload), 0x80) + payload
    elif mutation == "list_size_leading_zeros":
        size = len(payload).to_bytes(2, "big")
        assert size[0] == 0
        rlp = bytes([0xC0 + 55 + len(size)]) + size + payload
    transaction_test(pre=pre, tx=invalid_tx(pre, rlp, error))


@pytest.mark.ported_from(
    [
        f"{LEGACY_TX_TESTS}/ttRSValue/TransactionWithRvalue0Filler.json",
        f"{LEGACY_TX_TESTS}/ttRSValue/TransactionWithSvalue0Filler.json",
        f"{LEGACY_TX_TESTS}/ttVValue/V_wrongvalue_ffFiller.json",
        f"{LEGACY_TX_TESTS}/ttWrongRLP/tr201506052141PYTHONCopier.json",
    ],
)
@pytest.mark.exception_test
@pytest.mark.parametrize(
    "field, payload, error",
    [
        ("r", b"", TransactionException.INVALID_SIGNATURE_VRS),
        ("s", b"", TransactionException.INVALID_SIGNATURE_VRS),
        (
            "v",
            b"",
            [
                TransactionException.INVALID_SIGNATURE_VRS,
                TransactionException.INVALID_CHAINID,
            ],
        ),
        (
            "v",
            b"\x1d",
            [
                TransactionException.INVALID_SIGNATURE_VRS,
                TransactionException.INVALID_CHAINID,
            ],
        ),
        (
            "v",
            b"\xff",
            [
                TransactionException.INVALID_SIGNATURE_VRS,
                TransactionException.INVALID_CHAINID,
            ],
        ),
    ],
    ids=["r_zero", "s_zero", "v_zero", "v_29", "v_255"],
)
def test_invalid_signature_values(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    fork: Fork,
    field: str,
    payload: bytes,
    error: TransactionException | list[TransactionException],
) -> None:
    """
    Replace a signature field with a well-encoded but invalid value:
    zero r or s, or a v that is neither 27, 28 nor an EIP-155 value.

    Before EIP-155 any v other than 27 or 28 is a plain invalid v;
    afterwards clients may instead derive a chain id from the invalid
    v and reject the transaction for the chain id mismatch.
    """
    fields = signed_tx_fields(pre, fork)
    fields[field] = payload
    rlp = encode_tx(fields)
    transaction_test(pre=pre, tx=invalid_tx(pre, rlp, error))
