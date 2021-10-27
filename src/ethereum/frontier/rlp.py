"""
Recursive Length Prefix (RLP) Encoding
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Defines the serialization and deserialization format used throughout Ethereum.
"""

from __future__ import annotations

from typing import Any, List, Sequence, Union, cast

from ethereum import crypto
from ethereum.crypto import Hash32
from ethereum.utils.ensure import ensure

from ..base_types import U256, Bytes, Bytes0, Bytes8, Uint
from ..crypto import keccak256
from .eth_types import (
    Account,
    Address,
    Block,
    Bloom,
    Header,
    Log,
    Receipt,
    Root,
    Transaction,
)

RLP = Union[  # type: ignore
    Bytes,
    Uint,
    U256,
    Block,
    Header,
    Account,
    Transaction,
    Receipt,
    Log,
    Sequence["RLP"],  # type: ignore
]


#
# RLP Encode
#


def encode(raw_data: RLP) -> Bytes:
    """
    Encodes `raw_data` into a sequence of bytes using RLP.

    Parameters
    ----------
    raw_data :
        A `Bytes`, `Uint`, `Uint256` or sequence of `RLP` encodable
        objects.

    Returns
    -------
    encoded : `eth1spec.base_types.Bytes`
        The RLP encoded bytes representing `raw_data`.
    """
    if isinstance(raw_data, (bytearray, bytes)):
        return encode_bytes(raw_data)
    elif isinstance(raw_data, (Uint, U256)):
        return encode_bytes(raw_data.to_be_bytes())
    elif isinstance(raw_data, str):
        return encode_bytes(raw_data.encode())
    elif isinstance(raw_data, Sequence):
        return encode_sequence(cast(Sequence[RLP], raw_data))
    elif isinstance(raw_data, Block):
        return encode(transcode_block(raw_data))
    elif isinstance(raw_data, Header):
        return encode(transcode_header(raw_data))
    elif isinstance(raw_data, Transaction):
        return encode(transcode_transaction(raw_data))
    elif isinstance(raw_data, Receipt):
        return encode(transcode_receipt(raw_data))
    elif isinstance(raw_data, Log):
        return encode(transcode_log(raw_data))
    else:
        raise TypeError(
            "RLP Encoding of type {} is not supported".format(type(raw_data))
        )


def encode_bytes(raw_bytes: Bytes) -> Bytes:
    """
    Encodes `raw_bytes`, a sequence of bytes, using RLP.

    Parameters
    ----------
    raw_bytes :
        Bytes to encode with RLP.

    Returns
    -------
    encoded : `eth1spec.base_types.Bytes`
        The RLP encoded bytes representing `raw_bytes`.
    """
    len_raw_data = Uint(len(raw_bytes))

    if len_raw_data == 1 and raw_bytes[0] < 0x80:
        return raw_bytes
    elif len_raw_data < 0x38:
        return bytes([0x80 + len_raw_data]) + raw_bytes
    else:
        # length of raw data represented as big endian bytes
        len_raw_data_as_be = len_raw_data.to_be_bytes()
        return (
            bytes([0xB7 + len(len_raw_data_as_be)])
            + len_raw_data_as_be
            + raw_bytes
        )


def encode_sequence(raw_sequence: Sequence[RLP]) -> Bytes:
    """
    Encodes a list of RLP encodable objects (`raw_sequence`) using RLP.

    Parameters
    ----------
    raw_sequence :
            Sequence of RLP encodable objects.

    Returns
    -------
    encoded : `eth1spec.base_types.Bytes`
        The RLP encoded bytes representing `raw_sequence`.
    """
    joined_encodings = get_joined_encodings(raw_sequence)
    len_joined_encodings = Uint(len(joined_encodings))

    if len_joined_encodings < 0x38:
        return Bytes([0xC0 + len_joined_encodings]) + joined_encodings
    else:
        len_joined_encodings_as_be = len_joined_encodings.to_be_bytes()
        return (
            Bytes([0xF7 + len(len_joined_encodings_as_be)])
            + len_joined_encodings_as_be
            + joined_encodings
        )


def get_joined_encodings(raw_sequence: Sequence[RLP]) -> Bytes:
    """
    Obtain concatenation of rlp encoding for each item in the sequence
    raw_sequence.

    Parameters
    ----------
    raw_sequence :
        Sequence to encode with RLP.

    Returns
    -------
    joined_encodings : `eth1spec.base_types.Bytes`
        The concatenated RLP encoded bytes for each item in sequence
        raw_sequence.
    """
    return b"".join(encode(item) for item in raw_sequence)


#
# RLP Decode
#


