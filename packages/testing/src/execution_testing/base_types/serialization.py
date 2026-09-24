"""Ethereum test types for serialization and encoding."""

from dataclasses import astuple, is_dataclass
from typing import Any, ClassVar, List, Self, Sequence

import ethereum_rlp as eth_rlp
from ethereum_rlp.exceptions import EncodingError
from ethereum_types.numeric import FixedUnsigned, Uint
from trie import HexaryTrie

from execution_testing.base_types import Bytes


def to_serializable_element(v: Any) -> Any:
    """Return a serializable element that can be passed to `eth_rlp.encode`."""
    if isinstance(v, int):
        return Uint(v)
    elif isinstance(v, bytes):
        return v
    elif isinstance(v, list):
        return [to_serializable_element(v) for v in v]
    elif isinstance(v, RLPSerializable):
        if v.signable:
            v.sign()
        return v.to_list(signing=False)
    elif v is None:
        return b""
    raise Exception(f"Unable to serialize element {v} of type {type(v)}.")


def encoded_prefixed_size(payload_size: int) -> int:
    """
    Return the encoded size of an item with a payload of `payload_size`
    bytes, its length prefix included.
    """
    if payload_size < 0x38:
        return 1 + payload_size
    return 1 + len(Uint(payload_size).to_be_bytes()) + payload_size


def _encoded_bytes_size(raw_bytes: bytes | bytearray) -> int:
    """Return the length of `eth_rlp.encode_bytes(raw_bytes)`."""
    if len(raw_bytes) == 1 and raw_bytes[0] < 0x80:
        return 1
    return encoded_prefixed_size(len(raw_bytes))


def _encoded_sequence_size(raw_sequence: Sequence[Any]) -> int:
    """Return the length of `eth_rlp.encode_sequence(raw_sequence)`."""
    return encoded_prefixed_size(
        sum(encoded_size(item) for item in raw_sequence)
    )


