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