def decode(encoded_data: Bytes) -> RLP:
    """
    Decodes an integer, byte sequence, or list of RLP encodable objects
    from the byte sequence `encoded_data`, using RLP.

    Parameters
    ----------
    encoded_data :
        A sequence of bytes, in RLP form.

    Returns
    -------
    decoded_data : `RLP`
        Object decoded from `encoded_data`.
    """
    # Raising error as there can never be empty encoded data for any
    # given raw data (including empty raw data)
    # RLP Encoding(b'') -> [0x80]  # noqa: SC100
    # RLP Encoding([])  -> [0xc0]  # noqa: SC100
    ensure(len(encoded_data) > 0)

    if encoded_data[0] <= 0xBF:
        # This means that the raw data is of type bytes
        return decode_to_bytes(encoded_data)
    else:
        # This means that the raw data is of type sequence
        return decode_to_sequence(encoded_data)


def decode_to_bytes(encoded_bytes: Bytes) -> Bytes:
    """
    Decodes a rlp encoded byte stream assuming that the decoded data
    should be of type `bytes`.

    Parameters
    ----------
    encoded_bytes :
        RLP encoded byte stream.

    Returns
    -------
    decoded : `eth1spec.base_types.Bytes`
        RLP decoded Bytes data
    """
    if len(encoded_bytes) == 1 and encoded_bytes[0] < 0x80:
        return encoded_bytes
    elif encoded_bytes[0] <= 0xB7:
        len_raw_data = encoded_bytes[0] - 0x80
        ensure(len_raw_data < len(encoded_bytes))
        raw_data = encoded_bytes[1 : 1 + len_raw_data]
        ensure(not (len_raw_data == 1 and raw_data[0] < 0x80))
        return raw_data
    else:
        # This is the index in the encoded data at which decoded data
        # starts from.
        decoded_data_start_idx = 1 + encoded_bytes[0] - 0xB7
        ensure(decoded_data_start_idx - 1 < len(encoded_bytes))
        # Expectation is that the big endian bytes shouldn't start with 0
        # while trying to decode using RLP, in which case is an error.
        ensure(encoded_bytes[1] != 0)
        len_decoded_data = Uint.from_be_bytes(
            encoded_bytes[1:decoded_data_start_idx]
        )
        ensure(len_decoded_data >= 0x38)
        decoded_data_end_idx = decoded_data_start_idx + len_decoded_data
        ensure(decoded_data_end_idx - 1 < len(encoded_bytes))
        return encoded_bytes[decoded_data_start_idx:decoded_data_end_idx]


def decode_to_sequence(encoded_sequence: Bytes) -> List[RLP]:
    """
    Decodes a rlp encoded byte stream assuming that the decoded data
    should be of type `Sequence` of objects.

    Parameters
    ----------
    encoded_sequence :
        An RLP encoded Sequence.

    Returns
    -------
    decoded : `Sequence[RLP]`
        Sequence of objects decoded from `encoded_sequence`.
    """
    if encoded_sequence[0] <= 0xF7:
        len_joined_encodings = encoded_sequence[0] - 0xC0
        ensure(len_joined_encodings < len(encoded_sequence))
        joined_encodings = encoded_sequence[1 : 1 + len_joined_encodings]
    else:
        joined_encodings_start_idx = 1 + encoded_sequence[0] - 0xF7
        ensure(joined_encodings_start_idx - 1 < len(encoded_sequence))
        # Expectation is that the big endian bytes shouldn't start with 0
        # while trying to decode using RLP, in which case is an error.
        ensure(encoded_sequence[1] != 0)
        len_joined_encodings = Uint.from_be_bytes(
            encoded_sequence[1:joined_encodings_start_idx]
        )
        ensure(len_joined_encodings >= 0x38)
        joined_encodings_end_idx = (
            joined_encodings_start_idx + len_joined_encodings
        )
        ensure(joined_encodings_end_idx - 1 < len(encoded_sequence))
        joined_encodings = encoded_sequence[
            joined_encodings_start_idx:joined_encodings_end_idx
        ]

    return decode_joined_encodings(joined_encodings)


def decode_joined_encodings(joined_encodings: Bytes) -> List[RLP]:
    """
    Decodes `joined_encodings`, which is a concatenation of RLP encoded
    objects.

    Parameters
    ----------
    joined_encodings :
        concatenation of RLP encoded objects

    Returns
    -------
    decoded : `List[RLP]`
        A list of objects decoded from `joined_encodings`.
    """
    decoded_sequence = []

    item_start_idx = 0
    while item_start_idx < len(joined_encodings):
        encoded_item_length = decode_item_length(
            joined_encodings[item_start_idx:]
        )
        ensure(
            item_start_idx + encoded_item_length - 1 < len(joined_encodings)
        )
        encoded_item = joined_encodings[
            item_start_idx : item_start_idx + encoded_item_length
        ]
        decoded_sequence.append(decode(encoded_item))
        item_start_idx += encoded_item_length

    return decoded_sequence


