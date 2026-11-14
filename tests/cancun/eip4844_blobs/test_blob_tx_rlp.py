"""
Tests RLP-level validity of blob transaction encodings from EIP-4844.

Tests type-3 transactions whose fields are encoded with more bytes than
the field can hold, from
[EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844).
"""

from typing import Any, Dict, List

import ethereum_rlp as eth_rlp
import pytest
from ethereum_types.numeric import Uint
from execution_testing import (
    Alloc,
    Bytes,
    Hash,
    Transaction,
    TransactionException,
    TransactionTestFiller,
    add_kzg_version,
)

from .spec import Spec, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version

pytestmark = [
    pytest.mark.valid_from("Cancun"),
    pytest.mark.inclusion_test,
]


def signed_blob_tx(pre: Alloc) -> Transaction:
    """Build and sign the base blob transaction."""
    return Transaction(
        ty=Spec.BLOB_TX_TYPE,
        sender=pre.fund_eoa(amount=0),
        to=pre.fund_eoa(amount=0),
        gas_limit=21_000,
        max_fee_per_gas=10,
        max_priority_fee_per_gas=1,
        max_fee_per_blob_gas=10,
        access_list=[],
        blob_versioned_hashes=add_kzg_version(
            [Hash(1)], Spec.BLOB_COMMITMENT_VERSION_KZG
        ),
    ).with_signature_and_sender()


def blob_tx_fields(tx: Transaction) -> Dict[str, Any]:
    """Return the RLP fields of a transaction by name, in encoding order."""
    return dict(
        zip(tx.get_rlp_fields(), tx.to_list(signing=False), strict=True)
    )


def encode_blob_tx(fields: Dict[str, Any]) -> bytes:
    """Encode blob transaction fields as a typed transaction."""
    return bytes([Spec.BLOB_TX_TYPE]) + eth_rlp.encode(list(fields.values()))


def invalid_tx(
    pre: Alloc,
    rlp: bytes,
    error: TransactionException | List[TransactionException],
) -> Transaction:
    """
    Return a transaction whose serialization is the given raw bytes.

    Only the raw bytes are used; the other fields just need to form a
    valid blob transaction model.
    """
    tx = Transaction(
        ty=Spec.BLOB_TX_TYPE,
        sender=pre.fund_eoa(amount=0),
        to=0,
        gas_limit=21_000,
        max_fee_per_gas=10,
        max_priority_fee_per_gas=1,
        max_fee_per_blob_gas=10,
        blob_versioned_hashes=[],
        error=error,
    )
    tx.rlp_override = Bytes(rlp)
    return tx


def test_valid_reencoded_blob_transaction(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify the local encoder reproduces the framework encoding of the
    base blob transaction byte for byte, anchoring the malformation tests
    to a valid baseline.
    """
    tx = signed_blob_tx(pre)
    assert encode_blob_tx(blob_tx_fields(tx)) == bytes(tx.rlp())
    transaction_test(pre=pre, tx=tx)


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "field, value, error",
    [
        pytest.param(
            "chain_id",
            2**64,
            TransactionException.INVALID_CHAINID,
            id="chain_id_2_64",
        ),
        pytest.param(
            "chain_id",
            2**256,
            TransactionException.INVALID_CHAINID,
            id="chain_id_2_256",
        ),
        pytest.param(
            "nonce",
            2**64,
            TransactionException.NONCE_OVERFLOW,
            id="nonce_2_64",
        ),
        pytest.param(
            "nonce",
            2**256,
            TransactionException.RLP_INVALID_NONCE,
            id="nonce_2_256",
        ),
        pytest.param(
            "value",
            2**256,
            TransactionException.VALUE_OVERFLOW,
            id="value",
        ),
        pytest.param(
            "max_fee_per_blob_gas",
            2**256,
            TransactionException.GASPRICE_OVERFLOW,
            id="max_fee_per_blob_gas",
        ),
        pytest.param(
            "r",
            2**256,
            TransactionException.RLP_INVALID_SIGNATURE_R,
            id="r",
        ),
        pytest.param(
            "s",
            2**256,
            TransactionException.RLP_INVALID_SIGNATURE_S,
            id="s",
        ),
    ],
)
def test_blob_tx_field_overflow(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    field: str,
    value: int,
    error: TransactionException,
) -> None:
    """
    Encode one bounded integer field of a blob transaction with a value
    one past its width: 2**64 for the 64-bit chain id and nonce, 2**256
    (33 bytes) for the 256-bit fields.

    The gas limit, max fee per gas and max priority fee per gas are
    unbounded scalars in the spec, so oversized values there are not a
    decoding error. The signature y_parity is also a bounded field but
    has no field-specific decoding exception, so it is not covered.
    """
    fields = blob_tx_fields(signed_blob_tx(pre))
    fields[field] = Uint(value)
    rlp = encode_blob_tx(fields)
    transaction_test(pre=pre, tx=invalid_tx(pre, rlp, error))


@pytest.mark.exception_test
@pytest.mark.parametrize(
    "size, error",
    [
        pytest.param(19, TransactionException.ADDRESS_TOO_SHORT, id="19"),
        pytest.param(21, TransactionException.ADDRESS_TOO_LONG, id="21"),
    ],
)
def test_blob_tx_to_address_size(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    size: int,
    error: TransactionException,
) -> None:
    """
    Encode the `to` field of a blob transaction with a truncated 19-byte
    address or a 21-byte address made of a zero byte prefixing a valid
    address.
    """
    fields = blob_tx_fields(signed_blob_tx(pre))
    to = bytes(fields["to"])
    fields["to"] = to[:size] if size < 20 else to.rjust(size, b"\x00")
    rlp = encode_blob_tx(fields)
    transaction_test(pre=pre, tx=invalid_tx(pre, rlp, error))


@pytest.mark.exception_test
@pytest.mark.parametrize("size", [31, 33])
def test_blob_tx_versioned_hash_size(
    transaction_test: TransactionTestFiller,
    pre: Alloc,
    size: int,
) -> None:
    """
    Encode the blob versioned hash of a blob transaction with 31 or 33
    bytes instead of 32, keeping the KZG version byte first.

    The hash cannot be decoded as a 32-byte value, so clients may report
    an RLP size error or reject it as an invalid versioned hash.
    """
    fields = blob_tx_fields(signed_blob_tx(pre))
    versioned_hash = bytes(fields["blob_versioned_hashes"][0])
    if size < 32:
        versioned_hash = versioned_hash[:size]
    else:
        versioned_hash = versioned_hash + b"\x00"
    fields["blob_versioned_hashes"] = [versioned_hash]
    rlp = encode_blob_tx(fields)
    transaction_test(
        pre=pre,
        tx=invalid_tx(
            pre,
            rlp,
            [
                TransactionException.RLP_ERROR_SIZE,
                TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH,
            ],
        ),
    )
