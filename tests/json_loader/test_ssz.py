"""Tests for dataclass-native SSZ serialization."""

from dataclasses import dataclass
from typing import Annotated, Tuple

import pytest
from ethereum_types.bytes import Bytes32
from ethereum_types.numeric import U16, U64, Uint

from ethereum.utils.ssz import (
    ProgressiveSszContainer,
    SszContainer,
    byte_list,
    progressive_list,
    ssz_list,
    uint,
)


@dataclass(frozen=True)
class _Item(SszContainer):
    key: Bytes32
    value: U16


@dataclass(frozen=True)
class _ProgressiveItems(ProgressiveSszContainer):
    items: Annotated[Tuple[_Item, ...], progressive_list()]


@dataclass(frozen=True)
class _Envelope(SszContainer):
    count: Annotated[Uint, uint(64)]
    payload: Annotated[bytes, byte_list(16)]
    fixed_items: Annotated[Tuple[_Item, ...], ssz_list(2)]
    progressive_items: _ProgressiveItems


@dataclass(frozen=True)
class _ByteLists(SszContainer):
    bounded: Annotated[
        Tuple[Annotated[bytes, byte_list(16)], ...], ssz_list(2)
    ]
    progressive: Annotated[
        Tuple[Annotated[bytes, byte_list(16)], ...], progressive_list()
    ]


def test_nested_containers_roundtrip() -> None:
    """Restore Python types after standard and progressive SSZ decoding."""
    item = _Item(key=Bytes32(b"\x11" * 32), value=U16(3))
    original = _Envelope(
        count=Uint(1),
        payload=b"payload",
        fixed_items=(item,),
        progressive_items=_ProgressiveItems(items=(item, item)),
    )

    encoded = original.encode_bytes()
    recovered = _Envelope.decode_bytes(encoded)

    assert recovered == original
    assert type(recovered.count) is Uint
    assert type(recovered.fixed_items) is tuple
    assert type(recovered.progressive_items.items) is tuple
    assert len(original.hash_tree_root()) == 32


def test_collection_limits_are_enforced() -> None:
    """Reject dataclass values that exceed their declared SSZ limits."""
    item = _Item(key=Bytes32(b"\x22" * 32), value=U16(4))
    too_many_items = _Envelope(
        count=Uint(3),
        payload=b"payload",
        fixed_items=(item, item, item),
        progressive_items=_ProgressiveItems(items=()),
    )

    with pytest.raises(Exception, match="too many list inputs"):
        too_many_items.encode_bytes()


def test_fixed_width_integer_roundtrip() -> None:
    """Decode an explicitly sized integer to its specification type."""
    original = _Envelope(
        count=Uint(2**63),
        payload=b"",
        fixed_items=(),
        progressive_items=_ProgressiveItems(items=()),
    )

    recovered = _Envelope.decode_bytes(original.encode_bytes())

    assert recovered.count == Uint(2**63)
    assert type(recovered.count) is Uint
    assert U64(recovered.count) == U64(2**63)


@pytest.mark.parametrize("nested", [False, True])
def test_container_offset_gap_rejected(nested: bool) -> None:
    """Reject offset gaps in both standard and progressive containers."""
    original = _Envelope(
        count=Uint(0),
        payload=b"",
        fixed_items=(),
        progressive_items=_ProgressiveItems(items=()),
    )
    encoded = bytearray(original.encode_bytes())
    offsets: tuple[int, ...]
    if nested:
        # The final field is a progressive container with one offset.
        offsets = (int.from_bytes(encoded[16:20], "little"),)
    else:
        offsets = (8, 12, 16)
    for offset in offsets:
        value = int.from_bytes(encoded[offset : offset + 4], "little")
        encoded[offset : offset + 4] = (value + 1).to_bytes(4, "little")
    encoded.append(0xFF)

    with pytest.raises(ValueError, match="Non-canonical SSZ encoding"):
        _Envelope.decode_bytes(bytes(encoded))


@pytest.mark.parametrize("progressive", [False, True])
@pytest.mark.parametrize("trailing", [b"", b"ignored"])
def test_nonempty_list_with_zero_first_offset_rejected(
    progressive: bool, trailing: bytes
) -> None:
    """An empty variable-element list must have a zero-byte encoding."""
    invalid_list = b"\x00" * 4 + trailing
    second_offset = 8 if progressive else 8 + len(invalid_list)
    encoded = (
        (8).to_bytes(4, "little")
        + second_offset.to_bytes(4, "little")
        + invalid_list
    )

    with pytest.raises(ValueError):
        _ByteLists.decode_bytes(encoded)