def decode_item_length(encoded_data: Bytes) -> int:
    """
    Find the length of the rlp encoding for the first object in the
    encoded sequence.
    Here `encoded_data` refers to concatenation of rlp encoding for each
    item in a sequence.

    NOTE - This is a helper function not described in the spec. It was
    introduced as the spec doesn't discuss about decoding the RLP encoded
    data.

    Parameters
    ----------
    encoded_data :
        RLP encoded data for a sequence of objects.

    Returns
    -------
    rlp_length : `int`
    """
    # Can't decode item length for empty encoding
    ensure(len(encoded_data) > 0)

    first_rlp_byte = Uint(encoded_data[0])

    # This is the length of the big endian representation of the length of
    # rlp encoded object byte stream.
    length_length = Uint(0)
    decoded_data_length = 0

    # This occurs only when the raw_data is a single byte whose value < 128
    if first_rlp_byte < 0x80:
        # We return 1 here, as the end formula
        # 1 + length_length + decoded_data_length would be invalid for
        # this case.
        return 1
    # This occurs only when the raw_data is a byte stream with length < 56
    # and doesn't fall into the above cases
    elif first_rlp_byte <= 0xB7:
        decoded_data_length = first_rlp_byte - 0x80
    # This occurs only when the raw_data is a byte stream and doesn't fall
    # into the above cases
    elif first_rlp_byte <= 0xBF:
        length_length = first_rlp_byte - 0xB7
        ensure(length_length < len(encoded_data))
        # Expectation is that the big endian bytes shouldn't start with 0
        # while trying to decode using RLP, in which case is an error.
        ensure(encoded_data[1] != 0)
        decoded_data_length = Uint.from_be_bytes(
            encoded_data[1 : 1 + length_length]
        )
    # This occurs only when the raw_data is a sequence of objects with
    # length(concatenation of encoding of each object) < 56
    elif first_rlp_byte <= 0xF7:
        decoded_data_length = first_rlp_byte - 0xC0
    # This occurs only when the raw_data is a sequence of objects and
    # doesn't fall into the above cases.
    elif first_rlp_byte <= 0xFF:
        length_length = first_rlp_byte - 0xF7
        ensure(length_length < len(encoded_data))
        # Expectation is that the big endian bytes shouldn't start with 0
        # while trying to decode using RLP, in which case is an error.
        ensure(encoded_data[1] != 0)
        decoded_data_length = Uint.from_be_bytes(
            encoded_data[1 : 1 + length_length]
        )

    return 1 + length_length + decoded_data_length


#
# Encoding and decoding custom dataclasses like Account, Transaction,
# Receipt etc.
#


def transcode_block(raw_block_data: Block) -> RLP:
    """
    Encode `Block` dataclass
    """
    return (
        raw_block_data.header,
        raw_block_data.transactions,
        raw_block_data.ommers,
    )


def transcode_header(raw_header_data: Header) -> RLP:
    """
    Encode `Header` dataclass
    """
    return (
        raw_header_data.parent_hash,
        raw_header_data.ommers_hash,
        raw_header_data.coinbase,
        raw_header_data.state_root,
        raw_header_data.transactions_root,
        raw_header_data.receipt_root,
        raw_header_data.bloom,
        raw_header_data.difficulty,
        raw_header_data.number,
        raw_header_data.gas_limit,
        raw_header_data.gas_used,
        raw_header_data.timestamp,
        raw_header_data.extra_data,
        raw_header_data.mix_digest,
        raw_header_data.nonce,
    )


def encode_account(raw_account_data: Account, storage_root: Bytes) -> Bytes:
    """
    Encode `Account` dataclass.

    Storage is not stored in the `Account` dataclass, so `Accounts` cannot be
    enocoded with providing a storage root.
    """
    return encode(
        (
            raw_account_data.nonce,
            raw_account_data.balance,
            storage_root,
            keccak256(raw_account_data.code),
        )
    )


def transcode_transaction(raw_tx_data: Transaction) -> RLP:
    """
    Encode `Transaction` dataclass
    """
    return (
        raw_tx_data.nonce,
        raw_tx_data.gas_price,
        raw_tx_data.gas,
        raw_tx_data.to,
        raw_tx_data.value,
        raw_tx_data.data,
        raw_tx_data.v,
        raw_tx_data.r,
        raw_tx_data.s,
    )


