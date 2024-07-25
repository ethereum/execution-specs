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
from typing import (
    Any,
    ClassVar,
    Dict,
    Protocol,
    Sequence,
    Tuple,
    Type,
    TypeAlias,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import RLPDecodingError, RLPEncodingError

from .base_types import Bytes, FixedBytes, FixedUint, Uint


class RLP(Protocol):
    """
    [`Protocol`] that describes the requirements to be RLP-encodable.

    [`Protocol`]: https://docs.python.org/3/library/typing.html#typing.Protocol
    """

    __dataclass_fields__: ClassVar[Dict]


Simple: TypeAlias = Union[Sequence["Simple"], bytes]

Extended: TypeAlias = Union[
    Sequence["Extended"], bytearray, bytes, Uint, FixedUint, str, bool, RLP
]


#
# RLP Encode
#


def encode(raw_data: Extended) -> Bytes:
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
    if isinstance(raw_data, Sequence):
        if isinstance(raw_data, (bytearray, bytes)):
            return encode_bytes(raw_data)
        elif isinstance(raw_data, str):
            return encode_bytes(raw_data.encode())
        else:
            return encode_sequence(raw_data)
    elif isinstance(raw_data, (Uint, FixedUint)):
        return encode(raw_data.to_be_bytes())
    elif isinstance(raw_data, bool):
        if raw_data:
            return encode_bytes(b"\x01")
        else:
            return encode_bytes(b"")
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
    len_raw_data = len(raw_bytes)

    if len_raw_data == 1 and raw_bytes[0] < 0x80:
        return raw_bytes
    elif len_raw_data < 0x38:
        return bytes([0x80 + len_raw_data]) + raw_bytes
    else:
        # length of raw data represented as big endian bytes
        len_raw_data_as_be = Uint(len_raw_data).to_be_bytes()
        return (
            bytes([0xB7 + len(len_raw_data_as_be)])
            + len_raw_data_as_be
            + raw_bytes
        )


def encode_sequence(raw_sequence: Sequence[Extended]) -> Bytes:
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
    len_joined_encodings = len(joined_encodings)

    if len_joined_encodings < 0x38:
        return Bytes([0xC0 + len_joined_encodings]) + joined_encodings
    else:
        len_joined_encodings_as_be = Uint(len_joined_encodings).to_be_bytes()
        return (
            Bytes([0xF7 + len(len_joined_encodings_as_be)])
            + len_joined_encodings_as_be
            + joined_encodings
        )


def get_joined_encodings(raw_sequence: Sequence[Extended]) -> Bytes:
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


def decode(encoded_data: Bytes) -> Simple:
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


U = TypeVar("U", bound=Extended)


def decode_to(cls: Type[U], encoded_data: Bytes) -> U:
    """
    Decode the bytes in `encoded_data` to an object of type `cls`. `cls` can be
    a `Bytes` subclass, a dataclass, `Uint`, `U256` or `Tuple[cls]`.

    Parameters
    ----------
    cls: `Type[U]`
        The type to decode to.
    encoded_data :
        A sequence of bytes, in RLP form.

    Returns
    -------
    decoded_data : `U`
        Object decoded from `encoded_data`.
    """
    decoded = decode(encoded_data)
    return _deserialize_to(cls, decoded)


@overload
def _deserialize_to(class_: Type[U], value: Simple) -> U:
    pass


@overload
def _deserialize_to(class_: object, value: Simple) -> Extended:
    pass


def _deserialize_to(class_: object, value: Simple) -> Extended:
    if not isinstance(class_, type):
        return _deserialize_to_annotation(class_, value)
    elif is_dataclass(class_):
        return _deserialize_to_dataclass(class_, value)
    elif issubclass(class_, (Uint, FixedUint)):
        return _deserialize_to_uint(class_, value)
    elif issubclass(class_, (Bytes, FixedBytes)):
        return _deserialize_to_bytes(class_, value)
    elif class_ is bool:
        return _deserialize_to_bool(value)
    else:
        raise NotImplementedError(class_)


def _deserialize_to_dataclass(cls: Type[U], decoded: Simple) -> U:
    assert is_dataclass(cls)
    hints = get_type_hints(cls)
    target_fields = fields(cls)

    if isinstance(decoded, bytes):
        raise RLPDecodingError(f"got `bytes` while decoding `{cls.__name__}`")

    if len(target_fields) != len(decoded):
        name = cls.__name__
        actual = len(decoded)
        expected = len(target_fields)
        raise RLPDecodingError(
            f"`{name}` needs {expected} field(s), but got {actual} instead"
        )

    values: Dict[str, Any] = {}

    for value, target_field in zip(decoded, target_fields):
        resolved_type = hints[target_field.name]
        values[target_field.name] = _deserialize_to(resolved_type, value)

    result = cls(**values)
    assert isinstance(result, cls)
    return cast(U, result)


def _deserialize_to_bool(value: Simple) -> bool:
    if value == b"":
        return False
    elif value == b"\x01":
        return True
    else:
        raise RLPDecodingError


def _deserialize_to_bytes(
    class_: Union[Type[Bytes], Type[FixedBytes]], value: Simple
) -> Union[Bytes, FixedBytes]:
    if not isinstance(value, bytes):
        raise RLPDecodingError
    try:
        return class_(value)
    except ValueError as e:
        raise RLPDecodingError from e


def _deserialize_to_uint(
    class_: Union[Type[Uint], Type[FixedUint]], decoded: Simple
) -> Union[Uint, FixedUint]:
    if not isinstance(decoded, bytes):
        raise RLPDecodingError
    try:
        return class_.from_be_bytes(decoded)
    except ValueError as e:
        raise RLPDecodingError from e


def _deserialize_to_annotation(annotation: object, value: Simple) -> Extended:
    origin = get_origin(annotation)
    if origin is Union:
        return _deserialize_to_union(annotation, value)
    elif origin in (Tuple, tuple):
        return _deserialize_to_tuple(annotation, value)
    elif origin is None:
        raise Exception(annotation)
    else:
        raise NotImplementedError(f"RLP non-type {origin!r}")


def _deserialize_to_union(annotation: object, value: Simple) -> Extended:
    arguments = get_args(annotation)
    successes = []
    failures = []
    for argument in arguments:
        try:
            success = _deserialize_to(argument, value)
        except Exception as e:
            failures.append(e)
            continue

        successes.append(success)

    if len(successes) == 1:
        return successes[0]
    elif not successes:
        raise RLPDecodingError(f"no matching union variant\n{failures!r}")
    else:
        raise RLPDecodingError("multiple matching union variants")


def _deserialize_to_tuple(
    annotation: object, values: Simple
) -> Sequence[Extended]:
    if isinstance(values, bytes):
        raise RLPDecodingError
    arguments = list(get_args(annotation))

    if arguments[-1] is Ellipsis:
        arguments.pop()
        fill_count = len(values) - len(arguments)
        arguments = list(arguments) + [arguments[-1]] * fill_count

    decoded = []
    for argument, value in zip(arguments, values):
        decoded.append(_deserialize_to(argument, value))

    return tuple(decoded)


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
        len_decoded_data = int(
            Uint.from_be_bytes(encoded_bytes[1:decoded_data_start_idx])
        )
        if len_decoded_data < 0x38:
            raise RLPDecodingError
        decoded_data_end_idx = decoded_data_start_idx + int(len_decoded_data)
        if decoded_data_end_idx - 1 >= len(encoded_bytes):
            raise RLPDecodingError
        return encoded_bytes[decoded_data_start_idx:decoded_data_end_idx]


def decode_to_sequence(encoded_sequence: Bytes) -> Sequence[Simple]:
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
        len_joined_encodings = int(
            Uint.from_be_bytes(encoded_sequence[1:joined_encodings_start_idx])
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


def decode_joined_encodings(joined_encodings: Bytes) -> Sequence[Simple]:
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

    first_rlp_byte = encoded_data[0]

    # This is the length of the big endian representation of the length of
    # rlp encoded object byte stream.
    length_length = 0
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
        decoded_data_length = int(
            Uint.from_be_bytes(encoded_data[1 : 1 + length_length])
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
        decoded_data_length = int(
            Uint.from_be_bytes(encoded_data[1 : 1 + length_length])
        )

    return 1 + length_length + decoded_data_length


def rlp_hash(data: Extended) -> Hash32:
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
