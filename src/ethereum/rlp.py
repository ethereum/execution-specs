"""
.. _rlp:

Recursive Length Prefix (RLP) Encoding
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Defines the serialization and deserialization format used throughout Ethereum.
"""

from dataclasses import astuple, fields, is_dataclass
from typing import Any, List, Sequence, Tuple, Type, TypeVar, Union, cast

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import RLPDecodingError, RLPEncodingError

from .base_types import Bytes, Bytes0, Bytes20, FixedBytes, FixedUint, Uint

RLP = Any


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
    encoded : `ethereum.base_types.Bytes`
        The RLP encoded bytes representing `raw_data`.
    """
    if isinstance(raw_data, (bytearray, bytes)):
        return encode_bytes(raw_data)
    elif isinstance(raw_data, (Uint, FixedUint)):
        return encode(raw_data.to_be_bytes())
    elif isinstance(raw_data, str):
        return encode_bytes(raw_data.encode())
    elif isinstance(raw_data, bool):
        if raw_data:
            return encode_bytes(b"\x01")
        else:
            return encode_bytes(b"")
    elif isinstance(raw_data, Sequence):
        return encode_sequence(raw_data)
    elif is_dataclass(raw_data):
        return encode(astuple(raw_data))
    else:
        raise RLPEncodingError(
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
    encoded : `ethereum.base_types.Bytes`
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
    encoded : `ethereum.base_types.Bytes`
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
    joined_encodings : `ethereum.base_types.Bytes`
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
    if len(encoded_data) <= 0:
        raise RLPDecodingError("Cannot decode empty bytestring")

    if encoded_data[0] <= 0xBF:
        # This means that the raw data is of type bytes
        return decode_to_bytes(encoded_data)
    else:
        # This means that the raw data is of type sequence
        return decode_to_sequence(encoded_data)


T = TypeVar("T")


def decode_to(cls: Type[T], encoded_data: Bytes) -> T:
    """
    Decode the bytes in `encoded_data` to an object of type `cls`. `cls` can be
    a `Bytes` subclass, a dataclass, `Uint`, `U256` or `Tuple[cls]`.

    Parameters
    ----------
    cls: `Type[T]`
        The type to decode to.
    encoded_data :
        A sequence of bytes, in RLP form.

    Returns
    -------
    decoded_data : `T`
        Object decoded from `encoded_data`.
    """
    return _decode_to(cls, decode(encoded_data))


def _decode_to(cls: Type[T], raw_rlp: RLP) -> T:
    """
    Decode the rlp structure in `encoded_data` to an object of type `cls`.
    `cls` can be a `Bytes` subclass, a dataclass, `Uint`, `U256`,
    `Tuple[cls, ...]`, `Tuple[cls1, cls2]` or `Union[Bytes, cls]`.

    Parameters
    ----------
    cls: `Type[T]`
        The type to decode to.
    raw_rlp :
        A decoded rlp structure.

    Returns
    -------
    decoded_data : `T`
        Object decoded from `encoded_data`.
    """
    if isinstance(cls, type(Tuple[Uint, ...])) and cls._name == "Tuple":  # type: ignore # noqa: E501
        if not isinstance(raw_rlp, list):
            raise RLPDecodingError
        if cls.__args__[1] == ...:  # type: ignore
            args = []
            for raw_item in raw_rlp:
                args.append(_decode_to(cls.__args__[0], raw_item))  # type: ignore # noqa: E501
            return tuple(args)  # type: ignore
        else:
            args = []
            if len(raw_rlp) != len(cls.__args__):  # type: ignore
                raise RLPDecodingError
            for t, raw_item in zip(cls.__args__, raw_rlp):  # type: ignore
                args.append(_decode_to(t, raw_item))
            return tuple(args)  # type: ignore
    elif cls == Union[Bytes0, Bytes20]:
        if not isinstance(raw_rlp, Bytes):
            raise RLPDecodingError
        if len(raw_rlp) == 0:
            return Bytes0()  # type: ignore
        elif len(raw_rlp) == 20:
            return Bytes20(raw_rlp)  # type: ignore
        else:
            raise RLPDecodingError(
                "Bytes has length {}, expected 0 or 20".format(len(raw_rlp))
            )
    elif isinstance(cls, type(List[Bytes])) and cls._name == "List":  # type: ignore # noqa: E501
        if not isinstance(raw_rlp, list):
            raise RLPDecodingError
        items = []
        for raw_item in raw_rlp:
            items.append(_decode_to(cls.__args__[0], raw_item))  # type: ignore
        return items  # type: ignore
    elif isinstance(cls, type(Union[Bytes, List[Bytes]])) and cls.__origin__ == Union:  # type: ignore # noqa: E501
        if len(cls.__args__) != 2 or Bytes not in cls.__args__:  # type: ignore
            raise RLPDecodingError(
                "RLP Decoding to type {} is not supported".format(cls)
            )
        if isinstance(raw_rlp, Bytes):
            return raw_rlp  # type: ignore
        elif cls.__args__[0] == Bytes:  # type: ignore
            return _decode_to(cls.__args__[1], raw_rlp)  # type: ignore
        else:
            return _decode_to(cls.__args__[0], raw_rlp)  # type: ignore
    elif issubclass(cls, bool):
        if raw_rlp == b"\x01":
            return cls(True)  # type: ignore
        elif raw_rlp == b"":
            return cls(False)  # type: ignore
        else:
            raise TypeError("Cannot decode {} as {}".format(raw_rlp, cls))
    elif issubclass(cls, FixedBytes):
        if not isinstance(raw_rlp, Bytes):
            raise RLPDecodingError
        if len(raw_rlp) != cls.LENGTH:
            raise RLPDecodingError
        return cls(raw_rlp)  # type: ignore
    elif issubclass(cls, Bytes):
        if not isinstance(raw_rlp, Bytes):
            raise RLPDecodingError
        return raw_rlp  # type: ignore
    elif issubclass(cls, (Uint, FixedUint)):
        if not isinstance(raw_rlp, Bytes):
            raise RLPDecodingError
        try:
            return cls.from_be_bytes(raw_rlp)  # type: ignore
        except ValueError:
            raise RLPDecodingError
    elif is_dataclass(cls):
        if not isinstance(raw_rlp, list):
            raise RLPDecodingError
        assert isinstance(raw_rlp, list)
        args = []
        if len(fields(cls)) != len(raw_rlp):
            raise RLPDecodingError
        for field, rlp_item in zip(fields(cls), raw_rlp):
            args.append(_decode_to(field.type, rlp_item))
        return cast(T, cls(*args))
    else:
        raise RLPDecodingError(
            "RLP Decoding to type {} is not supported".format(cls)
        )


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
    decoded : `ethereum.base_types.Bytes`
        RLP decoded Bytes data
    """
    if len(encoded_bytes) == 1 and encoded_bytes[0] < 0x80:
        return encoded_bytes
    elif encoded_bytes[0] <= 0xB7:
        len_raw_data = encoded_bytes[0] - 0x80
        if len_raw_data >= len(encoded_bytes):
            raise RLPDecodingError
        raw_data = encoded_bytes[1 : 1 + len_raw_data]
        if len_raw_data == 1 and raw_data[0] < 0x80:
            raise RLPDecodingError
        return raw_data
    else:
        # This is the index in the encoded data at which decoded data
        # starts from.
        decoded_data_start_idx = 1 + encoded_bytes[0] - 0xB7
        if decoded_data_start_idx - 1 >= len(encoded_bytes):
            raise RLPDecodingError
        if encoded_bytes[1] == 0:
            raise RLPDecodingError
        len_decoded_data = Uint.from_be_bytes(
            encoded_bytes[1:decoded_data_start_idx]
        )
        if len_decoded_data < 0x38:
            raise RLPDecodingError
        decoded_data_end_idx = decoded_data_start_idx + len_decoded_data
        if decoded_data_end_idx - 1 >= len(encoded_bytes):
            raise RLPDecodingError
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
        if len_joined_encodings >= len(encoded_sequence):
            raise RLPDecodingError
        joined_encodings = encoded_sequence[1 : 1 + len_joined_encodings]
    else:
        joined_encodings_start_idx = 1 + encoded_sequence[0] - 0xF7
        if joined_encodings_start_idx - 1 >= len(encoded_sequence):
            raise RLPDecodingError
        if encoded_sequence[1] == 0:
            raise RLPDecodingError
        len_joined_encodings = Uint.from_be_bytes(
            encoded_sequence[1:joined_encodings_start_idx]
        )
        if len_joined_encodings < 0x38:
            raise RLPDecodingError
        joined_encodings_end_idx = (
            joined_encodings_start_idx + len_joined_encodings
        )
        if joined_encodings_end_idx - 1 >= len(encoded_sequence):
            raise RLPDecodingError
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
        if item_start_idx + encoded_item_length - 1 >= len(joined_encodings):
            raise RLPDecodingError
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
    if len(encoded_data) <= 0:
        raise RLPDecodingError

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
        if length_length >= len(encoded_data):
            raise RLPDecodingError
        if encoded_data[1] == 0:
            raise RLPDecodingError
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
        if length_length >= len(encoded_data):
            raise RLPDecodingError
        if encoded_data[1] == 0:
            raise RLPDecodingError
        decoded_data_length = Uint.from_be_bytes(
            encoded_data[1 : 1 + length_length]
        )

    return 1 + length_length + decoded_data_length


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
    return keccak256(encode(data))