def transcode_receipt(raw_receipt_data: Receipt) -> RLP:
    """
    Encode `Receipt` dataclass
    """
    return (
        raw_receipt_data.post_state,
        raw_receipt_data.cumulative_gas_used,
        raw_receipt_data.bloom,
        raw_receipt_data.logs,
    )


def transcode_log(raw_log_data: Log) -> RLP:
    """
    Encode `Log` dataclass
    """
    return (
        raw_log_data.address,
        raw_log_data.topics,
        raw_log_data.data,
    )


def sequence_to_header(sequence: Sequence[Bytes]) -> Header:
    """
    Build a Header object from a sequence of bytes. The sequence should be
    containing exactly 15 byte sequences.

    Parameters
    ----------
    sequence :
        The sequence of bytes which is supposed to form the Header
        object.

    Returns
    -------
    header : `Header`
        The obtained `Header` object.
    """
    ensure(len(sequence) == 15)

    ensure(len(sequence[12]) <= 32)

    return Header(
        parent_hash=Hash32(sequence[0]),
        ommers_hash=Hash32(sequence[1]),
        coinbase=Address(sequence[2]),
        state_root=Root(sequence[3]),
        transactions_root=Root(sequence[4]),
        receipt_root=Root(sequence[5]),
        bloom=Bloom(sequence[6]),
        difficulty=Uint.from_be_bytes(sequence[7]),
        number=Uint.from_be_bytes(sequence[8]),
        gas_limit=Uint.from_be_bytes(sequence[9]),
        gas_used=Uint.from_be_bytes(sequence[10]),
        timestamp=U256.from_be_bytes(sequence[11]),
        extra_data=sequence[12],
        mix_digest=Hash32(sequence[13]),
        nonce=Bytes8(sequence[14]),
    )


def sequence_to_transaction(sequence: Sequence[Bytes]) -> Transaction:
    """
    Build a Transaction object from a sequence of bytes. The sequence should
    be containing exactly 9 byte sequences.

    Parameters
    ----------
    sequence :
        The sequence of bytes which is supposed to form the Transaction
        object.

    Returns
    -------
    transaction : `Transaction`
        The obtained `Transaction` object.
    """
    # TODO: Add assertions about the number of bytes in each of the below
    # variables if it's used in chain sync later on.
    ensure(len(sequence) == 9)

    to: Union[Bytes0, Address] = Bytes0()
    if sequence[3] != b"":
        to = Address(sequence[3])

    return Transaction(
        nonce=U256.from_be_bytes(sequence[0]),
        gas_price=U256.from_be_bytes(sequence[1]),
        gas=U256.from_be_bytes(sequence[2]),
        to=to,
        value=U256.from_be_bytes(sequence[4]),
        data=sequence[5],
        v=U256.from_be_bytes(sequence[6]),
        r=U256.from_be_bytes(sequence[7]),
        s=U256.from_be_bytes(sequence[8]),
    )


def decode_to_header(encoded_header: Bytes) -> Header:
    """
    Decodes a rlp encoded byte stream assuming that the decoded data
    should be of type `Header`.

    NOTE - This function is valid only till the London Hardfork. Post that
    there would be changes in the Header object as well as this function with
    the introduction of `base_fee` parameter.

    Parameters
    ----------
    encoded_header :
        An RLP encoded Header.

    Returns
    -------
    decoded_header : `Header`
        The header object decoded from `encoded_header`.
    """
    decoded_data = cast(Sequence[Bytes], decode(encoded_header))
    return sequence_to_header(decoded_data)


def decode_to_block(encoded_block: Bytes) -> Block:
    """
    Decodes a rlp encoded byte stream assuming that the decoded data
    should be of type `Block`.

    NOTE - This function is valid only till the London Hardfork. Post that
    there would be changes in the Header object as well as this function with
    the introduction of `base_fee` parameter.

    Parameters
    ----------
    encoded_block :
        An RLP encoded block.

    Returns
    -------
    decoded_block : `Block`
        The block object decoded from `encoded_block`.
    """
    sequential_header, sequential_transactions, sequential_ommers = cast(
        Sequence[Any],
        decode(encoded_block),
    )

    header = sequence_to_header(sequential_header)
    transactions = tuple(
        sequence_to_transaction(sequential_tx)
        for sequential_tx in sequential_transactions
    )
    ommers = tuple(
        sequence_to_header(sequential_ommer)
        for sequential_ommer in sequential_ommers
    )

    return Block(header, transactions, ommers)


def rlp_hash(data: RLP) -> Hash32:
    """
    Obtain the keccak-256 hash of the rlp encoding of the passed in data.

    Parameters
    ----------
    data :
        The data for which we need the rlp hash.

    Returns
    -------
    hash : `Hash32`
        The rlp hash of the passed in data.
    """
    return crypto.keccak256(encode(data))