def _encoded_unsigned_size(value: int) -> int:
    """Return the length of `eth_rlp.encode(Uint(value))`."""
    if value < 0x80:
        return 1
    return encoded_prefixed_size((value.bit_length() + 7) // 8)


def encoded_size(raw_data: Any) -> int:
    """
    Return `len(eth_rlp.encode(raw_data))` without building the encoding.

    This covers the same cases as `ethereum_rlp.encode`, so measuring the
    size of a large structure costs a walk over it instead of megabytes of
    intermediate byte strings. The concrete types come first: the abstract
    `Sequence` check is slow enough to dominate the walk.
    """
    if isinstance(raw_data, (bytearray, bytes)):
        return _encoded_bytes_size(raw_data)
    elif isinstance(raw_data, (list, tuple)):
        return _encoded_sequence_size(raw_data)
    elif isinstance(raw_data, (Uint, FixedUnsigned)):
        return _encoded_unsigned_size(int(raw_data))
    elif isinstance(raw_data, bool):
        return 1
    elif isinstance(raw_data, str):
        return _encoded_bytes_size(raw_data.encode())
    elif isinstance(raw_data, Sequence):
        return _encoded_sequence_size(raw_data)
    elif is_dataclass(raw_data) and not isinstance(raw_data, type):
        return _encoded_sequence_size(astuple(raw_data))
    else:
        raise EncodingError(
            "RLP encoded size of type {} is not supported".format(
                type(raw_data)
            )
        )


class RLPSerializable:
    """Class that adds RLP serialization to another class."""

    rlp_override: Bytes | None = None

    signable: ClassVar[bool] = False
    rlp_fields: ClassVar[List[str]]
    rlp_signing_fields: ClassVar[List[str]]
    rlp_exclude_none: ClassVar[bool] = False

    def get_rlp_fields(self) -> List[str]:
        """
        Return an ordered list of field names to be included in RLP
        serialization.

        Function can be overridden to customize the logic to return the fields.

        By default, rlp_fields class variable is used.

        The list can be nested list up to one extra level to represent nested
        fields.
        """
        return self.rlp_fields

    def get_rlp_signing_fields(self) -> List[str]:
        """
        Return an ordered list of field names to be included in the RLP
        serialization of the object signature.

        Function can be overridden to customize the logic to return the fields.

        By default, rlp_signing_fields class variable is used.

        The list can be nested list up to one extra level to represent nested
        fields.
        """
        return self.rlp_signing_fields

    def get_rlp_prefix(self) -> bytes:
        """
        Return a prefix that has to be appended to the serialized object.

        By default, an empty string is returned.
        """
        return b""

    def get_rlp_signing_prefix(self) -> bytes:
        """
        Return a prefix that has to be appended to the serialized signing
        object.

        By default, an empty string is returned.
        """
        return b""

    def sign(self) -> None:
        """Sign the current object for further serialization."""
        raise NotImplementedError(
            f'Object "{self.__class__.__name__}" cannot be signed.'
        )

    def to_list_from_fields(self, fields: List[str]) -> List[Any]:
        """
        Return an RLP serializable list that can be passed to `eth_rlp.encode`.

        Can be for signing purposes or the entire object.
        """
        values_list: List[Any] = []
        for field in fields:
            assert isinstance(field, str), (
                f'Unable to rlp serialize field "{field}" '
                f'in object type "{self.__class__.__name__}"'
            )
            assert hasattr(self, field), (
                f'Unable to rlp serialize field "{field}" '
                f'in object type "{self.__class__.__name__}"'
            )
            try:
                value = getattr(self, field)
                if self.rlp_exclude_none and value is None:
                    continue
                values_list.append(to_serializable_element(value))
            except Exception as e:
                raise Exception(
                    f'Unable to rlp serialize field "{field}" '
                    f'in object type "{self.__class__.__name__}"'
                ) from e
        return values_list

    def to_list(self, signing: bool = False) -> List[Any]:
        """
        Return an RLP serializable list that can be passed to `eth_rlp.encode`.

        Can be for signing purposes or the entire object.
        """
        field_list: List[str]
        if signing:
            if not self.signable:
                raise Exception(
                    f'Object "{self.__class__.__name__}" '
                    "does not support signing"
                )
            field_list = self.get_rlp_signing_fields()
        else:
            if self.signable:
                # Automatically sign signable objects during full
                # serialization: Ensures nested objects have valid signatures
                # in the final RLP.
                self.sign()
            field_list = self.get_rlp_fields()

        return self.to_list_from_fields(field_list)

    def rlp_signing_bytes(self) -> Bytes:
        """Return the signing serialized envelope used for signing."""
        return Bytes(
            self.get_rlp_signing_prefix()
            + eth_rlp.encode(self.to_list(signing=True))
        )

    def rlp(self) -> Bytes:
        """Return the serialized object."""
        if self.rlp_override is not None:
            return self.rlp_override
        return Bytes(
            self.get_rlp_prefix() + eth_rlp.encode(self.to_list(signing=False))
        )

    def rlp_size(self) -> int:
        """Return `len(self.rlp())` without building the encoding."""
        if self.rlp_override is not None:
            return len(self.rlp_override)
        return len(self.get_rlp_prefix()) + encoded_size(
            self.to_list(signing=False)
        )

    @classmethod
    def list_root(cls, element_list: Sequence[Self]) -> bytes:
        """Return the root of a list of the given type."""
        t = HexaryTrie(db={})
        for i, e in enumerate(element_list):
            t.set(
                eth_rlp.encode(Uint(i)),
                e.rlp(),
            )
        return t.root_hash


class SignableRLPSerializable(RLPSerializable):
    """
    Class that adds RLP serialization to another class with signing support.
    """

    signable: ClassVar[bool] = True

    def sign(self) -> None:
        """Sign the current object for further serialization."""
        raise NotImplementedError(
            f'Object "{self.__class__.__name__}" needs to implement `sign`.'
        )
